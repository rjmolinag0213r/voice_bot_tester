"""Base class for patient personas."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BasePersona(ABC):
    """Abstract base class for patient personas."""
    
    def __init__(self, name: str, description: str):
        """Initialize persona.
        
        Args:
            name: Persona name
            description: Brief description of persona
        """
        self.name = name
        self.description = description
        self.conversation_history = []
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this persona.
        
        Returns:
            System prompt string
        """
        pass
    
    @abstractmethod
    def get_initial_greeting(self) -> str:
        """Get the initial greeting/opening statement.
        
        Returns:
            Initial greeting string
        """
        pass
    
    @abstractmethod
    def get_testing_goal(self) -> str:
        """Get the testing goal for this persona.
        
        Returns:
            Testing goal description
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert persona to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'name': self.name,
            'description': self.description,
            'testing_goal': self.get_testing_goal(),
            'system_prompt': self.get_system_prompt()
        }
