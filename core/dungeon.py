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
        #crap that was here, moved the better initial values back from generator_neo.py
        # 'width': 39,  # have to be odd
        # 'height': 39, # have to be odd
        # 'room_min': 5,
        # 'room_max': 15,
        # 'max_rooms': 30,
        # 'add_stairs': 2
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
        
        # Initialize visibility system
        self.visibility_system = VisibilitySystemNeo(
            self.state.grid, 
            self.state.party_position
        )
        self.visibility_system.update_visibility()
    
    def move_party(self, direction):
        """Move party in cardinal direction (north, south, east, west)"""
        # Use our direction constants
        dx, dy = DIRECTION_VECTORS.get(direction.lower(), (0, 0))
        x, y = self.state.party_position
        new_pos = (x + dx, y + dy)
        
        # Check if move is valid
        if not self.state.is_valid_position(new_pos):
            return False, "Cannot move there"
        
        # Update position in state
        self.state.party_position = new_pos
        
        # Update visibility system
        self.visibility_system.party_position = new_pos  # Update position
        self.visibility_system.update_visibility()       # Then update visibility
        
        return True, f"Moved {direction}"

    def _is_blocked(self, x, y):
        """Check if cell is blocked (wall or closed door)"""
        cell = self.state.get_cell(x, y)
        # things that cause vision to be blocked, see visibility_neo.py
        return cell_value & self.BLOCKED or cell_value & (self.PERIMETER | self.DOOR | self.LOCKED | self.TRAPPED | self.SECRET | self.STAIR_DN | self.STAIR_UP)

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