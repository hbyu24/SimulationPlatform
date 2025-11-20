import json
import os
import base64
import requests
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw
from .model_setup import ModelConfig, create_language_model


class LogToComicGenerator:
    def __init__(self, text_model_config: Optional[ModelConfig] = None, image_model_name: str = "gemini-2.5-flash-image-preview", image_style: str = "Cartoon animation style, vibrant colors, soft shading, expressive faces, clean outlines, TV animation look"):
        self.text_model = create_language_model(
            text_model_config
            or ModelConfig(disable_language_model=True)
        )
        self.image_model_name = image_model_name
        self.image_style = image_style
        self.api_key = self._get_api_key()

    def parse_log(self, jsonl_path: str) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                events.append(obj)
        return events

    def structure_narrative(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = self._build_structuring_prompt(events)
        try:
            output = self.text_model.sample_text(prompt)
        except Exception:
            return self._heuristic_structure(events)
        data = self._safe_json_parse(output)
        panels = data.get("panels", [])
        if not isinstance(panels, list) or len(panels) != 4:
            return self._heuristic_structure(events)
        return data

    def build_image_prompts(self, scene_spec: Dict[str, Any]) -> List[str]:
        panels = scene_spec.get("panels", [])
        prompts: List[str] = []
        for panel in panels:
            p = self._build_image_prompt(panel)
            prompts.append(p)
        return prompts

    def generate_images(self, prompts: List[str], out_dir: str) -> List[str]:
        os.makedirs(out_dir, exist_ok=True)
        paths: List[str] = []
        for i, p in enumerate(prompts, start=1):
            out_path = os.path.join(out_dir, f"panel_{i}.png")
            try:
                base_image = paths[-1] if len(paths) > 0 else None
                self._generate_image_via_rest(p, out_path, base_image_path=base_image)
            except Exception:
                img = Image.new("RGB", (768, 768), (255, 255, 255))
                draw = ImageDraw.Draw(img)
                text = p[:300]
                draw.multiline_text((24, 24), text, fill=(0, 0, 0))
                img.save(out_path)
            paths.append(out_path)
        return paths

    def render_comic(self, image_paths: List[str], out_path: str, layout: str = "2x2") -> str:
        imgs = [Image.open(p).convert("RGB") for p in image_paths]
        if layout == "1x4":
            w = sum(i.width for i in imgs)
            h = max(i.height for i in imgs)
            canvas = Image.new("RGB", (w, h), (255, 255, 255))
            x = 0
            for im in imgs:
                canvas.paste(im, (x, 0))
                x += im.width
        else:
            top_h = max(imgs[0].height, imgs[1].height)
            bottom_h = max(imgs[2].height, imgs[3].height)
            w = imgs[0].width + imgs[1].width
            h = top_h + bottom_h
            canvas = Image.new("RGB", (w, h), (255, 255, 255))
            canvas.paste(imgs[0], (0, 0))
            canvas.paste(imgs[1], (imgs[0].width, 0))
            canvas.paste(imgs[2], (0, top_h))
            canvas.paste(imgs[3], (imgs[2].width, top_h))
        canvas.save(out_path)
        return out_path

    def _safe_json_parse(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except Exception:
            return {"panels": []}

    def _build_structuring_prompt(self, events: List[Dict[str, Any]]) -> str:
        return STRUCTURING_PROMPT_TEMPLATE.format(events=json.dumps(events, ensure_ascii=False))

    def _build_image_prompt(self, panel: Dict[str, Any]) -> str:
        pid = panel.get("id", "")
        title = panel.get("title", "")
        setting = panel.get("setting", "")
        summary = panel.get("summary", "")
        characters = panel.get("characters", [])
        emotions = panel.get("emotions", [])
        visual_focus = panel.get("visual_focus", "")
        return IMAGE_PROMPT_TEMPLATE.format(
            id=pid,
            title=title,
            setting=setting,
            summary=summary,
            characters=", ".join(characters),
            emotions=", ".join(emotions),
            visual_focus=visual_focus,
            style=self.image_style,
        )


    def _heuristic_structure(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        scenes: List[str] = []
        for e in events:
            s = e.get("Scene")
            if s and (len(scenes) == 0 or scenes[-1] != s):
                scenes.append(s)
        panels: List[Dict[str, Any]] = []
        titles = ["Setup", "Turning Point", "Support", "Reflection"]
        for i in range(4):
            setting = scenes[i] if i < len(scenes) else scenes[-1] if scenes else ""
            panels.append({
                "id": i + 1,
                "title": titles[i],
                "setting": setting,
                "summary": "",
                "characters": [],
                "emotions": [],
                "visual_focus": ""
            })
        return {"panels": panels}

    def _get_api_key(self) -> str:
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            key_file = os.path.join(os.path.dirname(__file__), ".gemini_api_key")
            if os.path.exists(key_file):
                with open(key_file, "r", encoding="utf-8") as f:
                    key = f.read().strip()
                os.environ["GEMINI_API_KEY"] = key
        return key or ""

    def _generate_image_via_rest(self, prompt: str, out_path: str, base_image_path: Optional[str] = None) -> None:
        if not self.api_key:
            raise RuntimeError("Missing GEMINI_API_KEY")
        url = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent".format(self.image_model_name)
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        parts: List[Dict[str, Any]] = []
        if base_image_path and os.path.exists(base_image_path):
            mime, data_b64 = self._encode_image_file(base_image_path)
            parts.append({"inline_data": {"mime_type": mime, "data": data_b64}})
        parts.append({"text": prompt})
        payload = {"contents": [{"parts": parts}]}
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"Request failed: {resp.status_code}, {resp.text}")
        data = resp.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        inline_data_obj = None
        for p in parts:
            inline_data_obj = p.get("inlineData") or p.get("inline_data")
            if inline_data_obj and inline_data_obj.get("data"):
                break
        if not inline_data_obj or not inline_data_obj.get("data"):
            raise RuntimeError(f"No inlineData image found: {json.dumps(data)[:500]}")
        img_b64 = inline_data_obj["data"]
        img_bytes = base64.b64decode(img_b64)
        with open(out_path, "wb") as fh:
            fh.write(img_bytes)

    def _encode_image_file(self, path: str) -> (str, str):
        ext = os.path.splitext(path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        with open(path, "rb") as f:
            data_b64 = base64.b64encode(f.read()).decode("utf-8")
        return mime, data_b64


STRUCTURING_PROMPT_TEMPLATE = """
You are a narrative structuring model. Read the simulation events and output EXACTLY the following JSON with 4 panels. Do not add commentary.

InputEvents: {events}

Output JSON schema:
{{
  "panels": [
    {{
      "id": 1,
      "title": "string",
      "setting": "string",
      "summary": "string",
      "characters": ["name: short visual descriptor"],
      "emotions": ["keywords"],
      "visual_focus": "string"
    }},
    {{"id": 2, "title": "string", "setting": "string", "summary": "string", "characters": ["name: short visual descriptor"], "emotions": ["keywords"], "visual_focus": "string"}},
    {{"id": 3, "title": "string", "setting": "string", "summary": "string", "characters": ["name: short visual descriptor"], "emotions": ["keywords"], "visual_focus": "string"}},
    {{"id": 4, "title": "string", "setting": "string", "summary": "string", "characters": ["name: short visual descriptor"], "emotions": ["keywords"], "visual_focus": "string"}}
  ]
}}

Rules:
- Ensure a complete arc: setup, rising tension, support or turning point, resolution or reflection.
- Use settings from events such as hallway, teacher office, classroom.
- Each panel must define stable character descriptors for consistent depiction.
- Output must be valid JSON only.
"""

IMAGE_PROMPT_TEMPLATE = """
Panel {id}: {title}
Primary action: {visual_focus}
Characters: {characters}
Setting: {setting}
Mood: {emotions}
Style: {style}, consistent character appearance across panels, colored backgrounds
Camera: medium shot, clear composition for {summary}
"""
