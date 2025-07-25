from dungeon_neo.generator_neo import DungeonGeneratorNeo
from dungeon_neo.state_neo import DungeonStateNeo
from dungeon_neo.renderer_neo import DungeonRendererNeo
from dungeon_neo.visibility_neo import VisibilitySystemNeo
from dungeon_neo.constants import CELL_FLAGS, DIRECTION_VECTORS, OPPOSITE_DIRECTIONS
from dungeon_neo.movement_service import MovementService
from dungeon_neo.cell_neo import DungeonCellNeo

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
        
        # Set final party position FIRST
        self._set_initial_party_position()
        
        # THEN create visibility system with actual position
        self.state.visibility_system = VisibilitySystemNeo(
            self.state.grid_system, 
            self.state.party_position
        )
        
        # Update visibility immediately
        self.state.visibility_system.update_visibility()
        
        # Finally create movement service
        self.state.movement = MovementService(self.state)
        
        print(f"Generated dungeon: {self.state.width}x{self.state.height}")
        print(f"Initial party position: {self.state.party_position}")

    def _set_initial_party_position(self):
        """Set initial party position near first up stair"""
        # Find first up stair
        up_stairs = [stair for stair in self.state.stairs if stair.get('key') == 'up'] # find all the up stairs. You would come down them to be here.
        
        if not up_stairs:
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
            return
        else:
            stair = up_stairs[0]
            party_x = stair['y'] + stair['dy']
            party_y = stair['x'] + stair['dx']
            self.state.party_position = (party_x, party_y)
                    
    def is_blocked_for_movement(self, cell):
        """Simplified blocking logic"""
        # Block all BLOCKED cells
        if cell.is_blocked:
            return True
            
        # Block all perimeter cells that aren't doors
        if cell.is_perimeter and not cell.is_door:
            return True
            
        # Block non-arch doors
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
        print(f"move_party {new_pos}")
        
        # Check if move is valid
        if not self.state.is_valid_position(new_pos):
            return False, "Cannot move there", self.state.party_position
        
        # Check if path is blocked
        new_x, new_y = new_pos
        cell = self.state.get_cell(new_x, new_y)

        # Detailed cell debug
        # print(f"Cell at ({new_x},{new_y}):")
        # print(f"  Type: {type(cell)}")
        # print(f"  Base type: {hex(cell.base_type)}")
        # print(f"  is_blocked: {cell.is_blocked}")
        # print(f"  is_perimeter: {cell.is_perimeter}")
        # print(f"  is_door: {cell.is_door}")
        # print(f"  is_arch: {cell.is_arch}")
        # print(f"  is_room: {cell.is_room}")
        # print(f"  is_corridor: {cell.is_corridor}")

        # print(f"move_party before is_blocked_for_movement {cell}")
        if cell and self.is_blocked_for_movement(cell):
            return False, "Blocked by obstacle", self.state.party_position
        print(f"Movement not blocked. continuing")
        
        # Update position in state
        self.state.party_position = new_pos
        self.update_visibility()
        
        # Update visibility system
        self.visibility_system.party_position = new_pos
        self.visibility_system.update_visibility()
        
        print(f"Party moved to: {new_pos}")
        
        return True, f"Moved {direction}", new_pos

    def update_visibility(self):
        """Update visibility after position changes"""
        if self.state and self.state.visibility_system:
            self.state.visibility_system.party_position = self.state.party_position
            self.state.visibility_system.update_visibility()
    
    def get_image(self, debug=False):
        # Simply pass the state directly to the renderer
        return self.renderer.render(
            self.state, 
            debug_show_all=debug,
            visibility_system=self.state.visibility_system
        )
    
    def get_current_room_description(self): # maybe we can integrate AI later
        """Simple room description for UI"""
        x, y = self.state.party_position
        cell = self.state.get_cell(x, y)
        return f"You're in a {cell} room"