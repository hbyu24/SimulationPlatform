from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, List, Optional, Sequence

import pandas as pd

from concordia.components.game_master.questionnaire import Questionnaire as GMQuestionnaire
from concordia.components.game_master import event_resolution
from concordia.typing import entity as entity_lib
from concordia.contrib.data.questionnaires.base_questionnaire import QuestionnaireBase


class EduMirrorSurveyor:
    def __init__(
        self,
        questionnaires: Sequence[QuestionnaireBase],
        player_names: Sequence[str],
        pre_act_label: str = "Current Question",
    ) -> None:
        self._player_names: List[str] = list(player_names)
        self._questionnaire = GMQuestionnaire(
            questionnaires=questionnaires,
            player_names=self._player_names,
            pre_act_label=pre_act_label,
        )

    def run_once(
        self,
        responder: Callable[[str, str], str],
    ) -> Optional[pd.DataFrame]:
        spec = entity_lib.ActionSpec(
            call_to_action=",".join(self._player_names),
            output_type=entity_lib.OutputType.NEXT_ACTION_SPEC,
        )
        payload = self._questionnaire.pre_act(spec)
        try:
            items: List[Dict[str, Any]] = json.loads(payload)
        except Exception:
            items = []
        for item in items:
            player = item.get("player_name", "")
            q_id = item.get("question_id", "")
            action_spec_str = item.get("action_spec_str", "")
            if not player or not q_id:
                continue
            answer_text = responder(player, action_spec_str)
            observation = f"{event_resolution.PUTATIVE_EVENT_TAG} {player}: {q_id}: {answer_text}"
            self._questionnaire.pre_observe(observation)
        return self._questionnaire.get_questionnaires_results()

    def save_results(
        self,
        results_df: Optional[pd.DataFrame],
        output_dir: str,
        filename_prefix: str,
    ) -> None:
        answers = self._questionnaire.get_answers()
        os.makedirs(output_dir, exist_ok=True)
        answers_path = os.path.join(output_dir, f"{filename_prefix}_answers.json")
        with open(answers_path, "w", encoding="utf-8") as f:
            json.dump(answers, f, ensure_ascii=False, indent=2)
        if results_df is not None:
            results_csv = os.path.join(output_dir, f"{filename_prefix}_results.csv")
            results_json = os.path.join(output_dir, f"{filename_prefix}_results.json")
            results_df.to_csv(results_csv)
            results_df.to_json(results_json, orient="table")

    def reset(self) -> None:
        self._questionnaire.reset()

    def get_answers(self) -> Dict[str, Dict[str, Any]]:
        return self._questionnaire.get_answers()

    def get_results(self) -> Optional[pd.DataFrame]:
        return self._questionnaire.get_questionnaires_results()