"""Checkpoint management utilities for EduSim simulations.

This module provides standardized functions for saving and loading simulation states
across all scenarios in the EduSim project. It ensures consistent checkpoint handling
and error management.

Usage:
    from common.simulation_utils import save_simulation_state, load_simulation_from_checkpoint
    
    # Save simulation state
    save_simulation_state(simulation_object, "path/to/checkpoint.pkl")
    
    # Load simulation state
    restored_sim = load_simulation_from_checkpoint(
        "path/to/checkpoint.pkl", config, model, embedder
    )
"""

import os
import pickle
from typing import Callable, Any
import numpy as np

from concordia.prefabs.simulation import generic as simulation
from concordia.language_model import language_model
from concordia.typing import prefab


class CheckpointManager:
    """Manager class for simulation checkpoint operations.
    
    This class provides a centralized interface for checkpoint management,
    including directory creation, file naming conventions, and error handling.
    """
    
    def __init__(self, base_directory: str):
        """Initialize checkpoint manager.
        
        Args:
            base_directory: Base directory for storing checkpoints
        """
        self.base_directory = base_directory
        os.makedirs(base_directory, exist_ok=True)
    
    def get_checkpoint_path(self, checkpoint_name: str) -> str:
        """Generate standardized checkpoint file path.
        
        Args:
            checkpoint_name: Name for the checkpoint (without extension)
            
        Returns:
            Full path to checkpoint file
        """
        if not checkpoint_name.endswith('.pkl'):
            checkpoint_name += '.pkl'
        return os.path.join(self.base_directory, checkpoint_name)
    
    def save_checkpoint(self, simulation_object: simulation.Simulation, checkpoint_name: str) -> bool:
        """Save simulation checkpoint using the manager.
        
        Args:
            simulation_object: The simulation object to save
            checkpoint_name: Name for the checkpoint
            
        Returns:
            True if successful, False otherwise
        """
        filepath = self.get_checkpoint_path(checkpoint_name)
        return save_simulation_state(simulation_object, filepath)
    
    def load_checkpoint(
        self,
        checkpoint_name: str,
        config: prefab.Config,
        model: language_model.LanguageModel,
        embedder: Callable[[str], np.ndarray]
    ) -> simulation.Simulation:
        """Load simulation checkpoint using the manager.
        
        Args:
            checkpoint_name: Name of the checkpoint to load
            config: Simulation configuration (must match original)
            model: Language model (must match original)
            embedder: Embedding function (must match original)
            
        Returns:
            Restored simulation object
        """
        filepath = self.get_checkpoint_path(checkpoint_name)
        return load_simulation_from_checkpoint(filepath, config, model, embedder)
    
    def list_checkpoints(self) -> list[str]:
        """List all available checkpoints in the base directory.
        
        Returns:
            List of checkpoint names (without .pkl extension)
        """
        if not os.path.exists(self.base_directory):
            return []
        
        checkpoints = []
        for filename in os.listdir(self.base_directory):
            if filename.endswith('.pkl') and not filename.endswith('.failed'):
                checkpoints.append(filename[:-4])  # Remove .pkl extension
        return sorted(checkpoints)
    
    def checkpoint_exists(self, checkpoint_name: str) -> bool:
        """Check if a checkpoint exists.
        
        Args:
            checkpoint_name: Name of the checkpoint to check
            
        Returns:
            True if checkpoint exists and is valid, False otherwise
        """
        filepath = self.get_checkpoint_path(checkpoint_name)
        return os.path.exists(filepath) and not os.path.exists(filepath + '.failed')


def save_simulation_state(simulation_object: simulation.Simulation, filepath: str) -> bool:
    """Save simulation state to file using pickle serialization.
    
    This function provides standardized checkpoint saving with proper error handling
    and logging. It follows the EduSim project specifications for checkpoint management.
    
    Args:
        simulation_object: The simulation object to save
        filepath: Path where to save the checkpoint file
        
    Returns:
        True if successful, False if failed
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Create checkpoint data
        checkpoint_data = simulation_object.make_checkpoint_data()
        
        # Save to file
        with open(filepath, 'wb') as f:
            pickle.dump(checkpoint_data, f)
        
        print(f"  [Checkpoint Saved] Simulation state saved to: {filepath}")
        return True
        
    except (TypeError, AttributeError) as e:
        print(f"  [Checkpoint Warning] Skipping save due to serialization issue: {e}")
        print(f"  [Info] Continuing simulation run but checkpointing is disabled")
        
        # Create failure marker file
        try:
            with open(filepath + '.failed', 'w') as f:
                f.write(f"Serialization failed: {e}")
        except Exception:
            pass  # Ignore errors when creating failure marker
        
        return False
    
    except Exception as e:
        print(f"  [Checkpoint Error] Save failed: {e}")
        return False


def load_simulation_from_checkpoint(
    filepath: str,
    config: prefab.Config,
    model: language_model.LanguageModel,
    embedder: Callable[[str], np.ndarray],
) -> simulation.Simulation:
    """Load simulation state from checkpoint file.
    
    This function provides standardized checkpoint loading with proper error handling
    and fallback mechanisms. It follows the EduSim project specifications for
    checkpoint management.
    
    Args:
        filepath: Path to the checkpoint file
        config: Simulation configuration (must match original)
        model: Language model (must match original)
        embedder: Embedding function (must match original)
        
    Returns:
        Restored simulation object (or new instance if loading fails)
    """
    # Check for failure marker file
    if os.path.exists(filepath + '.failed'):
        print(f"  [Load Warning] Failure marker detected, creating new simulation instance")
        return simulation.Simulation(
            config=config,
            model=model,
            embedder=embedder,
        )
    
    try:
        # Load checkpoint data
        with open(filepath, 'rb') as f:
            checkpoint_data = pickle.load(f)
        
        # Create new simulation instance
        new_simulation = simulation.Simulation(
            config=config,
            model=model,
            embedder=embedder,
        )
        
        # Load from checkpoint
        new_simulation.load_from_checkpoint(checkpoint_data)
        print(f"  [Load Success] Restored simulation state from {filepath}")
        return new_simulation
        
    except (FileNotFoundError, pickle.UnpicklingError) as e:
        print(f"  [Load Warning] Unable to read checkpoint file, creating new simulation instance: {e}")
        return simulation.Simulation(
            config=config,
            model=model,
            embedder=embedder,
        )
    
    except Exception as e:
        print(f"  [Load Error] Load failed, creating new simulation instance: {e}")
        return simulation.Simulation(
            config=config,
            model=model,
            embedder=embedder,
        )
