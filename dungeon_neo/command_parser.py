# In dungeon_neo/command_parser.py
import re

class CommandParser:
    DIRECTION_MAP = {
        'north': 'north', 'n': 'north', 'up': 'north',
        'south': 'south', 's': 'south', 'down': 'south',
        'east': 'east', 'e': 'east', 'right': 'east',
        'west': 'west', 'w': 'west', 'left': 'west',
        'northeast': 'northeast', 'ne': 'northeast',
        'northwest': 'northwest', 'nw': 'northwest',
        'southeast': 'southeast', 'se': 'southeast',
        'southwest': 'southwest', 'sw': 'southwest'
    }
    
    @staticmethod
    def parse_movement(command):
        command = command.lower().strip()
        
        # Try to extract direction and steps
        match = re.match(r'^(?:move|go|walk|head)\s+(\w+)(?:\s+(\d+))?', command)
        if not match:
            match = re.match(r'^(\w+)(?:\s+(\d+))?', command)
            
        if match:
            dir_str = match.group(1)
            steps = int(match.group(2)) if match.group(2) else 1
            
            # Map direction
            direction = CommandParser.DIRECTION_MAP.get(dir_str)
            if direction:
                return {
                    "endpoint": "/api/move",  # Unified endpoint
                    "method": "POST",
                    "payload": {
                        "direction": mapped_direction,
                        "steps": steps
                    }
                }
        
        return None