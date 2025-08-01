# dungeon_neo/world_builder.py
import json
import random
from .ai_integration import DungeonAI
from pathlib import Path

class WorldBuilder:
    TEMPLATES = {
        "campaign_foundation": {
            "prompt": "Create a campaign foundation for a {theme} setting",
            "response": {
                "name": "string",
                "description": "string",
                "core_conflict": "string",
                "major_factions": ["string"],
                "key_locations": ["string"]
            }
        },
        "region": {
            "prompt": "Generate a region description for a {theme} campaign",
            "response": {
                "name": "string",
                "description": "string",
                "geography": "string",
                "climate": "string",
                "key_features": ["string"]
            }
        },
        "location": {
            "prompt": "Generate a {location_type} location for a {theme} setting",
            "response": {
                "id": "string",
                "name": "string",
                "type": "string",
                "description": "string",
                "features": ["string"],
                "services": ["string"],
                "dungeon_type": "string"
            }
        },
        "faction": {
            "prompt": "Generate a faction for a {theme} setting",
            "response": {
                "id": "string",
                "name": "string",
                "ideology": "string",
                "goals": ["string"],
                "resources": ["string"],
                "relationships": {"string": "string"},
                "activities": ["string"]
            }
        },
        "npc": {
            "prompt": "Generate an NPC for a {location} location in a {theme} setting",
            "response": {
                "id": "string",
                "name": "string",
                "role": "string",
                "motivation": "string",
                "dialogue": ["string"]
            }
        },
        "dungeon_type": {
            "prompt": "Generate a dungeon type for a {location} in a {theme} setting",
            "response": {
                "type": "string",
                "description": "string",
                "themes": ["string"],
                "common_creatures": ["string"]
            }
        },
        "quest": {
            "prompt": "Generate a quest for a {location} in a {theme} setting",
            "response": {
                "id": "string",
                "title": "string",
                "description": "string",
                "objectives": ["string"],
                "dungeon_required": "boolean"
            }
        },
        "story_arc": {
            "prompt": "Generate a {scope}-scope story arc for a {theme} campaign",
            "response": {
                "name": "string",
                "description": "string",
                "key_events": ["string"],
                "major_players": ["string"],
                "potential_endings": ["string"]
            }
        }
    }
    
    def __init__(self, ai_system: DungeonAI):
        self.ai = ai_system
    
    def generate(self, entity_type: str, **kwargs) -> dict:
        # Check if entity type is supported
        if entity_type not in self.TEMPLATES:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        # Get template for this entity type
        template = self.TEMPLATES[entity_type]
        
        # Format prompt with provided kwargs
        prompt = template["prompt"].format(**kwargs)
        
        # Add theme if not provided
        if "theme" not in kwargs:
            prompt += f" in a {kwargs.get('theme', 'fantasy')} setting"
        
        # Get response format
        response_format = template["response"]
        
        # Use the new structured generation method
        result = self.ai.generate_structured_data(prompt, response_format)

        
        # Handle string returns (fallback)
        if isinstance(result, str):
            return self._generate_fallback(entity_type, **kwargs)
        
        return result
    
    def _generate_fallback(self, entity_type: str, **kwargs) -> dict:
        """Fallback generator for when AI returns a string instead of structured data"""
        theme = kwargs.get("theme", "fantasy")
        location_type = kwargs.get("location_type", "generic")
        
        fallbacks = {
            "campaign_foundation": {
                "name": f"The {theme.capitalize()} Chronicles",
                "description": f"A grand adventure in a {theme} world",
                "core_conflict": "The struggle between light and darkness",
                "major_factions": ["Order of the Sun", "Shadow Collective"],
                "key_locations": ["Capital City", "Dark Forest"]
            },
            "region": {
                "name": f"{theme.capitalize()} Frontier",
                "description": f"A wild frontier region in a {theme} setting",
                "geography": "Varied landscapes with mountains, forests, and rivers",
                "climate": "Temperate with seasonal changes",
                "key_features": ["Great River", "Ancient Forest", "Mystic Mountains"]
            },
            "location": {
                "id": f"loc_{random.randint(1000,9999)}",
                "name": f"{location_type.capitalize()} of {theme.capitalize()}",
                "type": location_type,
                "description": f"A {location_type} location in a {theme} setting",
                "features": ["Central square", "Market district", "Ancient monument"],
                "services": ["Inn", "Blacksmith", "General Store"],
                "dungeon_type": f"{theme}_dungeon"
            },
            "faction": {
                "id": f"fac_{random.randint(1000,9999)}",
                "name": f"{theme.capitalize()} Guardians",
                "ideology": "Protecting the realm from darkness",
                "goals": ["Maintain order", "Defend the weak"],
                "resources": ["Skilled warriors", "Ancient artifacts"],
                "relationships": {"Merchant Guild": "Allied"},
                "activities": ["Patrol borders", "Train recruits"]
            },
            "npc": {
                "id": f"npc_{random.randint(1000,9999)}",
                "name": f"Guardian {random.choice(['Aelar', 'Borin', 'Celia'])}",
                "role": "Protector",
                "motivation": "Keep the town safe",
                "dialogue": ["The darkness is gathering...", "We need brave adventurers!"]
            },
            "dungeon_type": {
                "type": f"{theme}_crypt",
                "description": f"Ancient crypt filled with {theme} creatures",
                "themes": ["Decay", "Ancient evil"],
                "common_creatures": ["Skeletons", "Zombies", "Ghosts"]
            },
            "quest": {
                "id": f"quest_{random.randint(1000,9999)}",
                "title": f"The {theme.capitalize()} Threat",
                "description": f"Deal with a growing threat in the {theme} region",
                "objectives": ["Investigate the source", "Defeat the leader"],
                "dungeon_required": True
            },
            "story_arc": {
                "name": f"Rise of the {theme.capitalize()} Lord",
                "description": f"A powerful entity threatens the {theme} realm",
                "key_events": ["The awakening", "The gathering storm", "The final confrontation"],
                "major_players": ["The Hero", "The Dark Lord", "The Wise Mentor"],
                "potential_endings": ["Heroic victory", "Bittersweet peace", "Darkness prevails"]
            }
        }
        
        return fallbacks.get(entity_type, {})