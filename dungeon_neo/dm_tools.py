from .tool_system import tool
import random

class DMTools:
    def __init__(self, state):
        self.state = state

    @tool(
        name="move_party",
        description="Move the player party in a direction",
        direction="Direction to move (north, south, east, west, northeast, etc.)",
        steps="Number of steps (default=1)"
    )
    def move_party(self, direction: str, steps: int = 1) -> dict:
        """Move party with proper validation"""
        return self.state.movement.move(direction, steps)
    
    def set_property(self, x, y, prop, value):
        cell = self.state.get_cell(x, y)
        if cell: cell.properties[prop] = value

    @tool(
        name="add_entity",
        description="Add an entity to a dungeon cell",
        x="X coordinate (number)",
        y="Y coordinate (number)",
        entity_type="Type of entity (npc, monster, item, trap, portal, chest, etc.)"
    )
    def add_entity(self, x: int, y: int, entity_type: str) -> dict:
        """Add entity to specified cell"""
        cell = self.state.get_cell(x, y)
        if not cell:
            return {"success": False, "message": "Invalid coordinates"}
        
        cell.entities.append(Entity(entity_type))
        return {"success": True, "message": f"Added {entity_type} at ({x}, {y})"}
    
    @tool(
        name="describe_cell",
        description="Add a text description to a dungeon cell",
        x="X coordinate (number)",
        y="Y coordinate (number)",
        text="Description text"
    )
    def describe_cell(self, x: int, y: int, text: str) -> dict:
        """Add description to cell"""
        cell = self.state.get_cell(x, y)
        if not cell:
            return {"success": False, "message": "Invalid coordinates"}
        
        cell.description = text
        return {"success": True, "message": f"Added description to ({x}, {y})"}

    def add_overlay(self, x, y, primitive, **params):
        cell = self.state.get_cell(x, y)
        if not cell:
            return {"success": False, "message": "Invalid coordinates"}
        
        # Handle special primitive types
        if primitive == "blood":
            return self._add_blood_overlay(cell, params)
        elif primitive == "glow":
            return self._add_glow_overlay(cell, params)
        
        # Default primitive handling
        cell.overlays.append(Overlay(primitive, **params))
        return {"success": True, "message": f"Added {primitive} overlay"}
    
    @tool(
        name="add_blood_effect",
        description="Add a blood stain effect to a cell",
        x="X coordinate (number)",
        y="Y coordinate (number)",
        size="Size of the effect (0.1-2.0)",
        intensity="Intensity of the effect (1-5)"
    )
    def add_blood_effect(self, x: int, y: int, size: float = 1.0, intensity: int = 3) -> dict:
        """Add blood effect to cell"""
        return self.add_overlay(x, y, "blood", size=size, intensity=intensity)
    
    @tool(
        name="add_glow_effect",
        description="Add a glowing aura effect to a cell",
        x="X coordinate (number)",
        y="Y coordinate (number)",
        color="Color name or hex value",
        intensity="Intensity of the glow (1-10)"
    )
    def add_glow_effect(self, x: int, y: int, color: str = "yellow", intensity: int = 5) -> dict:
        """Add glow effect to cell"""
        return self.add_overlay(x, y, "glow", color=color, intensity=intensity)
        
        return {"success": True, "message": "Added glow effect"}

    @tool(
        name="get_debug_grid",
        description="Get a text-based debug view of the dungeon"
    )
    def get_debug_grid(self) -> dict:
        """Get debug grid view"""
        grid = self.state.get_debug_grid()
        grid_str = "\n".join(grid)
        return {
            "success": True,
            "message": f"Debug Grid:\n{grid_str}",
            "grid": grid
        }
    
    @tool(
        name="reveal_secret",
        description="Reveal a secret door or passage",
        x="X coordinate (number)",
        y="Y coordinate (number)"
    )
    def reveal_secret(self, x: int, y: int) -> dict:
        """Reveal a secret at specified position"""
        success = self.state.reveal_secret(x, y)
        if success:
            return {"success": True, "message": f"Revealed secret at ({x}, {y})"}
        return {"success": False, "message": f"No secret found at ({x}, {y})"}
    
    @tool(
        name="reset_dungeon",
        description="Generate a new dungeon"
    )
    def reset_dungeon(self) -> dict:
        """Reset the dungeon"""
        self.state.dungeon.generate()
        return {"success": True, "message": "Generated new dungeon"}
    
    # Helper method
    def get_cell_type(self, x: int, y: int) -> str:
        """Get readable cell type name"""
        cell = self.state.get_cell(x, y)
        if not cell:
            return "None"
        
        if cell.is_room: return "Room"
        if cell.is_corridor: return "Corridor"
        if cell.is_blocked: return "Blocked"
        if cell.is_perimeter: return "Perimeter"
        if cell.is_door:
            if cell.is_arch: return "Archway"
            if cell.is_locked: return "Locked Door"
            if cell.is_trapped: return "Trapped Door"
            if cell.is_secret: return "Secret Door"
            if cell.is_portc: return "Portcullis"
            return "Door"
        if cell.is_stairs:
            if cell.is_stair_up: return "Stairs Up"
            if cell.is_stair_down: return "Stairs Down"
            return "Stairs"
        return "Unknown"


