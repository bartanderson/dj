from typing import List, Dict, Any, Tuple, Optional, Union
from dungeon_neo.constants import CELL_FLAGS, DIRECTION_VECTORS
from dungeon_neo.cell_neo import DungeonCellNeo
from dungeon_neo.visibility_neo import VisibilitySystemNeo
from dungeon_neo.generator_neo import DungeonGeneratorNeo

class DungeonStateNeo:

    # NOTHING = CELL_FLAGS['NOTHING']
    # BLOCKED = CELL_FLAGS['BLOCKED']
    ROOM = CELL_FLAGS['ROOM']
    CORRIDOR = CELL_FLAGS['CORRIDOR']
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

    def __init__(self, generator: DungeonGeneratorNeo):
        self.generator = generator
        dungeon_data = generator.create_dungeon()
        self.grid = self._convert_grid(dungeon_data['grid'])
        self.rooms = dungeon_data['rooms']
        self.doors = dungeon_data['doors']
        self.stairs = dungeon_data['stairs']
        
        # Set dimensions based on actual grid size
        self._height = len(self.grid)
        self._width = len(self.grid[0]) if self._height > 0 else 0
        
        # Determine starting position
        self._party_position = self._determine_start_position()
        
        # Initialize visibility system
        self.visibility = VisibilitySystemNeo(self.grid, self._party_position)

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
        # Automatically update visibility when position changes
        if hasattr(self, 'visibility'):
            self.visibility.party_position = value
            self.visibility.update_visibility()
        
    def _convert_grid(self, generator_grid):
        grid = []
        for x, row in enumerate(generator_grid):
            new_row = []
            for y, cell_value in enumerate(row):
                new_row.append(DungeonCellNeo(cell_value, x, y))
            grid.append(new_row)
        return grid
        
    def _determine_start_position(self):
        # Find starting position (stairs or center)
        if self.stairs:
            stair = self.stairs[0]
            return (stair['row'], stair['col'])  # Use row/col instead of position
        return (self.height // 2, self.width // 2)

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