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
        self.width = len(grid[0]) if grid else 0
        
        # Initialize visibility states: 
        # true_state stores the actual visibility status for each cell
        self.true_state = [
            ["unexplored" for _ in range(self.width)] 
            for _ in range(self.height)
        ]
        
        # Initialize the visibility
        self.update_visibility()

    @property
    def reveal_all(self):
        return self._reveal_all

    @reveal_all.setter
    def reveal_all(self, value):
        self._reveal_all = value
        self.update_visibility()
        
    def _init_true_state(self):
        for x, row in enumerate(self.grid):
            for y, _ in enumerate(row):
                self.true_state[(x, y)] = {
                    'explored': False,
                    'visible': False
                }
    
    def set_reveal_all(self, reveal: bool):
        self.reveal_all = reveal
        self.update_visibility()

    def update_visibility(self):
        """Update visibility using octant-based shadow casting"""
        # First, mark all currently visible cells as explored
        for y in range(self.height):
            for x in range(self.width):
                if self.true_state[y][x] == "visible":
                    self.true_state[y][x] = "explored"
        
        # Cast light from party position
        cx, cy = self.party_position
        max_distance = 5  # Configurable view distance
        
        # Mark current position as visible
        self.true_state[cy][cx] = "visible"
        
        # Cast light in all 8 octants
        for octant in range(8):
            self._cast_light(cx, cy, octant, 1, 1.0, 0.0, max_distance)

    def _cast_light(self, cx, cy, octant, row, start_slope, end_slope, max_distance):
        """Recursive shadow casting algorithm"""
        if row > max_distance:
            return
        
        # Determine search range for this row
        start_col = max(0, int(row * start_slope))
        end_col = min(row, int(row * end_slope)) + 1
        
        # Process cells in this row
        for col in range(start_col, end_col):
            # Transform octant coordinates to grid coordinates
            tx, ty = self._transform_octant(cx, cy, octant, col, row)
            
            # Skip if out of bounds
            if not (0 <= tx < self.width and 0 <= ty < self.height):
                continue
            
            # Mark cell as visible
            self.true_state[ty][tx] = "visible"
            
            # Block light if cell is opaque
            if self._is_blocking(tx, ty):
                # Calculate new slopes for recursion
                new_start_slope = (col - 0.5) / (row + 1) if col > 0 else start_slope
                new_end_slope = (col + 0.5) / (row + 1)
                
                # Recursively cast light with new slopes
                self._cast_light(cx, cy, octant, row+1, start_slope, new_start_slope, max_distance)
                start_slope = new_end_slope
                
                # Stop if slopes converge
                if start_slope >= end_slope:
                    return
            else:
                # Continue light through transparent cells
                if col == end_col - 1:
                    self._cast_light(cx, cy, octant, row+1, start_slope, end_slope, max_distance)
    
    def _transform_octant(self, cx, cy, octant, col, row):
        """Transform octant coordinates to grid coordinates"""
        # Each octant covers 45 degrees around the center point
        if octant == 0: return cx + col, cy - row
        if octant == 1: return cx + row, cy - col
        if octant == 2: return cx + row, cy + col
        if octant == 3: return cx + col, cy + row
        if octant == 4: return cx - col, cy + row
        if octant == 5: return cx - row, cy + col
        if octant == 6: return cx - row, cy - col
        if octant == 7: return cx - col, cy - row
    
    def _is_blocking(self, x, y):
        """Check if a cell blocks light (walls, closed doors, etc.)"""
        cell_value = self.grid[y][x]
        
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

    # NOTHING = CELL_FLAGS['NOTHING']
    # BLOCKED = CELL_FLAGS['BLOCKED']
    # ROOM = CELL_FLAGS['ROOM']
    # CORRIDOR = CELL_FLAGS['CORRIDOR']
    # PERIMETER = CELL_FLAGS['PERIMETER']
    # ENTRANCE = CELL_FLAGS['ENTRANCE']
    # ROOM_ID = CELL_FLAGS['ROOM_ID']
    # ARCH = CELL_FLAGS['ARCH']
    # DOOR = CELL_FLAGS['DOOR']
    # LOCKED = CELL_FLAGS['LOCKED']
    # TRAPPED = CELL_FLAGS['TRAPPED']
    # SECRET = CELL_FLAGS['SECRET']
    # PORTC = CELL_FLAGS['PORTC']
    # STAIR_DN = CELL_FLAGS['STAIR_DN']
    # STAIR_UP = CELL_FLAGS['STAIR_UP']
    # LABEL = CELL_FLAGS['LABEL']

    
    def get_visibility(self, position):
        """Get visibility status of a cell: 'visible', 'explored', or 'unexplored'"""
        x, y = position
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.true_state[y][x]
        return "unexplored"