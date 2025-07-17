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
            self.stair_orientations[pos] = stair['orientation'] # stair.get('orientation', 'horizontal')
        # Initialize secret mask
        self.secret_mask = [[False] * self.width for _ in range(self.height)]
        # Corridor directions for initial placement
        self.stair_corridor_dirs = {}
        for stair in self.stairs:
            pos = (stair['row'], stair['col'])
            self.stair_corridor_dirs[pos] = (
                stair.get('corridor_dx', 0),
                stair.get('corridor_dy', 0)
            )

        # Initialize visibility system
        self.visibility_system = VisibilitySystemNeo(self.grid, self.party_position)

        # Import at runtime to break circular dependency
        from dungeon_neo.movement_service import MovementService

        # Initialize movement service
        self.movement = MovementService(self)


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
        # Update visibility when position changes
        self.visibility_system.party_position = value
        self.visibility_system.update_visibility()

    def get_door_orientation(self, row, col):
        """Override for corridor doors not connected to rooms"""
        cell = self.get_cell(row, col)
        
        # Check if door is between two corridors
        east = self.get_cell(row, col+1)
        west = self.get_cell(row, col-1)
        north = self.get_cell(row-1, col)
        south = self.get_cell(row+1, col)
        
        # Determine corridor direction
        if (east and east.is_corridor and 
            west and west.is_corridor and
            not (north and north.is_corridor) and
            not (south and south.is_corridor)):
            # Between east-west corridors → vertical door
            return 'vertical'
            
        if (north and north.is_corridor and 
            south and south.is_corridor and
            not (east and east.is_corridor) and
            not (west and west.is_corridor)):
            # Between north-south corridors → horizontal door
            return 'horizontal'
        
        # Default to generator's orientation
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
    
    def is_valid_position(self, pos):
        """Check if position is valid and passable"""
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

    
    def update_visibility_for_path(self, cells):
        """Mark cells along the path as discovered"""
        for (x, y) in cells:
            # Add to explored set
            self.visibility_system.explored.add((x, y))
            
            # Add to visible set for current position
            self.visibility_system.visible.add((x, y))
