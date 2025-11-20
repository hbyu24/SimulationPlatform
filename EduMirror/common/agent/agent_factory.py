# Copyright 2024 EduSim Project.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Agent factory for creating different types of educational simulation agents."""

import sys
import os
import importlib
import types
from typing import List, Callable, Any, Optional, Dict, Mapping
import numpy as np

# Add concordia path to sys.path
concordia_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'concordia-git')
sys.path.insert(0, concordia_path)

from concordia.agents import entity_agent_with_logging
from concordia.associative_memory import basic_associative_memory
from concordia.associative_memory import formative_memories
from concordia.clocks import game_clock
# Import our project's model configuration instead of direct concordia import
# from concordia.language_model import language_model
from concordia.prefabs.entity import basic_with_plan
from concordia.utils import measurements as measurements_lib


class AgentFactory:
    """Factory class for creating educational simulation agents.
    
    This factory provides a simple and unified API for creating different types
    of agents (students, teachers, parents) with consistent architecture but
    different characteristics and behaviors.
    """
    
    def __init__(self, model: Any, embedder_model: Callable[[str], np.ndarray]):
        """Initialize the agent factory.
        
        Args:
            model: Language model for agent reasoning
            embedder_model: Function to create text embeddings
        """
        self._model = model
        self._embedder_model = embedder_model
        self._value_agent_builders: Dict[str, Callable[..., entity_agent_with_logging.EntityAgentWithLogging]] = {}
    
    def _create_memory_bank(self) -> basic_associative_memory.AssociativeMemoryBank:
        """Create an empty memory bank.
        
        Returns:
            Configured AssociativeMemoryBank instance
        """
        return basic_associative_memory.AssociativeMemoryBank(
            sentence_embedder=self._embedder_model
        )

    def register_external_builders(self, base_path: Optional[str] = None) -> None:
        if base_path is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            base_path = os.path.join(project_root, 'agent')
        if base_path not in sys.path:
            sys.path.insert(0, base_path)
        nda_dir = os.path.join(base_path, 'examples', 'NDA')
        if nda_dir not in sys.path:
            sys.path.insert(0, nda_dir)
        d2a_dir = os.path.join(base_path, 'old_version')
        if d2a_dir not in sys.path:
            sys.path.insert(0, d2a_dir)
        try:
            importlib.import_module('concordia.components.agent.observation')
        except Exception:
            obs_adapter = importlib.import_module('common.agent.adapters.concordia_obs_compat')
            sys.modules['concordia.components.agent.observation'] = obs_adapter
            agent_pkg = importlib.import_module('concordia.components.agent')
            setattr(agent_pkg, 'observation', obs_adapter)
        try:
            importlib.import_module('concordia.associative_memory.associative_memory')
        except ImportError:
            basic_mod = importlib.import_module('concordia.associative_memory.basic_associative_memory')
            sys.modules['concordia.associative_memory.associative_memory'] = basic_mod
            pkg = importlib.import_module('concordia.associative_memory')
            setattr(pkg, 'associative_memory', basic_mod)
        try:
            importlib.import_module('concordia.memory_bank.legacy_associative_memory')
        except ImportError:
            legacy_mod = importlib.import_module('concordia.deprecated.memory_bank.legacy_associative_memory')
            sys.modules['concordia.memory_bank.legacy_associative_memory'] = legacy_mod
            if importlib.util.find_spec('concordia.memory_bank'):
                mem_pkg = importlib.import_module('concordia.memory_bank')
            else:
                mem_pkg = types.ModuleType('concordia.memory_bank')
                sys.modules['concordia.memory_bank'] = mem_pkg
            setattr(mem_pkg, 'legacy_associative_memory', legacy_mod)
        try:
            importlib.import_module('concordia.components.agent.memory_component')
        except ImportError:
            mem_comp_mod = importlib.import_module('concordia.components.agent.deprecated.memory_component')
            sys.modules['concordia.components.agent.memory_component'] = mem_comp_mod
            agent_pkg = importlib.import_module('concordia.components.agent')
            setattr(agent_pkg, 'memory_component', mem_comp_mod)
        def _nda_builder(**kwargs):
            mod = importlib.import_module('examples.NDA.NDA_agent.ValueAgent')
            return getattr(mod, 'build_NDA_agent')(**kwargs)
        def _d2a_builder(**kwargs):
            mod = importlib.import_module('old_version.ValueAgent')
            return getattr(mod, 'build_D2A_agent')(**kwargs)
        self._value_agent_builders['psych'] = _nda_builder
        self._value_agent_builders['social'] = _d2a_builder
    
    def _create_base_agent(
        self,
        name: str,
        goal: str,
        traits: List[str],
        formative_memories_list: List[str],
        specific_instructions: str = ""
    ) -> entity_agent_with_logging.EntityAgentWithLogging:
        """Create a base agent using basic_with_plan prefab.
        
        Args:
            name: The agent's name.
            goal: The agent's primary goal.
            traits: List of personality traits.
            formative_memories_list: List of formative memories.
            specific_instructions: Role-specific instructions.
            
        Returns:
            A configured EntityAgentWithLogging instance.
        """
        # Create memory bank with formative memories
        memory_bank = self._create_memory_bank()
        
        # Add formative memories
        for memory in formative_memories_list:
            memory_bank.add(memory)
        
        # Create the basic_with_plan prefab
        prefab = basic_with_plan.Entity(
            params={
                'name': name,
                'goal': goal,
                'force_time_horizon': False,
            }
        )
        
        # Build the agent using the prefab
        agent = prefab.build(
            model=self._model,
            memory_bank=memory_bank
        )
        
        return agent

    def create_value_agent_psych(
        self,
        name: str,
        profile: str,
        background_knowledge: str,
        selected_desires: List[str],
        predefined_setting: Dict[str, int],
        context_dict: Dict[str, str],
        goal: Optional[str] = None,
        formative_memories_list: Optional[List[str]] = None,
        clock: Optional[game_clock.MultiIntervalClock] = None,
        main_character: bool = True,
        additional_components: Optional[Mapping[str, Any]] = None,
    ) -> entity_agent_with_logging.EntityAgentWithLogging:
        if 'psych' not in self._value_agent_builders:
            raise RuntimeError('Psych builders not registered')
        memory_bank = self._create_memory_bank()
        if formative_memories_list:
            for m in formative_memories_list:
                memory_bank.add(m)
        if clock is None:
            clock = game_clock.MultiIntervalClock(game_clock.GameClockConfig(time_step=game_clock.timedelta(hours=1)))
        config = formative_memories.AgentConfig(name=name, goal=goal, extras={'main_character': main_character})
        builder = self._value_agent_builders['psych']
        measurements = measurements_lib.Measurements()
        if additional_components is None:
            additional_components = types.MappingProxyType({})
        return builder(
            config=config,
            context_dict=context_dict,
            selected_desire=selected_desires,
            predefined_setting=predefined_setting,
            model=self._model,
            profile=profile,
            memory=memory_bank,
            background_knowledge=background_knowledge,
            clock=clock,
            update_time_interval=game_clock.timedelta(hours=1),
            additional_components=additional_components,
        )

    def create_value_agent_social(
        self,
        name: str,
        profile: str,
        background_knowledge: str,
        selected_desires: List[str],
        predefined_setting: Dict[str, int],
        context_dict: Dict[str, str],
        social_personality: str,
        stored_target_folder: str,
        agent_names: List[str],
        current_time: str,
        goal: Optional[str] = None,
        formative_memories_list: Optional[List[str]] = None,
        clock: Optional[game_clock.MultiIntervalClock] = None,
        main_character: bool = True,
        additional_components: Optional[Mapping[str, Any]] = None,
    ) -> entity_agent_with_logging.EntityAgentWithLogging:
        if 'social' not in self._value_agent_builders:
            raise RuntimeError('Social builders not registered')
        memory_bank = self._create_memory_bank()
        if formative_memories_list:
            for m in formative_memories_list:
                memory_bank.add(m)
        if clock is None:
            clock = game_clock.MultiIntervalClock(game_clock.GameClockConfig(time_step=game_clock.timedelta(hours=1)))
        config = formative_memories.AgentConfig(name=name, goal=goal, extras={'main_character': main_character})
        builder = self._value_agent_builders['social']
        measurements = measurements_lib.Measurements()
        if additional_components is None:
            additional_components = types.MappingProxyType({})
        return builder(
            config=config,
            context_dict=context_dict,
            selected_desire=selected_desires,
            predefined_setting=predefined_setting,
            model=self._model,
            profile=profile,
            memory=memory_bank,
            background_knowledge=background_knowledge,
            clock=clock,
            update_time_interval=game_clock.timedelta(hours=1),
            additional_components=additional_components,
            stored_target_folder=stored_target_folder,
            social_personality=social_personality,
            agent_names=agent_names,
            current_time=current_time,
        )
    
    def create_student(
        self,
        name: str,
        goal: str,
        traits: List[str],
        formative_memories: List[str],
        additional_params: Optional[Dict[str, Any]] = None
    ) -> entity_agent_with_logging.EntityAgentWithLogging:
        """Create a student agent.
        
        Args:
            name: The student's name.
            goal: The student's primary goal or motivation.
            traits: List of personality traits (e.g., ['curious', 'shy', 'hardworking']).
            formative_memories: List of key memories that shape the student's behavior.
            additional_params: Optional additional parameters for customization.
            
        Returns:
            A configured student agent.
        """
        student_instructions = (
            "You are a student in an educational environment. "
            "You interact with teachers, parents, and other students. "
            "You have your own thoughts, feelings, and reactions to situations. "
            "You may face academic challenges, social pressures, and personal growth opportunities."
        )
        
        return self._create_base_agent(
            name=name,
            goal=goal,
            traits=traits,
            formative_memories_list=formative_memories
        )
    
    def create_teacher(
        self,
        name: str,
        goal: str,
        traits: List[str],
        formative_memories: List[str],
        subject_area: str = "general education",
        additional_params: Optional[Dict[str, Any]] = None
    ) -> entity_agent_with_logging.EntityAgentWithLogging:
        """Create a teacher agent.
        
        Args:
            name: The teacher's name.
            goal: The teacher's primary goal or educational philosophy.
            traits: List of personality traits (e.g., ['patient', 'strict', 'encouraging']).
            formative_memories: List of key memories that shape the teacher's approach.
            subject_area: The subject area the teacher specializes in.
            additional_params: Optional additional parameters for customization.
            
        Returns:
            A configured teacher agent.
        """
        teacher_instructions = (
            f"You are a teacher specializing in {subject_area}. "
            "You are responsible for educating and guiding students. "
            "You interact with students, parents, and other educators. "
            "You care about student development and maintain professional standards. "
            "You may need to handle classroom management, curriculum delivery, and student assessment."
        )
        
        return self._create_base_agent(
            name=name,
            goal=goal,
            traits=traits,
            formative_memories_list=formative_memories
        )
    
    def create_parent(
        self,
        name: str,
        goal: str,
        traits: List[str],
        formative_memories: List[str],
        child_name: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> entity_agent_with_logging.EntityAgentWithLogging:
        """Create a parent agent.
        
        Args:
            name: The parent's name.
            goal: The parent's primary goal regarding their child's development.
            traits: List of personality traits (e.g., ['protective', 'supportive', 'demanding']).
            formative_memories: List of key memories that shape the parent's approach.
            child_name: The name of their child (student).
            additional_params: Optional additional parameters for customization.
            
        Returns:
            A configured parent agent.
        """
        parent_instructions = (
            f"You are the parent of {child_name}. "
            "You care deeply about your child's wellbeing and development. "
            "You interact with teachers, other parents, and your child. "
            "You may have concerns about academic performance, social development, and future prospects. "
            "You balance support and expectations in your parenting approach."
        )
        
        return self._create_base_agent(
            name=name,
            goal=goal,
            traits=traits,
            formative_memories_list=formative_memories
        )
    
    def create_custom_agent(
        self,
        name: str,
        goal: str,
        traits: List[str],
        formative_memories: List[str],
        role_description: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> entity_agent_with_logging.EntityAgentWithLogging:
        """Create a custom agent with specified role.
        
        Args:
            name: The agent's name.
            goal: The agent's primary goal.
            traits: List of personality traits.
            formative_memories: List of key memories.
            role_description: Description of the agent's role and responsibilities.
            additional_params: Optional additional parameters for customization.
            
        Returns:
            A configured custom agent.
        """
        return self._create_base_agent(
            name=name,
            goal=goal,
            traits=traits,
            formative_memories_list=formative_memories
        )
