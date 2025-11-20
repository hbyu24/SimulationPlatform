from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import pandas as pd


@dataclass
class RubricItem:
    id: str
    label: str
    criteria: Dict[str, Any]
    options: List[str]
    scoring: Dict[str, Any]


@dataclass
class Rubric:
    name: str
    description: str
    target_agent: Optional[str]
    items: List[RubricItem]
    prompt_template: str


class EduMirrorRater:
    def __init__(self, model: Any):
        self._model = model

    def load_transcript(self, path: str) -> List[Dict[str, Any]]:
        data: List[Dict[str, Any]] = []
        if not os.path.exists(path):
            return data
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    data.append(obj)
                except Exception:
                    pass
        return data

    def analyze_transcript(self, transcript: List[Dict[str, Any]], rubric: Rubric) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        for entry in transcript:
            step = entry.get("Step")
            scene = entry.get("Scene")
            event = entry.get("Event", "")
            agent = self._extract_agent(event)
            if rubric.target_agent and agent != rubric.target_agent:
                continue
            for item in rubric.items:
                matched, option, severity, evidence = self._match_item(event, item)
                if matched:
                    rows.append({
                        "time_step": step,
                        "scene": scene,
                        "agent": agent,
                        "rubric": rubric.name,
                        "item_id": item.id,
                        "label": item.label,
                        "option": option,
                        "score": self._option_score(item, option),
                        "severity": severity,
                        "evidence": evidence,
                    })
        df = pd.DataFrame(rows)
        return df

    def _extract_agent(self, event_text: str) -> str:
        if not event_text:
            return ""
        t = event_text.strip()
        if t.startswith("Event:"):
            t = t[len("Event:"):].strip()
        parts = t.split(":", 1)
        if parts:
            name_part = parts[0].strip()
            return name_part.split()[0].strip()
        return ""

    def _match_item(self, event_text: str, item: RubricItem) -> tuple[bool, str, int, str]:
        text = (event_text or "").lower()
        keys = item.criteria.get("keywords", [])
        matched = False
        evidence = ""
        for k in keys:
            kl = str(k).lower()
            if kl and kl in text:
                matched = True
                evidence = k
                break
        if not matched:
            return False, "", 0, ""
        option = item.options[0] if item.options else ""
        severity = item.scoring.get("severity_map", {}).get(option, 1)
        return True, option, severity, evidence

    def _option_score(self, item: RubricItem, option: str) -> float:
        m = item.scoring.get("score_map", {})
        if option in m:
            return float(m[option])
        return 0.0

    def save_results(self, df: pd.DataFrame, output_dir: str, filename_prefix: str) -> None:
        os.makedirs(output_dir, exist_ok=True)
        csv_path = os.path.join(output_dir, f"{filename_prefix}_results.csv")
        json_path = os.path.join(output_dir, f"{filename_prefix}_results.json")
        df.to_csv(csv_path, index=False)
        df.to_json(json_path, orient="table")

    def apply_rubrics(self, transcript: List[Dict[str, Any]], rubrics: List[Rubric]) -> Dict[str, pd.DataFrame]:
        out: Dict[str, pd.DataFrame] = {}
        for r in rubrics:
            out[r.name] = self.analyze_transcript(transcript, r)
        return out