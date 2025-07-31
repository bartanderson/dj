from .dungeon import DungeonSystem
from dungeon_neo.movement_service import MovementService
from dungeon_neo.party_system import PartySystem
from collections import defaultdict
from dungeon_neo.campaign import WorldState, Location, NPC, Faction, Quest
from dungeon_neo.narrative_engine import NarrativeEngine
from dungeon_neo.pacing_controller import PacingManager
from dungeon_neo.ai_integration import DungeonAI
from dungeon_neo.world_builder import WorldBuilder
from dungeon_neo.world_map import WorldMap
from .session_manager import SessionManager  # New import
import uuid

class GameState:
    def __init__(self, campaign_theme: str = "fantasy"):
        # Core systems
        self.world_map = WorldMap()
        self.world = WorldState()
        self.ai = DungeonAI(self)
        self.world_builder = WorldBuilder(self.ai)
        self.session = SessionManager()  # Session manager
        self.narrative = NarrativeEngine(ai=self.ai, world=self.world, session=self.session)
        self.party_system = PartySystem(self)
        self.pacing = PacingManager()
        self.campaign_theme = campaign_theme

        # Dungeon systems (lazy-loaded)
        self.dungeon = None
        self.dungeon_active = False
        self.movement = MovementService(self)

        # Character/party state
        self.characters = []
        self.parties = []
        self.character_parties = {}
        self.user_characters = defaultdict(list)
        self.active_character_id = None
        self.in_combat = False

        # Generate starting campaign
        self.generate_campaign()


    def start_quest(self, quest_id: str):
        """Player starts a quest"""
        self.narrative.start_quest(quest_id)
    
    def complete_quest(self, quest_id: str):
        """Player completes a quest"""
        self.narrative.complete_quest(quest_id)
    
    def fail_quest(self, quest_id: str):
        """Player fails a quest"""
        self.narrative.fail_quest(quest_id)

    def generate_campaign(self):
        """Dynamically generate entire campaign based on theme"""
        # Generate campaign foundation
        foundation = self.world_builder.generate("campaign_foundation", theme=self.campaign_theme)
        
        # Generate starting region
        region = self.world_builder.generate("region", theme=self.campaign_theme)
        print("region")
        # Generate locations
        location_types = ["town", "forest", "mountain", "coast"]
        for loc_type in location_types:
            location_data = self.world_builder.generate(
                "location", 
                location_type=loc_type,
                theme=self.campaign_theme
            )
            location = Location(
                id=location_data["id"],
                name=location_data["name"],
                type=loc_type,
                description=location_data["description"],
                dungeon_type=location_data.get("dungeon_type")
            )
            self.world.add_location(location)
            self.populate_location(location.id)
        print(f"locations")
        
        # Set starting location
        starting_town = next(loc for loc in self.world.locations.values() if loc.type == "town")
        self.world_map.travel_to(starting_town.id)
        self.session.move_party(starting_town.id)  # Set session location
        
        # Generate main story arc
        main_arc = self.narrative.generate_story_arc(self.campaign_theme, "campaign")
        self.narrative.start_story_arc(main_arc)
        
        # Generate factions
        for _ in range(3):  # 3 initial factions
            faction_data = self.world_builder.generate("faction", theme=self.campaign_theme)
            faction = Faction(
                id=faction_data["id"],
                name=faction_data["name"],
                ideology=faction_data["ideology"],
                goals=faction_data["goals"]
            )
            self.world.add_faction(faction)
        if not self.dungeon_active:
            self.enter_dungeon(starting_town.id)

    def populate_location(self, location_id: str):
        """Generate content for a location"""
        location = self.world.get_location(location_id)
        
        # Generate NPCs
        for _ in range(3):  # 3 NPCs per location
            npc_data = self.world_builder.generate(
                "npc", 
                location=location.name,
                theme=self.campaign_theme
            )
            npc = NPC(
                id=npc_data["id"],
                name=npc_data["name"],
                role=npc_data["role"],
                motivation=npc_data["motivation"]
            )
            self.world.add_npc(npc)
        
        # Generate initial quest
        quest = self.narrative.generate_quest(location_id)
        self.world.add_quest(quest)
        # START TRACKING THE QUEST PROPERLY
        self.narrative.start_quest(quest.id)

    def enter_dungeon(self, location_id: str):
        """Enter a dungeon associated with a location"""
        location = self.world.get_location(location_id)
        
        # Handle case where location doesn't exist
        if not location:
            print(f"Error: Location {location_id} not found")
            return False
        
        # Generate dungeon type if not set
        if not location.dungeon_type:
            # Generate dungeon type dynamically
            dungeon_data = self.world_builder.generate(
                "dungeon_type",
                location=location.name,
                theme=self.campaign_theme
            )
            location.dungeon_type = dungeon_data.get("type", "default_dungeon")
        
        # Initialize dungeon system
        if not self.dungeon:
            self.dungeon = DungeonSystem()
        
        # Generate dungeon with parameters
        success = self.dungeon.generate(
            dungeon_type=location.dungeon_type,
            theme=self.campaign_theme,
            context=location.description
        )
        
        if not success:
            print("Dungeon generation failed")
            return False
            
        # Update state
        self.dungeon_active = True
        self.session.enter_dungeon(location_id)
        self.narrative.on_dungeon_enter(location_id)
        return True

    # === CHARACTER MANAGEMENT METHODS ===
    def add_character(self, character):
        """Add a new character to the game state"""
        self.characters.append(character)
        self.user_characters[character.owner_id].append(character.id)

    def get_character(self, char_id):
        """Retrieve a character by ID"""
        for char in self.characters:
            if char.id == char_id:
                return char
        return None
        
    def get_user_characters(self, user_id):
        """Get all characters belonging to a user"""
        return [c for c in self.characters if c.owner_id == user_id]
        
    def set_active_character(self, user_id, char_id):
        """Set a user's active character"""
        for char in self.get_user_characters(user_id):
            char.active = (char.id == char_id)
        self.active_character_id = char_id
        return True
    
    # === PARTY MANAGEMENT METHODS ===
    def create_party(self, leader_id):
        """Create a new party with a leader"""
        party = {
            "id": f"party_{uuid.uuid4().hex[:6]}",
            "leader": leader_id,
            "members": [leader_id]
        }
        self.parties.append(party)
        self.character_parties[leader_id] = party["id"]
        return party

    def join_party(self, char_id, party_id):
        """Add character to a party"""
        party = next((p for p in self.parties if p["id"] == party_id), None)
        if not party:
            return False
            
        if char_id not in party["members"]:
            party["members"].append(char_id)
            self.character_parties[char_id] = party_id
        return True

    def leave_party(self, char_id):
        """Remove character from their party"""
        party_id = self.character_parties.get(char_id)
        if not party_id:
            return False
            
        party = next((p for p in self.parties if p["id"] == party_id), None)
        if not party:
            return False
            
        party["members"].remove(char_id)
        del self.character_parties[char_id]
        
        # Handle party leadership change if needed
        if party["leader"] == char_id and party["members"]:
            party["leader"] = party["members"][0]
        return True
        
    # === DUNGEON OPERATIONS ===
    def move_party(self, direction, steps=1):
        """Move the active party in the dungeon"""
        if not self.dungeon_active:
            return {"success": False, "message": "Not in dungeon"}
        return self.movement.move_party(direction, steps)
    
    def get_dungeon_image(self, debug=False):
        """Get the current dungeon view"""
        if not self.dungeon_active:
            return None
        img = self.dungeon.get_image(debug)
        return img.convert('RGB') if img.mode == 'RGBA' else img
    
    def get_current_room(self):
        """Get description of current dungeon room"""
        if not self.dungeon_active:
            return "Not in dungeon"
        return self.dungeon.get_current_room_description()

    def reset_dungeon(self):
        """Regenerate the current dungeon"""
        if not self.dungeon_active:
            return False
        location_id = self.session.current_dungeon_id
        self.enter_dungeon(location_id)
        return True
        
    # === WORLD OPERATIONS ===
    def travel_to_location(self, location_id):
        """Move party to a new location"""
        if self.world_map.travel_to(location_id):
            location = self.world_map.get_location(location_id)
            self.session.move_party(location_id)
            self.narrative.on_location_discovered(location_id)
            return True
        return False