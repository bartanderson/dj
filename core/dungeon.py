from dungeon_neo.generator_neo import DungeonGeneratorNeo
from dungeon_neo.state_neo import DungeonStateNeo
from dungeon_neo.renderer_neo import DungeonRendererNeo
from dungeon_neo.visibility_neo import VisibilitySystemNeo
from dungeon_neo.constants import CELL_FLAGS, DIRECTION_VECTORS, OPPOSITE_DIRECTIONS

class DungeonSystem:
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
    
    DEFAULT_OPTIONS = {
            'seed': 'None',
            'n_rows': 39,
            'n_cols': 39,
            'dungeon_layout': 'None',
            'room_min': 3,
            'room_max': 9,
            'room_layout': 'Scattered',
            'corridor_layout': 'Bent',
            'remove_deadends': 50,
            'add_stairs': 2,
            'map_style': 'Standard',
            #'cell_size': 18, handled in renderer options
            'grid': 'Square'
        }
    
    def __init__(self, options=None):
        self.options = options or self.DEFAULT_OPTIONS
        self.generator = DungeonGeneratorNeo(self.options)
        self.renderer = DungeonRendererNeo()
        self.state = None  # Will be initialized after generation
        self.visibility_system = None  # Will be initialized after generation
    
    def generate(self):
        # Generate dungeon and get the result
        generator_result = self.generator.create_dungeon()
        
        # Create state from generator result
        self.state = DungeonStateNeo(generator_result)
        
        # Set initial party position
        self._set_initial_party_position()
        
        # Initialize visibility system
        self.visibility_system = VisibilitySystemNeo(
            self.state.grid, 
            self.state.party_position
        )
        print(f"Visibility system initialized at: {self.state.party_position}")

    def _set_initial_party_position(self):
        """Set initial party position near first up stair"""
        # Find first up stair
        up_stairs = [stair for stair in self.state.stairs if stair.get('key') == 'up']
        
        if up_stairs:
            stair = up_stairs[0]
            stair_x, stair_y = stair['row'], stair['col']
            orientation = stair.get('orientation', 'horizontal')
            
            # Try to place one step beyond the stair
            if orientation == 'horizontal':
                candidate_pos = (stair_x, stair_y + 1) # need to check which way to place
            else:
                candidate_pos = (stair_x + 1, stair_y) # ditto
            
            # Use candidate position if valid, otherwise use stair position
            if self.state.is_valid_position(candidate_pos):
                self.state.party_position = candidate_pos
            else:
                self.state.party_position = (stair_x, stair_y)
            return
        
        # Fallback to first room center
        if self.state.rooms:
            room = self.state.rooms[0]
            center_x = (room['north'] + room['south']) // 2
            center_y = (room['west'] + room['east']) // 2
            self.state.party_position = (center_x, center_y)
            return
        
        # Final fallback to dungeon center
        center_x = self.state.height // 2
        center_y = self.state.width // 2
        self.state.party_position = (center_x, center_y)
    
    def is_blocked_for_movement(self, cell):
        """Check if cell blocks movement"""
        print(f"is_blocked_for_movement {cell}")
        # Always blocking
        if cell.base_type == self.NOTHING:
            return True
        if cell.is_blocked or cell.is_perimeter:
            return True
        # Door handling - Block all doors except arches
        if cell.is_door and not cell.is_arch:
            return True
        
        return False
    
    def move_party(self, direction):
        """Move party with proper movement restrictions"""
        # Use our direction constants
        dx, dy = DIRECTION_VECTORS.get(direction.lower(), (0, 0))
        x, y = self.state.party_position
        
        # Calculate new position
        new_pos = (x + dx, y + dy)
        
        # Check if move is valid
        if not self.state.is_valid_position(new_pos):
            return False, "Cannot move there", self.state.party_position
        
        # Check if path is blocked
        new_x, new_y = new_pos
        cell = self.state.get_cell(new_x, new_y)

        # Detailed cell debug
        print(f"Cell at ({new_x},{new_y}):")
        print(f"  Type: {type(cell)}")
        print(f"  Base type: {hex(cell.base_type)}")
        print(f"  is_blocked: {cell.is_blocked}")
        print(f"  is_perimeter: {cell.is_perimeter}")
        print(f"  is_door: {cell.is_door}")
        print(f"  is_arch: {cell.is_arch}")
        print(f"  is_room: {cell.is_room}")
        print(f"  is_corridor: {cell.is_corridor}")

        print(f"move_party before is_blocked_for_movement {cell}")
        if cell and self.is_blocked_for_movement(cell):
            return False, "Blocked by obstacle", self.state.party_position
        print(f"Movement not blocked. continuing")
        
        # Update position in state
        self.state.party_position = new_pos
        
        # Update visibility system
        self.visibility_system.party_position = new_pos
        self.visibility_system.update_visibility()
        
        # DEBUG: Print explored grid
        print(f"Party moved to: {new_pos}")
        cx, cy = new_pos
        print("Explored area:")
        cx, cy = new_pos
        # print(f"Visibility grid at ({cx},{cy}):")
        # grid = ""
        # for dy in range(-3, 4):
        #     for dx in range(-3, 4):
        #         x, y = cx + dx, cy + dy
        #         if 0 <= x < self.state.width and 0 <= y < self.state.height:
        #             explored = "X" if self.visibility_system.is_explored(x, y) else "."
        #             grid += explored
        #         else:
        #             grid += " "
        #     grid += "\n"
        # print(grid)
        
        return True, f"Moved {direction}", new_pos

    def _is_blocked(self, x, y):
        """Check if cell is blocked (wall or closed door)"""
        cell = self.state.get_cell(x, y)
        
        # Always blocking
        if cell.base_type & (self.BLOCKED | self.PERIMETER):
            return True
        
        # Door handling
        if cell.base_type & self.DOORSPACE:
            # Portcullis isn't blocked
            if cell.base_type & (self.ARCH | self.PORTC):
                return False
            # All other doors are blocked
            return True
        
        return False

    def update_visibility(self):
        """Update visibility based on party position"""
        self.visibility_system.party_position = self.state.party_position
        self.visibility_system.update_visibility()
    
    def get_image(self, debug=False):
        # Simply pass the state directly to the renderer
        return self.renderer.render(
            self.state, 
            debug_show_all=debug,
            visibility_system=self.visibility_system
        )
    
    def get_current_room_description(self): # maybe we can integrate AI later
        """Simple room description for UI"""
        x, y = self.state.party_position
        cell = self.state.get_cell(x, y)
        return f"You're in a {cell} room"