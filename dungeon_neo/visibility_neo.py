from dungeon_neo.constants import CELL_FLAGS, DIRECTION_VECTORS, OPPOSITE_DIRECTIONS

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

    def __init__(self, grid, party_position):
        self.grid = grid
        self.party_position = party_position
        self.height = len(grid)
        self.width = len(grid[0])
        self.explored = set()  # Persistent exploration memory
        self.visible = set()   # Current visible cells
        self.update_visibility()

    @property
    def reveal_all(self):
        return self._reveal_all

    @reveal_all.setter
    def reveal_all(self, value):
        self._reveal_all = value
        self.update_visibility()
        
    
    def set_reveal_all(self, reveal: bool):
        self.reveal_all = reveal
        self.update_visibility()

    def update_visibility(self):
        """Reveal area around party with proper coordinate handling"""
        x, y = self.party_position
        print(f"Updating visibility at: ({y}, {x})")
        
        new_explored = set(self.explored)
        
        # Add 5x5 diamond area
        for d_y in range(-2, 3):
            for d_x in range(-2, 3):
                # Diamond shape
                if abs(d_y) + abs(d_x) > 3:
                    continue
                    
                new_y = y + d_y
                new_x = x + d_x
                
                if 0 <= new_y < self.height and 0 <= new_x < self.width:
                    new_explored.add((new_y, new_x))
                    print(f"  - Added position: ({new_y}, {new_x})")

        self.explored = new_explored
        
        print(f"Total explored positions: {len(self.explored)}")
        
    def is_visible_through(self, start_x, start_y, end_x, end_y):
        """Check if path is unobstructed (Bresenham's line algorithm)"""
        dx = abs(end_x - start_x)
        dy = abs(end_y - start_y)
        sx = 1 if start_x < end_x else -1
        sy = 1 if start_y < end_y else -1
        err = dx - dy
        
        x, y = start_x, start_y
        while x != end_x or y != end_y:
            # Stop if we hit a blocking cell before reaching target
            if (x, y) != (start_x, start_y) and self._is_blocking(x, y):
                return False
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
                
        return True

    def is_visible(self, x, y):
        return self.visible[y][x]
        
    def is_explored(self, x, y):
        """Check if cell is explored (no fog)"""
        return (x, y) in self.explored  # Check set membership

    def _is_blocking(self, x, y):
        """Check if a cell blocks light (walls, closed doors, etc.)"""
        cell = self.grid[y][x]
        cell_value = cell.base_type
        
        # Always blocking
        if cell_value & (self.BLOCKED | self.PERIMETER):
            return True
        
        # Door handling
        if cell_value & self.DOORSPACE:
            # Portcullis and Arch don't block vision
            if cell_value & (self.ARCH | self.PORTC):
                return False
            # All other doors block vision
            return True
        
        return False
    
    def get_visibility(self, position):
        """Get visibility status of a cell"""
        x, y = position
        if self.visible[y][x]:
            return "visible"
        elif self.explored[y][x]:
            return "explored"
        else:
            return "unexplored"