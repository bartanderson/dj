import time
from typing import Dict, List, Optional

class SessionManager:
    def __init__(self):
        self.session_id = f"session_{int(time.time())}"
        self.start_time = time.time()
        self.current_location_id: Optional[str] = None
        self.current_dungeon_id: Optional[str] = None
        self.active_quests: List[str] = []
        self.completed_quests: List[str] = []
        self.party_position: Dict[str, float] = {}
        self.elapsed_days = 0
        self.current_time = 0  # Minutes in-game (0-1440)
        self.weather: str = "clear"
        self.encounter_cooldown = 0
        self.active_quests: List[str] = []  # Quest IDs
        self.completed_quests: List[str] = []  # Quest IDs
        self.failed_quests: List[str] = []  # Quest IDs
        
    def move_party(self, location_id: str, position: Optional[Dict] = None):
        self.current_location_id = location_id
        if position:
            self.party_position = position
            
    def enter_dungeon(self, dungeon_id: str):
        self.current_dungeon_id = dungeon_id
        self.current_location_id = None
        
    def exit_dungeon(self):
        self.current_dungeon_id = None
        
    def start_quest(self, quest_id: str):
        if quest_id not in self.active_quests and quest_id not in self.completed_quests:
            self.active_quests.append(quest_id)
    
    def complete_quest(self, quest_id: str):
        if quest_id in self.active_quests:
            self.active_quests.remove(quest_id)
            self.completed_quests.append(quest_id)
    
    def fail_quest(self, quest_id: str):
        if quest_id in self.active_quests:
            self.active_quests.remove(quest_id)
            self.failed_quests.append(quest_id)
    
    def get_active_quests(self) -> List[str]:
        return self.active_quests
    
    def get_completed_quests(self) -> List[str]:
        return self.completed_quests
            
    def advance_time(self, minutes: int):
        self.current_time += minutes
        if self.current_time >= 1440:
            self.elapsed_days += 1
            self.current_time %= 1440
            # Update world state daily
            self.update_world_state()
            
    def update_world_state(self):
        """Update faction activities, NPC schedules, etc."""
        # This would be expanded to handle faction movements, 
        # settlement growth, etc. based on elapsed days
        pass
        
    def get_time_of_day(self) -> str:
        if 300 <= self.current_time < 600:
            return "dawn"
        elif 600 <= self.current_time < 1800:
            return "day"
        elif 1800 <= self.current_time < 2100:
            return "dusk"
        else:
            return "night"
            
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "current_location_id": self.current_location_id,
            "current_dungeon_id": self.current_dungeon_id,
            "active_quests": self.active_quests,
            "elapsed_days": self.elapsed_days,
            "current_time": self.current_time,
            "time_of_day": self.get_time_of_day(),
            "weather": self.weather
        }