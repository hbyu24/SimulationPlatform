from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Sequence

from concordia.typing import scene as scene_lib
from .scene_builder import SceneBuilder


class InterventionSpec:
    def __init__(self, name: str, scenes: Sequence[scene_lib.SceneSpec], output_label: str):
        self.name = name
        self.scenes = list(scenes)
        self.output_label = output_label


class InterventionScenarioRunner:
    def __init__(
        self,
        builder: SceneBuilder,
        entities: Sequence[Any],
        initializer_params: Dict[str, Any],
        output_root: str,
    ) -> None:
        self._builder = builder
        self._entities = list(entities)
        self._initializer_params = dict(initializer_params)
        self._output_root = output_root
        self._pre_scenes: List[scene_lib.SceneSpec] = []
        self._post_scenes: List[scene_lib.SceneSpec] = []
        self._interventions: List[InterventionSpec] = []

    def set_pipeline(
        self,
        pre_scenes: Sequence[scene_lib.SceneSpec],
        post_scenes: Sequence[scene_lib.SceneSpec],
    ) -> None:
        self._pre_scenes = list(pre_scenes)
        self._post_scenes = list(post_scenes)

    def set_interventions(self, interventions: Sequence[InterventionSpec]) -> None:
        self._interventions = list(interventions)

    def _build_initializer(self) -> Any:
        params = dict(self._initializer_params)
        params['next_game_master_name'] = 'conversation rules'
        return self._builder.build_initializer_game_master(
            name=params.get('name', 'initial setup rules'),
            entities=self._entities,
            params=params,
        )

    def _build_dialogic_gm(self, name: str, scenes: Sequence[scene_lib.SceneSpec]) -> Any:
        return self._builder.build_dialogic_and_dramaturgic_game_master(
            name='conversation rules',
            entities=self._entities,
            scenes=scenes,
        )

    def _sum_rounds(self, scenes: Sequence[scene_lib.SceneSpec]) -> int:
        return sum(s.num_rounds for s in scenes)

    def _make_windows(self, scenes: Sequence[scene_lib.SceneSpec]) -> List[tuple[int, int, str, List[str]]]:
        windows: List[tuple[int, int, str, List[str]]] = []
        current = 1
        for s in scenes:
            start = current
            end = current + s.num_rounds - 1
            name = s.scene_type.name
            parts = list(s.participants)
            windows.append((start, end, name, parts))
            current = end + 1
        return windows

    def _write_log(self, log: List[Dict[str, Any]], windows: List[tuple[int, int, str, List[str]]], out_file: str) -> None:
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        with open(out_file, 'w', encoding='utf-8') as f:
            step_idx = 1
            for entry in log:
                summary = entry.get('Summary', '')
                event_text = ''
                if isinstance(summary, str) and '---' in summary:
                    event_text = summary.split('---', 1)[1].strip()
                scene_name = ''
                participants: List[str] = []
                for start, end, name, parts in windows:
                    if start <= step_idx <= end:
                        scene_name = name
                        participants = parts
                        break
                safe_entry = {
                    'Step': step_idx,
                    'Scene': scene_name,
                    'Participants': participants,
                    'Event': event_text,
                }
                f.write(json.dumps(safe_entry, ensure_ascii=False) + '\n')
                step_idx += 1

    def run_pre_and_checkpoint(self, verbose: bool = True) -> Dict[str, Any]:
        initializer = self._build_initializer()
        pre_gm = self._build_dialogic_gm('conversation rules', self._pre_scenes)
        log: List[Dict[str, Any]] = []
        self._builder.run_with_sequential_engine(
            game_masters=[initializer, pre_gm],
            entities=self._entities,
            premise='',
            max_steps=self._sum_rounds(self._pre_scenes),
            verbose=verbose,
            log=log,
        )
        return {'log': log}

    def run_branch(self, intervention: InterventionSpec, verbose: bool = True) -> Dict[str, Any]:
        initializer = self._build_initializer()
        pre_gm = self._build_dialogic_gm('conversation rules', self._pre_scenes)
        mid_gm = self._build_dialogic_gm('conversation rules', intervention.scenes)
        post_gm = self._build_dialogic_gm('conversation rules', self._post_scenes)
        all_scenes = [*self._pre_scenes, *intervention.scenes, *self._post_scenes]
        log: List[Dict[str, Any]] = []
        self._builder.run_with_sequential_engine(
            game_masters=[initializer, pre_gm],
            entities=self._entities,
            premise='',
            max_steps=self._sum_rounds(self._pre_scenes),
            verbose=verbose,
            log=log,
        )
        self._builder.run_with_sequential_engine(
            game_masters=[mid_gm],
            entities=self._entities,
            premise='',
            max_steps=self._sum_rounds(intervention.scenes),
            verbose=verbose,
            log=log,
        )
        self._builder.run_with_sequential_engine(
            game_masters=[post_gm],
            entities=self._entities,
            premise='',
            max_steps=self._sum_rounds(self._post_scenes),
            verbose=verbose,
            log=log,
        )
        windows = self._make_windows(all_scenes)
        out_dir = os.path.join(self._output_root, f'condition_{intervention.output_label}')
        out_file = os.path.join(out_dir, 'simulation_events.jsonl')
        self._write_log(log, windows, out_file)
        return {'log': log, 'windows': windows, 'output_dir': out_dir}

    def run_all_branches(self, verbose: bool = True) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for spec in self._interventions:
            result = self.run_branch(spec, verbose=verbose)
            results.append(result)
        return results