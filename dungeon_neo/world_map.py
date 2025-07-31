# world_map.py
from dungeon_neo.campaign import Location
from typing import Dict, List

class WorldMap:
    def __init__(self):
        self.locations: Dict[str, Location] = {}
        self.connections: Dict[str, List[str]] = {}
        self.current_location: str = None
    
    def add_location(self, location: Location):
        self.locations[location.id] = location
        
    def connect_locations(self, loc1_id: str, loc2_id: str, bidirectional=True):
        if loc1_id not in self.connections:
            self.connections[loc1_id] = []
        self.connections[loc1_id].append(loc2_id)
        
        if bidirectional:
            if loc2_id not in self.connections:
                self.connections[loc2_id] = []
            self.connections[loc2_id].append(loc1_id)
    
    def get_location(self, location_id: str) -> Location:
        return self.locations.get(location_id)
    
    def get_adjacent_locations(self, location_id: str) -> List[Location]:
        return [self.locations[adj_id] for adj_id in self.connections.get(location_id, [])]
    
    def travel_to(self, location_id: str) -> bool:
        if location_id in self.locations:
            self.current_location = location_id
            return True
        return False
    
    def get_map_data(self) -> dict:
        return {
            "locations": {id: loc.to_dict() for id, loc in self.locations.items()},
            "connections": self.connections,
            "currentLocation": self.current_location
        }