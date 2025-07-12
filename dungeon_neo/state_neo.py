from typing import List, Dict, Any, Tuple, Optional, Union
from dungeon_neo.constants import CELL_FLAGS, DIRECTION_VECTORS
from dungeon_neo.cell_neo import DungeonCellNeo
from dungeon_neo.visibility_neo import VisibilitySystemNeo
from dungeon_neo.generator_neo import DungeonGeneratorNeo

class DungeonStateNeo:

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

    def __init__(self, generator_result):
        self.n_cols = generator_result['n_cols']
        self.n_rows = generator_result['n_rows']
        # Convert grid with strict dimension enforcement
        self.grid = self._convert_grid(
            generator_result['grid'], 
            self.n_rows, 
            self.n_cols
        )

        self.stairs = generator_result['stairs']
        self.doors = generator_result.get('doors', [])
        self.rooms = generator_result.get('rooms', [])

        
        # Set dimensions based on actual grid size
        self._height = len(self.grid)
        self._width = len(self.grid[0]) if self.grid else 0
        
        # Initialize party position to (0, 0) as placeholder
        self._party_position = (0, 0)

        # Create orientation lookup dictionaries
        self.door_orientations = {}
        for door in self.doors:
            pos = (door['row'], door['col'])
            self.door_orientations[pos] = door['orientation']

        self.stair_orientations = {}
        for stair in self.stairs:
            pos = (stair['row'], stair['col'])
            self.stair_orientations[pos] = stair['orientation'] # stair.get('orientation', 'horizontal') # mimic door for this just in case, change back if it breaks I guess

        # Initialize secret mask
        self.secret_mask = [[False] * self.width for _ in range(self.height)]

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def party_position(self):
        return self._party_position

    @party_position.setter
    def party_position(self, value):
        self._party_position = value

    def get_door_orientation(self, row, col):
        return self.door_orientations.get((row, col), 'horizontal')

    def get_stair_orientation(self, row, col):
        return self.stair_orientations.get((row, col), 'horizontal')

        
    def _convert_grid(self, generator_grid, num_rows, num_cols):
        """Convert grid to DungeonCellNeo objects with comprehensive validation"""
        grid = []
        for x in range(num_rows + 1):
            row = []
            for y in range(num_cols + 1):
                # Get value with fallback
                try:
                    value = generator_grid[x][y]
                except (IndexError, TypeError):
                    value = CELL_FLAGS['NOTHING']
                
                # Create cell with validated value
                cell = DungeonCellNeo(value, x, y)
                
                # Log conversion if needed
                if not isinstance(value, int):
                    print(f"Converted cell ({x},{y}) from {type(value)} to int: {cell.base_type}")
                
                row.append(cell)
            grid.append(row)
        return grid


    def get_valid_moves(self, position=None):
        """Get list of valid move directions from current position"""
        if position is None:
            position = self.party_position
            
        valid_directions = []
        for direction, (dx, dy) in DIRECTION_VECTORS.items():
            new_pos = (position[0] + dx, position[1] + dy)
            
            # Check bounds
            if not (0 <= new_pos[0] < self.height and 
                    0 <= new_pos[1] < self.width):
                continue
                
            # Check passability
            cell = self.grid[new_pos[0]][new_pos[1]]
            if not cell.is_blocked:
                valid_directions.append(direction)
                
        return valid_directions
            
    def move_party(self, direction: str) -> Tuple[bool, str]:
        if direction not in DIRECTION_VECTORS:
            return False, f"Invalid direction: {direction}"
            
        dx, dy = DIRECTION_VECTORS[direction]
        x, y = self.party_position
        new_pos = (x + dx, y + dy)
        
        # Validate new position
        if not self.is_valid_position(new_pos):
            return False, "Invalid position"
            
        # Check if the new position is passable
        new_x, new_y = new_pos
        if not (0 <= new_x < self.height and 0 <= new_y < self.width):
            return False, "Out of bounds"
            
        new_cell = self.grid[new_x][new_y]
        if new_cell.is_blocked:
            return False, "Blocked by obstacle"
        
        # Update position
        self.party_position = new_pos
        return True, f"Moved {direction}"
    
    def is_valid_position(self, pos):
        x, y = pos
        if x < 0 or x >= self.height or y < 0 or y >= self.width:
            return False
        cell = self.get_cell(x, y)
        return cell and not cell.is_blocked

    
    def get_cell(self, x: int, y: int):
        if 0 <= x < self.height and 0 <= y < self.width:
            return self.grid[x][y]
        return None

    def reveal_secret(self, x, y):
        """Mark a secret door as discovered"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.secret_mask[y][x] = True
            return True
        return False