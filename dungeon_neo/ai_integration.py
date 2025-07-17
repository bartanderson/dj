# File: dungeon_neo/ai_integration.py
from ollama import Client
from dungeon_neo.dm_tools import DMTools
import re
import json

class DungeonAI:
    def __init__(self, dungeon_state, ollama_host="http://localhost:11434"):
        self.tools = DMTools(dungeon_state)
        self.ollama = Client(host=ollama_host)
        self.primitive_descriptions = self._get_primitive_descriptions()
        self.system_prompt = self._create_system_prompt()
        
    def _get_primitive_descriptions(self):
        """Get AI-readable primitive descriptions"""
        return {
            "circle": "A circular shape. Parameters: size (0.1-2.0), color (name or hex)",
            "square": "A square shape. Parameters: size (0.1-2.0), color, rotation (degrees)",
            "triangle": "A triangular shape. Parameters: size, color, direction (up/down/left/right)",
            "text": "Text overlay. Parameters: content (string), color, size (0.5-3.0)",
            "blood": "Blood stain effect. Parameters: size, intensity (1-5)",
            "glow": "Glowing aura. Parameters: color, intensity (1-10)"
        }
    
    def _create_system_prompt(self):
        """Create the system prompt for the AI"""
        return f"""
        You are a Dungeon Master assistant in a text-based dungeon game. 
        The player can give you commands to move or modify the dungeon.
        
        Always respond with JSON containing:
        {{
            "command": "<command_type>",
            "parameters": {{ ... }}
        }}
        
        Available commands:
        - MOVE_PARTY <direction> [steps]
          Directions: north, south, east, west
          Example: {{"command": "MOVE_PARTY", "parameters": {{"direction": "west", "steps": 3}}}}
          
        - ADD_ENTITY <x> <y> <entity_type>
          Entity types: npc, monster, item, trap, portal, chest, corpse, altar, fountain
          Example: {{"command": "ADD_ENTITY", "parameters": {{"x": 5, "y": 10, "entity_type": "chest"}}}}
          
        - ADD_OVERLAY <x> <y> <primitive>
          Primitives: circle, square, triangle, text, blood, glow
          Example: {{"command": "ADD_OVERLAY", "parameters": {{"x": 5, "y": 10, "primitive": "blood"}}}}
          
        - DESCRIBE <x> <y> <text>
          Example: {{"command": "DESCRIBE", "parameters": {{"x": 5, "y": 10, "text": "Bloody altar"}}}}
          
        Important rules:
        1. Always respond with valid JSON
        2. Only use the commands listed above
        3. For movement, use MOVE_PARTY
        4. Coordinates are numbers (x, y positions)
        5. Use simple, direct commands
        """

    def move_party(self, direction, steps=1):
        """Use centralized movement logic"""
        return self.tools.state.move_party(direction, steps)
    
    def process_command(self, natural_language):
        # First try to parse as direct movement command
        movement_command = self.parse_movement(natural_language)
        if movement_command:
            print(f"Handled as direct movement command: {movement_command}")
            return self.execute_ai_command(movement_command)
        
        # Otherwise use existing AI processing
        return self.process_with_ai(natural_language)
    
    def parse_movement(self, command):
        """Enhanced parser for 8-direction movement"""
        command = command.lower().strip()
        
        # Direction mapping including 8 directions
        direction_map = {
            'n': 'north', 'north': 'north', 'up': 'north',
            's': 'south', 'south': 'south', 'down': 'south',
            'e': 'east', 'east': 'east', 'right': 'east',
            'w': 'west', 'west': 'west', 'left': 'west',
            'ne': 'northeast', 'northeast': 'northeast', 'north-east': 'northeast',
            'nw': 'northwest', 'northwest': 'northwest', 'north-west': 'northwest',
            'se': 'southeast', 'southeast': 'southeast', 'south-east': 'southeast',
            'sw': 'southwest', 'southwest': 'southwest', 'south-west': 'southwest'
        }
        
        # Match movement patterns
        patterns = [
            r'^(?:move|go|walk|head)\s+(\w+)(?:\s+(\d+))?',  # "move northeast 3"
            r'^(\w+)(?:\s+(\d+))?$',                          # "northeast 3"
            r'^(\d+)\s+steps?\s+(\w+)$',                      # "3 steps northeast"
            r'^(\w+)\s+(\d+)$'                                # "northeast 3"
        ]
        
        for pattern in patterns:
            match = re.match(pattern, command)
            if match:
                # Extract direction and steps
                dir_str = match.group(1) if 'steps' not in pattern else match.group(2)
                steps_str = match.group(2) if 'steps' not in pattern else match.group(1)
                
                # Convert steps to number
                steps = int(steps_str) if steps_str and steps_str.isdigit() else 1
                
                # Map direction
                direction = direction_map.get(dir_str.lower())
                if direction:
                    return {
                        "command": "MOVE_PARTY",
                        "parameters": {"direction": direction, "steps": steps}
                    }
        
        return None

    
    def process_with_ai(self, natural_language):
        """Original AI processing logic (unchanged)"""
        response = self.ollama.generate(
            model="deepseek-r1:8b",
            system=self.system_prompt,
            prompt=natural_language,
            format="json",
            options={"temperature": 0.3}
        )
        
        try:
            # Extract response text
            response_text = ""
            if hasattr(response, "response"):
                response_text = response.response
            elif "text" in response:
                response_text = response["text"]
            else:
                return {"success": False, "message": "AI response format not recognized"}
            
            command_data = json.loads(response_text)
            return self.execute_ai_command(command_data)
        except json.JSONDecodeError:
            return {"success": False, "message": "AI returned invalid JSON"}
    
    def execute_ai_command(self, command_data):
        cmd = command_data.get("command", "").upper()
        params = command_data.get("parameters", {})
        
        try:
            if cmd == "MOVE_PARTY":
                # Use the DMTools move_party method
                return self.tools.move_party(
                    params["direction"], 
                    params.get("steps", 1)
                )
                
            elif cmd == "SET_PROPERTY":
                return self.tools.set_property(
                    params["x"], params["y"], 
                    params["property"], params["value"]
                )
                
            elif cmd == "ADD_ENTITY":
                return self.tools.add_entity(
                    params["x"], params["y"], 
                    params["entity_type"], **params.get("properties", {})
                )
                
            elif cmd == "ADD_OVERLAY":
                return self.tools.add_overlay(
                    params["x"], params["y"], 
                    params["primitive"], **params.get("parameters", {})
                )
                
            elif cmd == "DESCRIBE":
                return self.tools.describe_cell(
                    params["x"], params["y"], params["text"]
                )
                
            return {"success": False, "message": f"Unknown command: {cmd}"}
        except KeyError as e:
            return {"success": False, "message": f"Missing parameter: {str(e)}"}