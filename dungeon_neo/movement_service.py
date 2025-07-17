from dungeon_neo.cell_neo import DungeonCellNeo
from dungeon_neo.constants import DIRECTION_VECTORS, DIRECTION_VECTORS_8

class MovementService:
    def __init__(self, state):
        self.state = state
        self.visibility = state.visibility_system
    
    def move(self, direction: str, steps: int = 1) -> dict:
        """Centralized movement handling with discovery and 8-direction support"""
        if direction not in DIRECTION_VECTORS_8:
            return {"success": False, "message": "Invalid direction"}
        
        dx, dy = DIRECTION_VECTORS_8[direction]
        x, y = self.state.party_position
        actual_steps = 0
        messages = []
        discovered_cells = []
        
        for step in range(steps):
            new_x, new_y = x + dx, y + dy
            
            # Validate position
            if not self.is_passable(new_x, new_y):
                cell_type = self.get_cell_type(new_x, new_y)
                if cell_type in ['SECRET']:
                    cell_type = ['BLOCKED']
                messages.append(f"Blocked by {cell_type} at ({new_x}, {new_y})")
                break  
            
            # Update position
            x, y = new_x, new_y
            actual_steps += 1
            discovered_cells.append((new_x, new_y))
            messages.append(f"Moved {direction} to ({x}, {y})")
        
        # Update position and discovery
        self.state.party_position = (x, y)
        self.update_discovery(discovered_cells)
        
        # Format response
        response = {
            "success": actual_steps > 0,
            "message": "\n".join(messages) if messages else "No movement",
            "new_position": (x, y),
            "steps_moved": actual_steps,
            "direction": direction
        }
        return response
    
    def is_passable(self, x: int, y: int) -> bool:
        """Centralized passability check"""
        # Boundary check
        if not (0 <= x < self.state.height and 0 <= y < self.state.width):
            return False
            
        cell = self.state.get_cell(y, x)  # Note: grid uses [y][x] indexing
        if not cell:
            return False
            
        # Special cases
        if cell.is_stairs:
            return True
        if cell.is_door:
            return cell.is_arch
            
        # Default passability
        return not (cell.is_blocked or cell.is_perimeter)
    
    def get_cell_type(self, x: int, y: int) -> str:
        """Centralized cell type identification"""
        if not (0 <= x < self.state.height and 0 <= y < self.state.width):
            return "boundary"
            
        cell = self.state.get_cell(x, y)
        if not cell:
            return "void"
            
        if cell.is_blocked: return "wall"
        if cell.is_perimeter: return "perimeter"
        if cell.is_room: return "room"
        if cell.is_corridor: return "corridor"
        if cell.is_door: 
            if cell.is_arch: return "arch"
            if cell.is_portc: return "portcullis"
            return "door"
        if cell.is_stairs: return "stairs"
        return "unknown"
    
    def update_discovery(self, cells: list):
        """Centralized discovery update"""
        for (x, y) in cells:
            # Add to explored set
            self.visibility.explored.add((x, y))
            
            # Add to visible set
            self.visibility.visible.add((x, y))
        
        # Update visibility from final position
        self.visibility.party_position = self.state.party_position
        self.visibility.update_visibility()