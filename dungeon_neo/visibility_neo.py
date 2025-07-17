from dungeon_neo.constants import CELL_FLAGS, DIRECTION_VECTORS, OPPOSITE_DIRECTIONS
import math

DIRECTION_VECTORS_8 = {
'n': (-1, 0), 's': (1, 0), 'e': (0, 1), 'w': (0, -1),
'ne': (-1, 1), 'nw': (-1, -1), 'se': (1, 1), 'sw': (1, -1)}

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
        if not hasattr(self, 'party_position') or not self.party_position:
            return
        
        y0, x0 = self.party_position
        new_visible = set()
        
        # Always see current cell
        new_visible.add((x0, y0))
        
        # Check in 8 directions
        for dir, (dr, dc) in DIRECTION_VECTORS_8.items():
            x, y = x0, y0
            clear_path = True
            
            # Check up to 2 steps in each direction
            for distance in range(1, 3):
                x += dr
                y += dc
                
                # Stop at boundaries
                if not (0 <= x < self.height and 0 <= y < self.width):
                    break
                    
                # Add cell if path is clear
                if clear_path:
                    new_visible.add((x, y))
                    
                # Check if cell blocks vision
                if self._is_blocking(y, x):  # Note: grid uses [y][x] indexing
                    clear_path = False
        
        # Update visibility sets
        self.visible = new_visible
        self.explored |= new_visible

    def is_visible(self, x, y):
        return self.visible[y][x]
        
    def is_explored(self, x, y):
        """Check if cell is explored (no fog)"""
        return (x, y) in self.explored  # Check set membership

    def _is_blocking(self, x, y):
        cell = self.grid[y][x]
        # Comprehensive wall detection
        return (cell.is_blocked or 
                cell.is_perimeter or
                (cell.is_door and not (cell.is_arch)) or
                cell.base_type == self.NOTHING)
    
    def get_visibility(self, position):
        """Get visibility status of a cell"""
        x, y = position
        if self.visible[y][x]:
            return "visible"
        elif self.explored[y][x]:
            return "explored"
        else:
            return "unexplored"