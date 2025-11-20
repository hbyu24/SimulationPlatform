from typing import Any, Mapping, Sequence
from datetime import datetime

from concordia.associative_memory import basic_associative_memory
from concordia.prefabs.game_master import dialogic_and_dramaturgic as dialogic_gm
from concordia.prefabs.game_master import formative_memories_initializer as initializer_gm
from concordia.environment.engines.sequential import Sequential
from concordia.typing import scene as scene_lib


class SceneBuilder:
    def __init__(self, model: Any, embedder_model: Any):
        self._model = model
        self._embedder_model = embedder_model

    def _create_memory_bank(self) -> basic_associative_memory.AssociativeMemoryBank:
        return basic_associative_memory.AssociativeMemoryBank(
            sentence_embedder=self._embedder_model
        )

    def build_dialogic_and_dramaturgic_game_master(
        self,
        name: str,
        entities: Sequence[Any],
        scenes: Sequence[scene_lib.SceneSpec],
    ) -> Any:
        params = {
            'name': name,
            'scenes': scenes,
        }
        prefab = dialogic_gm.GameMaster(params=params, entities=entities)
        return prefab.build(model=self._model, memory_bank=self._create_memory_bank())

    def build_initializer_game_master(
        self,
        name: str,
        entities: Sequence[Any],
        params: Mapping[str, Any],
    ) -> Any:
        gm_params = {
            'name': name,
            'next_game_master_name': params.get('next_game_master_name', 'default rules'),
            'shared_memories': params.get('shared_memories', []),
            'player_specific_context': params.get('player_specific_context', {}),
            'player_specific_memories': params.get('player_specific_memories', {}),
        }
        prefab = initializer_gm.GameMaster(params=gm_params, entities=entities)
        return prefab.build(model=self._model, memory_bank=self._create_memory_bank())

    def make_scene_type(
        self,
        name: str,
        default_premise: Mapping[str, Sequence[str]] | None = None,
        action_spec: scene_lib.SceneTypeSpec | None = None,
        game_master_name: str | None = None,
        possible_participants: Sequence[str] | None = None,
    ) -> scene_lib.SceneTypeSpec:
        return scene_lib.SceneTypeSpec(
            name=name,
            game_master_name=game_master_name,
            default_premise=default_premise,
            action_spec=None,
            possible_participants=possible_participants,
        )

    def make_scene(
        self,
        scene_type: scene_lib.SceneTypeSpec,
        participants: Sequence[str],
        num_rounds: int,
        start_time: datetime | None = None,
        premise: Mapping[str, Sequence[str]] | None = None,
    ) -> scene_lib.SceneSpec:
        return scene_lib.SceneSpec(
            scene_type=scene_type,
            participants=participants,
            num_rounds=num_rounds,
            start_time=start_time,
            premise=premise,
        )

    def run_with_sequential_engine(
        self,
        game_masters: Sequence[Any],
        entities: Sequence[Any],
        premise: str = '',
        max_steps: int = 200,
        verbose: bool = False,
        log: list[Mapping[str, Any]] | None = None,
    ) -> None:
        engine = Sequential()
        engine.run_loop(
            game_masters=game_masters,
            entities=entities,
            premise=premise,
            max_steps=max_steps,
            verbose=verbose,
            log=log,
        )