from dungeon_neo.constants import DIRECTION_VECTORS_8

class MovementService:
    def __init__(self, state):
        self.state = state
        self.visibility = state.visibility_system
    
    def move(self, direction: str, steps: int = 1) -> dict:
        dx, dy = DIRECTION_VECTORS_8[direction]
        x, y = self.state.party_position
        actual_steps = 0
        messages = []
        path_cells = []
        
        for step in range(steps):
            new_x, new_y = x + dx, y + dy
            
            # Validate next cell
            if not self.is_passable(new_x, new_y):
                cell_type = self.get_cell_type(new_x, new_y)
                messages.append(f"Blocked by {cell_type} at ({new_x}, {new_y})")
                break
                
            # Validate diagonal paths
            if direction in ['northeast', 'northwest', 'southeast', 'southwest']:
                if not (self.is_passable(x + dx, y) and self.is_passable(x, y + dy)):
                    messages.append(f"Diagonal path blocked to ({new_x}, {new_y})")
                    break
            
            # Move to next cell
            x, y = new_x, new_y
            actual_steps += 1
            path_cells.append((x, y))
            messages.append(f"Moved {direction} to ({x}, {y})")
        
        # Update state and discovery
        self.state.party_position = (x, y)
        self.update_discovery(path_cells)
        
        return {
            "success": actual_steps > 0,
            "message": "\n".join(messages),
            "new_position": (x, y),
            "steps_moved": actual_steps
        }

    def update_discovery(self, cells: list):
        """Centralized discovery update"""
        # Mark cells as explored
        for (x, y) in cells:
            self.state.visibility_system.mark_explored(x, y)
            
        # Add to visible set for current position
        self.state.visibility_system.update_visibility()
        
    def is_passable(self, x: int, y: int) -> bool:
        if not self.state.grid_system.is_valid_position(x, y):
            return False
            
        cell = self.state.get_cell(x, y)
        if not cell:
            return False
            
        # Special cases
        if cell.is_stairs:
            return True
        if cell.is_secret and not self.state.secret_mask[y][x]:
            return False
        if cell.is_door:
            return cell.is_arch
            
        # Default passability
        return not (cell.is_blocked or cell.is_perimeter)
    
    def get_cell_type(self, x: int, y: int) -> str:
        if not self.state.grid_system.is_valid_position(x, y):
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