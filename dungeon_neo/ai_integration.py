# File: dungeon_neo/ai_integration.py
from .tool_system import ToolRegistry, tool
from ollama import Client
from .dm_tools import DMTools
import re
import json

class DungeonAI:
    def __init__(self, dungeon_state, ollama_host="http://localhost:11434"):
        self.state = dungeon_state
        self.ollama = Client(host=ollama_host)
        self.tool_registry = ToolRegistry()
        
        # Register tools from this class
        self.tool_registry.register_from_class(self)
        
        # Register tools from DMTools
        self.tools = DMTools(dungeon_state)
        self.tool_registry.register_from_class(self.tools)
        
        # Generate dynamic system prompt
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
    
    def _create_system_prompt(self) -> str:
        """Create prompt with dynamic tool descriptions"""
        tools_spec = self.tool_registry.get_tools_spec()
        tools_json = json.dumps(tools_spec, indent=2)
        
        return f"""
        You are a Dungeon Master assistant in a text-based dungeon game. 
        The player can give you commands to interact with the dungeon.
        
        You have access to these tools:
        {tools_json}
        
        Always respond with JSON containing:
        {{
            "thoughts": "<reasoning>",
            "tool": "<tool_name>",
            "arguments": {{ ... }}
        }}
        
        Important rules:
        1. Only use the tools provided
        2. Fill all required arguments
        3. Use simple, direct commands
        4. If a request requires multiple steps, break it into separate responses
        """

    @tool(
        name="inspect_cell",
        description="Get detailed information about a dungeon cell",
        x="X coordinate (number)",
        y="Y coordinate (number)"
    )
    def inspect_cell(self, x: int, y: int) -> dict:
        """Get detailed information about a cell"""
        cell = self.state.get_cell(x, y)
        if not cell:
            return {"success": False, "message": f"No cell at ({x}, {y})"}
        
        # Get readable cell type from DMTools
        cell_type = self.tools.get_cell_type(x, y)
        
        # Build detailed description
        description = f"Cell at ({x}, {y}):\n"
        description += f"- Type: {cell_type}\n"
        description += f"- Base flags: {hex(cell.base_type)}\n"
        description += f"- Is room: {cell.is_room}\n"
        description += f"- Is corridor: {cell.is_corridor}\n"
        description += f"- Is blocked: {cell.is_blocked}\n"
        description += f"- Is door: {cell.is_door}\n"
        description += f"- Is arch: {cell.is_arch}\n"
        description += f"- Is stairs: {cell.is_stairs}\n"
        description += f"- Is secret: {cell.is_secret}\n"
        description += f"- Description: {cell.description or 'None'}\n"
        description += f"- Entities: {len(cell.entities)}\n"
        description += f"- Overlays: {len(cell.overlays)}"
        
        return {
            "success": True,
            "message": description
        }
    
    @tool(
        name="get_current_position",
        description="Get the party's current position"
    )
    def get_current_position(self) -> dict:
        """Get party's current position"""
        x, y = self.state.party_position
        return {
            "success": True,
            "message": f"Party is at ({x}, {y})",
            "position": (x, y)
        }
        
    def process_command(self, natural_language: str) -> dict:
        # Generate response chunks
        response_chunks = self.ollama.generate(
            model="deepseek-r1:8b",
            system=self.system_prompt,
            prompt=natural_language,
            format="json",
            options={"temperature": 0.1},
            stream=True  # Enable streaming to get chunks
        )
        
        # Collect all response chunks
        full_response = ""
        for chunk in response_chunks:
            full_response += chunk.get("response", "")
        
        try:
            # Parse the full response
            response_json = json.loads(full_response)
            tool_name = response_json.get("tool")
            arguments = response_json.get("arguments", {})
            
            # Execute the selected tool
            result = self.tool_registry.execute_tool(tool_name, arguments)
            return result
        except json.JSONDecodeError:
            return {"success": False, "message": "AI returned invalid JSON"}
        except Exception as e:
            return {
                "success": False,
                "message": f"Tool execution error: {str(e)}",
                "ai_response": full_response  # Use the full_response variable
            }
