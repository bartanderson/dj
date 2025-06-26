# game\state.py - Unified game state management
from dungeon.generator import EnhancedDungeonGenerator
from dungeon.state import EnhancedDungeonState
from dungeon.objects import EnvironmentalEffect, MONSTER_DB, FEATURE_TEMPLATES
from src.AIDMFramework import PuzzleEntity
import random

class TrapSystem:
    def __init__(self):
        self.traps = {}
        
    def add_trap(self, position, trap_type, dc, effect):
        trap_id = f"trap_{len(self.traps)+1}"
        self.traps[trap_id] = {
            "position": position,
            "type": trap_type,
            "dc": dc,  # Difficulty class to detect/avoid
            "effect": effect,
            "triggered": False
        }
        return trap_id

class ItemSystem:
    ITEM_TYPES = {
        "consumable": ["health_potion", "mana_potion", "antidote"],
        "equipment": ["sword", "shield", "armor"],
        "key_item": ["dungeon_key", "ancient_relic"],
        "quest": ["lost_amulet", "dragon_scale"],
        "valuable": ["gold_coins", "gemstone", "silver_ring"],
        "junk": ["broken_shard", "dusty_bone", "torn_cloth"],
        "special": ["get_out_of_jail_card", "mysterious_scroll"]
    }
    
    def __init__(self):
        self.items = {}
        self.item_counter = 1
        
    def create_item(self, item_type, subtype=None, **kwargs):
        """Create a new item with automatic categorization"""
        if subtype is None:
            if item_type in self.ITEM_TYPES:
                subtype = random.choice(self.ITEM_TYPES[item_type])
            else:
                subtype = "mysterious_item"
                
        item_id = f"item_{self.item_counter}"
        self.item_counter += 1
        
        self.items[item_id] = {
            "id": item_id,
            "name": kwargs.get("name", subtype.replace("_", " ").title()),
            "type": item_type,
            "subtype": subtype,
            "description": kwargs.get("description", f"A {subtype.replace('_', ' ')}"),
            "value": kwargs.get("value", random.randint(1, 100)),
            "weight": kwargs.get("weight", 0.1),
            "attributes": kwargs.get("attributes", {}),
            "discovered": False
        }
        return item_id
    
    def place_item(self, item_id, location_type, location_id, hidden=False):
        """Place item in a specific location"""
        item = self.items.get(item_id)
        if not item:
            return False
            
        item["location"] = {"type": location_type, "id": location_id}
        item["hidden"] = hidden
        return True

class UnifiedGameState:
    def __init__(self, campaign_theme="default"):
        self.campaign_theme = campaign_theme
        self.characters = {}
        self.monsters = {}
        self.active_quests = {}
        self.completed_quests = {}
        self.game_log = []
        self.dungeon_state = None
        self.current_level = 0
        self.party_position = (0, 0)
        self.active_puzzle = None
        self.puzzle_history = {}
        self.npcs = {}  # NPC storage: {npc_id: {name, position, dialogue, ...}}
        self.items = {}  # Item storage: {item_id: {name, description, ...}}

    def add_npc(self, npc_id, name, position, dialogue, role="neutral"):
        self.npcs[npc_id] = {
            'name': name,
            'position': position,
            'dialogue': dialogue,
            'role': role,
            'quests': []
        }
    
    def interact_with_npc(self, npc_id):
        npc = self.npcs.get(npc_id)
        if not npc:
            return "No NPC found"
        
        # Check if NPC is nearby
        if npc['position'] not in self.dungeon_state.visibility.get_visible_cells():
            return f"{npc['name']} is too far to interact with"
        
        return {
            'name': npc['name'],
            'dialogue': npc['dialogue'],
            'quests': npc.get('quests', [])
        }

    def assign_quest(self, npc_id, quest_id):
        if npc_id in self.npcs and quest_id in self.active_quests:
            self.npcs[npc_id]['quests'].append(quest_id)
            return True
        return False
    
    def assign_quest(self, npc_id, quest_id):
        if npc_id in self.npcs and quest_id in self.active_quests:
            self.npcs[npc_id]['quests'].append(quest_id)
            return True
        return False
        
    def initialize_dungeon(self, **params):
        generator = EnhancedDungeonGenerator({
            'seed': params.get('seed', random.randint(1, 100000)),
            'n_rows': 39,
            'n_cols': 39,
            'room_min': params.get('room_min', 3),
            'room_max': params.get('room_max', 9),
            'theme': params.get('theme', 'dungeon'),
            'difficulty': params.get('difficulty', 'medium'),
            'feature_density': params.get('feature_density', 0.1)
        })

        generator.create_dungeon() # This initializes the generator's internal state

        self.dungeon_state = EnhancedDungeonState(generator)
        self.current_level = 1
        self.party_position = self.find_starting_position()
        
    def find_starting_position(self):
        """Find stairs or suitable starting position"""
        if self.dungeon_state.stairs:
            return self.dungeon_state.stairs[0]['position']
        # Find first open space
        for r in range(len(self.dungeon_state.grid)):
            for c in range(len(self.dungeon_state.grid[0])):
                if self.dungeon_state.grid[r][c].base_type & DungeonGenerator.OPENSPACE:
                    return (r, c)
        return (0, 0)
    
    def generate_new_level(self, **params):
        self.initialize_dungeon(**params)
        self.game_log.append(f"Descended to dungeon level {self.current_level}")
        
    def add_character(self, character):
        self.characters[character.id] = character
        character.position = self.party_position

    def get_character(self, character_id: str):
        """Get a character by ID"""
        return self.characters.get(character_id)
        
    def move_party(self, direction):
        # Calculate new position
        dr, dc = {
            'north': (-1, 0),
            'south': (1, 0),
            'east': (0, 1),
            'west': (0, -1)
        }.get(direction, (0, 0))
        
        new_pos = (self.party_position[0] + dr, self.party_position[1] + dc)
        
        # Check if move is valid
        if self.is_valid_position(new_pos):
            self.party_position = new_pos
            # Update all character positions
            for char in self.characters.values():
                char.position = new_pos
            self.game_log.append(f"Party moved {direction} to {new_pos}")
            return True
        return False
    
    def is_valid_position(self, pos):
        """Check if position is traversable"""
        x, y = pos
        if not (0 <= x < len(self.dungeon_state.grid) and 
                0 <= y < len(self.dungeon_state.grid[0])):
            return False
            
        cell = self.dungeon_state.grid[x][y]
        return bool(cell.current_type & DungeonGenerator.OPENSPACE)

    def complete_puzzle(self, puzzle_id: str):
        """Mark a puzzle as completed"""
        self.puzzle_history[puzzle_id] = {
            "timestamp": datetime.now().isoformat(),
            "attempts": len(self.active_puzzle.attempts)
        }
        self.active_puzzle = None

    def activate_puzzle(self, puzzle_id: str) -> PuzzleEntity:
        """Activate a puzzle with hints from dungeon state"""
        # Get puzzle data from dungeon
        puzzle_data = self.dungeon_state.get_puzzle_data(puzzle_id)
        
        # Create puzzle entity
        puzzle = PuzzleEntity(
            puzzle_id, 
            puzzle_data['description'],
            success_effect=puzzle_data['success_effect']
        )
        
        # Add hints
        for hint in puzzle_data.get('hints', []):
            puzzle.add_hint(hint['text'])
            
        return puzzle