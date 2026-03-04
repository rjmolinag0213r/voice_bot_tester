"""Factory for creating patient personas."""
from typing import List, Dict, Any
from src.personas.base_persona import BasePersona
from src.personas.scheduler import SchedulerPersona
from src.personas.refiller import RefillerPersona
from src.personas.confused_senior import ConfusedSeniorPersona
from src.personas.edge_case import EdgeCasePersona


class PersonaFactory:
    """Factory for creating and managing patient personas."""
    
    @staticmethod
    def get_all_personas() -> List[BasePersona]:
        """Get all available personas.
        
        Returns:
            List of persona instances
        """
        return [
            SchedulerPersona(),
            RefillerPersona(),
            ConfusedSeniorPersona(),
            EdgeCasePersona()
        ]
    
    @staticmethod
    def get_persona_by_name(name: str) -> BasePersona:
        """Get a specific persona by name.
        
        Args:
            name: Persona name
            
        Returns:
            Persona instance
            
        Raises:
            ValueError: If persona not found
        """
        personas = {
            "scheduler": SchedulerPersona(),
            "refiller": RefillerPersona(),
            "confused_senior": ConfusedSeniorPersona(),
            "edge_case": EdgeCasePersona()
        }
        
        name_lower = name.lower().replace(" ", "_")
        if name_lower in personas:
            return personas[name_lower]
        
        raise ValueError(f"Persona '{name}' not found")
    
    @staticmethod
    def get_personas_summary() -> List[Dict[str, Any]]:
        """Get summary of all personas.
        
        Returns:
            List of persona summaries
        """
        return [persona.to_dict() for persona in PersonaFactory.get_all_personas()]
