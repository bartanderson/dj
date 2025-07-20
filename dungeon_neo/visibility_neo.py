from dungeon_neo.constants import CELL_FLAGS, DIRECTION_VECTORS_8
import math

class VisibilitySystemNeo:
    NOTHING = CELL_FLAGS['NOTHING']
    BLOCKED = CELL_FLAGS['BLOCKED']
    ROOM = CELL_FLAGS['ROOM']
    CORRIDOR = CELL_FLAGS['CORRIDOR']
    PERIMETER = CELL_FLAGS['PERIMETER']
    ENTRANCE = CELL_FLAGS['ENTRANCE']
    ROOM_ID = CELL_FLAGS['ROOM_ID']
    ARCH = CELL_FLAGS['ARCH']
    DOOR = CELL_FLAGS['DOOR']
    LOCKED = CELL_FLAGS['LOCKED']
    TRAPPED = CELL_FLAGS['TRAPPED']
    SECRET = CELL_FLAGS['SECRET']
    PORTC = CELL_FLAGS['PORTC']
    STAIR_DN = CELL_FLAGS['STAIR_DN']
    STAIR_UP = CELL_FLAGS['STAIR_UP']
    LABEL = CELL_FLAGS['LABEL']

    # Composite flags
    DOORSPACE = CELL_FLAGS['DOORSPACE']
    ESPACE = CELL_FLAGS['ESPACE']
    STAIRS = CELL_FLAGS['STAIRS']
    BLOCK_ROOM = CELL_FLAGS['BLOCK_ROOM']
    BLOCK_CORR = CELL_FLAGS['BLOCK_CORR']
    BLOCK_DOOR = CELL_FLAGS['BLOCK_DOOR']

    def __init__(self, grid_system, party_position):
        self.grid_system = grid_system
        self.party_position = party_position
        self.explored = set()  # Cells that have been seen
        self.visible = set()   # Cells currently visible
        self.update_visibility()
    
    def mark_explored(self, x: int, y: int):
        """Mark a cell as explored (persistent memory)"""
        if self.grid_system.is_valid_position(x, y):
            self.explored.add((x, y))
    
    def update_visibility(self):
        if not self.party_position:
            return
        
        x0, y0 = self.party_position
        new_visible = set()
        new_visible.add((x0, y0))  # Always visible
        
        # Diamond-shaped visibility (Manhattan distance <= 2)
        for dx in range(-2, 2):
            for dy in range(-2, 2):
                if abs(dx) + abs(dy) > 4:  # Skip corners
                    continue
                    
                x, y = x0 + dx, y0 + dy
                if not self.grid_system.is_valid_position(x, y):
                    continue
                
                # Line-of-sight check
                visible = True
                line = self._get_line(x0, y0, x, y)
                for i in range(1, len(line)):
                    cx, cy = line[i]
                    if (cx, cy) == (x, y):
                        break
                    if self._is_blocking(cx, cy):
                        visible = False
                        break
                        
                if visible:
                    new_visible.add((x, y))
        
        self.visible = new_visible
        self.explored |= new_visible

    def _get_line(self, x0, y0, x1, y1):
        """Bresenham's line algorithm"""
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            points.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        
        return points
    
    def _is_blocking(self, x: int, y: int) -> bool:
        cell = self.grid_system.get_cell(x, y)
        if not cell:
            return True
            
        return (cell.is_blocked or 
                cell.is_perimeter or
                (cell.is_door and not cell.is_arch) or
                cell.base_type == CELL_FLAGS['NOTHING'])
    
    def is_visible(self, x: int, y: int) -> bool:
        """Check if cell is currently visible"""
        return (x, y) in self.visible
        
    def is_explored(self, x: int, y: int) -> bool:
        """Check if cell has been explored (seen before)"""
        return (x, y) in self.explored