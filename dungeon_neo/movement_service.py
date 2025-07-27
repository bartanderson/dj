from dungeon_neo.constants import DIRECTION_VECTORS_8

class MovementService:
    def __init__(self, state):
        self.state = state
        self.visibility = state.visibility_system if hasattr(state, 'visibility_system') else None
    
    def move(self, direction: str, steps: int = 1) -> dict:
        """Move party with proper validation and visibility updates"""
        # Get direction vector
        dx, dy = DIRECTION_VECTORS_8.get(direction.lower(), (0, 0))

        if dx == 0 and dy == 0:
            return {
                "success": False,
                "message": f"Invalid direction: {direction}",
                "new_position": self.state.party_position
            }
        
        # Get current position
        x, y = self.state.party_position
        actual_steps = 0
        messages = []
        
        # Update visibility along the path BEFORE moving
        self.visibility.update_visibility_directional(direction, steps)
        
        # Execute movement step-by-step
        for step in range(steps):
            new_y, new_x = y + dy, x + dx 
            
            # Check if position is valid
            if not self.state.grid_system.is_valid_position(new_x, new_y):
                messages.append(f"Cannot move to ({new_x}, {new_y}) - out of bounds")
                break
                
            # Get cell and check if it's passable
            cell = self.state.get_cell(new_x, new_y)
            if not cell:
                messages.append(f"Invalid cell at ({new_x}, {new_y})")
                break
                
            if not self.is_passable(new_x, new_y):
                cell_type = self.get_cell_type(new_x, new_y)
                messages.append(f"Blocked by {cell_type} at ({new_x}, {new_y})")
                break
                
            # Validate diagonal paths
            if direction in ['northeast', 'northwest', 'southeast', 'southwest']:
                # Check horizontal and vertical components
                if not (self.is_passable(x + dx, y) and self.is_passable(x, y + dy)):
                    messages.append(f"Diagonal path blocked to ({new_x}, {new_y})")
                    break
            
            # Move to next cell
            x, y = new_x, new_y
            actual_steps += 1
            messages.append(f"Moved {direction} to ({x}, {y})")
        
        # Update final position
        old_position = self.state.party_position
        self.state.party_position = (x, y) 
        
        # Update visibility system with new position
        if self.visibility:
            self.visibility.party_position = (x, y)
            self.visibility.update_visibility()
        
        # Return results
        return {
            "success": actual_steps > 0,
            "message": "\n".join(messages),
            "old_position": old_position,
            "new_position": (x, y),
            "steps_moved": actual_steps
        }
    
    def is_passable(self, x: int, y: int) -> bool:
        """Check if a cell is passable for movement"""
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
        """Get descriptive cell type"""
        if not self.state.grid_system.is_valid_position(x, y):
            return "boundary"
            
        cell = self.state.get_cell(x, y)
        if not cell:
            return "void"
            
        if cell.is_blocked: return "blocked"
        if cell.is_perimeter: return "perimeter"
        if cell.is_room: return "room"
        if cell.is_corridor: return "corridor"
        if cell.is_door: 
            if cell.is_arch: return "arch"
            if cell.is_portc: return "portcullis"
            return "door"
        if cell.is_stairs: return "stairs"
        if cell.is_secret: return "secret door"
        return "unknown"