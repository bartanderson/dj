# world_controller.py
from world_map import WorldMap
from campaign import Location, Quest
from party_system import PartySystem
from dungeon import DungeonSystem
from narrative_engine import NarrativeEngine
from pacing_controller import PacingManager
from game_state import GameState

class WorldController:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.world_map = game_state.world_map
        self.party_system = game_state.party_system
        self.narrative = game_state.narrative
        self.pacing = PacingManager()
    
    def travel_to_location(self, location_id: str) -> bool:
        if self.world_map.travel_to(location_id):
            location = self.world_map.get_location(location_id)
            
            # First discovery triggers events
            if not location.discovered:
                location.discovered = True
                self.narrative.on_location_discovered(location)
                self.pacing.on_discovery_event()
            
            # Update game state
            self.game_state.current_location = location
            return True
        return False
    
    def enter_dungeon(self, location_id: str) -> bool:
        location = self.world_map.get_location(location_id)
        if not location or not location.dungeon_type:
            return False
        
        # Initialize dungeon
        dungeon = DungeonSystem()
        dungeon.generate(
            dungeon_type=location.dungeon_type,
            level=location.dungeon_level
        )
        
        # Transfer party
        party = self.party_system.get_active_party()
        dungeon.set_party(party)
        
        # Set game state
        self.game_state.set_mode('dungeon')
        self.game_state.current_dungeon = dungeon
        self.game_state.dungeon_location = location_id
        
        # Narrative trigger
        self.narrative.on_dungeon_enter(location)
        
        return True
    
    def complete_dungeon(self, success: bool, rewards: dict):
        location_id = self.game_state.dungeon_location
        location = self.world_map.get_location(location_id)
        
        if success:
            # Apply rewards
            self.party_system.apply_rewards(rewards)
            
            # Complete related quests
            for quest in location.quests:
                if quest.dungeon_required and not quest.completed:
                    quest.completed = True
                    self.narrative.on_quest_complete(quest)
        
        # Return to world
        self.game_state.set_mode('world')
        self.game_state.current_dungeon = None
        self.pacing.on_dungeon_complete(success)
        
        return self.world_map.current_location