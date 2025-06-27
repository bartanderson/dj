#dungeon\state.py
from dungeon.generator import DungeonGenerator
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw
import math

class DungeonCell:
    def __init__(self, base_type, x, y):
        self.base_type = base_type  # Original generated type
        self.current_type = base_type  # Current visible type
        self.x = x  # Store row position
        self.y = y  # Store column position
        self.features = []  # List of features (water, rubble, etc.)
        self.objects = []  # Interactive objects
        self.npcs = []  # NPCs present in this cell
        self.items = []  # Items in this cell
        self.visibility = {
            'explored': False,
            'visible': False,
            'light_source': False
        }
        self.search_difficulty = 10  # DC for finding hidden items
        self.searched = False
        self.metadata = {}  # Custom DM data

    @property
    def position(self):
        """Return position as tuple (x, y)"""
        return (self.x, self.y)

    def add_npc(self, npc_id):
        if npc_id not in self.npcs:
            self.npcs.append(npc_id)
    
    def remove_npc(self, npc_id):
        if npc_id in self.npcs:
            self.npcs.remove(npc_id)

    def add_item(self, item_id):
        if item_id not in self.items:
            self.items.append(item_id)
    
    def remove_item(self, item_id):
        if item_id in self.items:
            self.items.remove(item_id)

    def transform(self, new_type):
        """Permanently change cell type"""
        self.current_type = new_type
        
    def add_feature(self, feature_type, data=None):
        """Add environmental feature"""
        self.features.append({
            'type': feature_type,
            'data': data or {}
        })
        
    def reveal_secret(self):
        """Reveal hidden elements"""
        if self.base_type == DungeonGenerator.SECRET:
            self.current_type = DungeonGenerator.DOOR
        # Add other secret revelation logic
        
    def break_door(self):
        """Convert door to archway"""
        if self.current_type in [DungeonGenerator.DOOR, DungeonGenerator.LOCKED]:
            self.current_type = DungeonGenerator.ARCH

    def add_puzzle(self, puzzle_id: str, description: str, success_effect: str, hints: List[str] = None):
        """Add a puzzle to this cell with hints"""
        puzzle_obj = {
            'type': 'puzzle',
            'puzzle_id': puzzle_id,
            'description': description,
            'success_effect': success_effect,
            'hints': []
        }
        
        # Add hints with default level
        if hints:
            for i, hint_text in enumerate(hints):
                puzzle_obj['hints'].append({
                    'text': hint_text,
                    'level': i  # Default level based on order
                })
                
        self.objects.append(puzzle_obj)

    def get_puzzle_hints(self, puzzle_id: str) -> List[Dict[str, Any]]:
        """Get hints for a specific puzzle"""
        for obj in self.objects:
            if obj.get('type') == 'puzzle' and obj.get('puzzle_id') == puzzle_id:
                return obj.get('hints', [])
        return []

class VisibilitySystem:
    def __init__(self, dungeon, party_position):
        self.dungeon = dungeon
        self.party_position = party_position
        self.light_sources = [party_position]
        self.fog_enabled = True  # Default to fog of war

        # Dual-layer state storage
        self.true_state = {}  # Immutable exploration progress
        self.view_state = {}  # Temporary view overrides

    def set_view_at(self, position, explored, visible):
        """Set temporary view at specific position"""
        self.view_state[position] = {
            'explored': explored,
            'visible': visible
        }

    def init_true_state(self):
        """Initialize true exploration state (call after dungeon generation)"""
        for x, row in enumerate(self.dungeon):
            for y, cell in enumerate(row):
                self.true_state[(x, y)] = {
                    'explored': False,
                    'visible': False
                }
    
    def update_true_visibility(self):
        """Update true visibility based on party position (gameplay only)"""
        # Only update if fog is enabled
        if not self.fog_enabled:
            return
            
        for x, row in enumerate(self.dungeon):
            for y, cell in enumerate(row):
                pos = (x, y)
                
                # Preserve exploration state
                was_explored = self.true_state[pos]['explored']
                
                # Update visibility
                visible = self.has_line_of_sight(self.party_position, pos)
                self.true_state[pos] = {
                    'explored': was_explored or visible,
                    'visible': visible
                }
    
    def set_view(self, explored=True, visible=True):
        """Set temporary view state (doesn't alter true state)"""
        for pos in self.true_state:
            self.view_state[pos] = {
                'explored': explored,
                'visible': visible
            }
    
    def clear_view(self):
        """Clear temporary view overrides"""
        self.view_state = {}
    
    def get_visibility(self, pos):
        """Get effective visibility (view state overrides true state)"""
        if pos in self.view_state:
            return self.view_state[pos]
        return self.true_state.get(pos, {'explored': False, 'visible': False})      

    def set_global_visibility(self, explored=True, visible=True):
        """Set visibility for all cells"""
        for row in self.dungeon:
            for cell in row:
                cell.visibility['explored'] = explored
                cell.visibility['visible'] = visible
                
    def toggle_fog(self):
        """Toggle fog of war"""
        self.fog_enabled = not self.fog_enabled
        return self.fog_enabled

    def get_visible_cells(self):
        """Return list of currently visible positions"""
        visible = []
        for x in range(len(self.dungeon)):
            for y in range(len(self.dungeon[0])):
                if self.dungeon[x][y].visibility['visible']:
                    visible.append((x, y))
        return visible
        
    def update_visibility(self):
        """Update visibility for all cells"""
        for x in range(len(self.dungeon)):
            for y in range(len(self.dungeon[0])):
                cell = self.dungeon[x][y]
                
                # Reset visibility
                cell.visibility['visible'] = False
                
                # Check light sources
                for source in self.light_sources:
                    if self.has_line_of_sight(source, (x, y)):
                        cell.visibility['visible'] = True
                        cell.visibility['explored'] = True
                        
    def has_line_of_sight(self, from_pos, to_pos):
        x0, y0 = from_pos
        x1, y1 = to_pos
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while x0 != x1 or y0 != y1:
            cell = self.dungeon[x0][y0]
            
            # Secret cells block vision until discovered
            if (cell.base_type == DungeonGenerator.SECRET and 
                not cell.metadata.get('discovered', False)):
                return False
                
            # Blocked cells block vision
            if cell.base_type & DungeonGenerator.BLOCKED:
                return False
                
            # Update position
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
                
        return True
        
    def add_light_source(self, position):
        self.light_sources.append(position)
        
    def remove_light_source(self, position):
        if position in self.light_sources:
            self.light_sources.remove(position)
            

class DungeonState:
    def __init__(self, generator: DungeonGenerator):
        self.grid = self._convert_generator_output(generator)
        self.rooms = generator.room
        self.doors = generator.doorList
        # Convert stairs to use position tuples
        self.stairs = [{
            'position': (stair['row'], stair['col']),
            'next_position': (stair['next_row'], stair['next_col']),
            'key': stair['key']
        } for stair in generator.stairs]
        
        # Initialize start position
        start_position = self.determine_start_position()
        
        # Set visibility and party position
        self.visibility = VisibilitySystem(self.grid, start_position)
        self.party_position = start_position

    def determine_start_position(self):
        """Find the best starting position based on stairs"""
        # Find first down stair in our new stair format
        start_position = None
        for stair in self.stairs:
            if stair['key'] == 'down':
                start_position = stair['position']
                break
        
        # If no down stairs, use first stairs
        if not start_position and self.stairs:
            start_position = self.stairs[0]['position']
        
        # Default to center if no stairs
        if not start_position:
            return (len(self.grid)//2, len(self.grid[0])//2)
        
        # Position just beyond stairs if possible
        for stair in self.stairs:  # Use self.stairs here!
            if stair['position'] == start_position:
                # Use next_position from our new stair structure
                next_pos = stair['next_position']
                if self.is_valid_position(next_pos):
                    return next_pos
                break
        
        return start_position

    def is_valid_position(self, position: Tuple[int, int]) -> bool:
        """Check if position is within grid bounds"""
        x, y = position
        return (0 <= x < len(self.grid)) and (0 <= y < len(self.grid[0]))


    def search_cell(self, position, search_skill=0):
        """Search a cell with chance-based discovery"""
        if not self.is_valid_position(position):
            return False, "Invalid position", []
        
        cell = self.grid[position[0]][position[1]]
        
        # Can only search once per cell
        if cell.searched:
            return False, "Already searched this area", []
        
        cell.searched = True
        found_items = []
        
        # Base chance to find obvious items
        for item_id in cell.items:
            found_items.append(item_id)
        
        # Chance to find hidden items
        if random.randint(1, 20) + search_skill >= cell.search_difficulty:
            # Add hidden items if any
            pass
        
        # Clear found items from cell
        for item_id in found_items:
            cell.remove_item(item_id)
        
        # Generate discovery message
        if found_items:
            items_desc = ", ".join([self.game_state.items[item_id]['name'] for item_id in found_items])
            return True, f"You found: {items_desc}", found_items
        return True, "You find nothing of interest", []

    def move_party(self, direction: str) -> Tuple[bool, str]:
        """Move party in specified direction with validation"""
        if not hasattr(self, 'party_position'):
            # Initialize party position at first stair
            if self.stairs:
                self.party_position = self.stairs[0]['position']
                self.visibility.party_position = self.party_position
                self.visibility.update_true_visibility()
                return True, "Party positioned at entrance"
            return False, "No starting position available"
        
        x, y = self.party_position
        new_position = None
        
        if direction == 'north': new_position = (x-1, y)
        elif direction == 'south': new_position = (x+1, y)
        elif direction == 'west': new_position = (x, y-1)
        elif direction == 'east': new_position = (x, y+1)
        
        if not new_position:
            return False, "Invalid direction"
        
        # Validate movement
        if not self.is_valid_position(new_position):
            return False, "Cannot move outside dungeon"
        
        cell = self.grid[new_position[0]][new_position[1]]
        if cell.current_type & (self.BLOCKED | self.PERIMETER):
            return False, "Path blocked"
        
        # Handle doors
        if cell.current_type & self.DOORSPACE:
            door_type = self.get_door_type(cell.current_type)
            if door_type in ['locked', 'secret']:
                return False, f"{door_type.capitalize()} door blocks your path"
        
        # Update position
        self.party_position = new_position
        self.visibility.party_position = new_position
        self.visibility.update_true_visibility()
        
        # Mark as explored
        cell.visibility['explored'] = True
        
        return True, f"Moved {direction} to {self.get_room_description(new_position)}"

    def get_door_type(self, cell_value):
        if cell_value & self.LOCKED: return 'locked'
        if cell_value & self.SECRET: return 'secret'
        if cell_value & self.TRAPPED: return 'trapped'
        if cell_value & self.ARCH: return 'arch'
        return 'door'
        
    def _convert_generator_output(self, generator):
        """Convert generator output to enhanced cells with validation"""
        grid = []
        for x in range(len(generator.cell)):
            row = []
            for y in range(len(generator.cell[0])):
                # Add validation during cell creation
                cell_value = generator.cell[x][y]
                if not isinstance(cell_value, int):
                    print(f"WARNING: Invalid cell value at ({x},{y}): {cell_value}")
                    cell_value = DungeonGenerator.NOTHING
                    
                cell = DungeonCell(cell_value, x, y)
                
                # Verify initialization
                if not hasattr(cell, 'current_type'):
                    print(f"CRITICAL: DungeonCell at ({x},{y}) has no current_type!")
                    cell.current_type = DungeonGenerator.NOTHING

                # Store door information
                if cell.base_type & DungeonGenerator.DOORSPACE:
                    door_type = self.get_door_type(cell.base_type)
                    #print(f"Door at ({x},{y}): {door_type}")
                    
                row.append(cell)
            grid.append(row)
        return grid

    def get_room_description(self, position: Tuple[int, int]) -> str:
        """Get description of a room at given position"""
        room_id = self.get_current_room_id(position)
        if room_id and room_id in self.rooms:
            return self.rooms[room_id].get('description', 'A mysterious room')
        
        # Fallback description
        cell_type = self.grid[position[0]][position[1]].base_type
        if cell_type == DungeonGenerator.ROOM:
            return "A stone chamber"
        elif cell_type == DungeonGenerator.CORRIDOR:
            return "A narrow passageway"
        return "An unknown area"
        
    def move_party(self, new_position):
        """Move party and update visibility"""
        self.party_position = new_position
        self.visibility.party_position = new_position
        self.visibility.update_visibility()
        
    def add_feature(self, position, feature_type, data=None):
        x, y = position
        self.grid[x][y].add_feature(feature_type, data)
        self.modification_history.append(('add_feature', position, feature_type))
        
    def transform_cell(self, position, new_type):
        x, y = position
        self.grid[x][y].transform(new_type)
        self.modification_history.append(('transform', position, new_type))
        
    def reveal_secrets(self, position):
        x, y = position
        self.grid[x][y].reveal_secret()
        self.modification_history.append(('reveal', position))

    def get_puzzle_hints(self, puzzle_id: str) -> List[Dict[str, Any]]:
        """Get hints for a puzzle across the entire dungeon"""
        hints = []
        for row in self.grid:
            for cell in row:
                for obj in cell.objects:
                    if obj.get('type') == 'puzzle' and obj.get('puzzle_id') == puzzle_id:
                        hints.extend(obj.get('hints', []))
        return hints

    def get_puzzle_data(self, puzzle_id: str) -> Dict[str, Any]:
        """Get complete puzzle data including hints"""
        for row in self.grid:
            for cell in row:
                for obj in cell.objects:
                    if obj.get('type') == 'puzzle' and obj.get('puzzle_id') == puzzle_id:
                        return {
                            'description': obj['description'],
                            'success_effect': obj['success_effect'],
                            'hints': obj.get('hints', [])
                        }
        return {
            'description': f"Unknown puzzle {puzzle_id}",
            'success_effect': "Something happens",
            'hints': []
        }

# Enhanced with AI integration
class EnhancedDungeonState(DungeonState):
    def __init__(self, generator):
        super().__init__(generator)
        self.theme = generator.opts.get('theme', 'dungeon')
        self.dynamic_features = {}
        self.quest_items = {}
        self.ai_notes = {}  # For DM's private notes about areas
        self.puzzles = {}   # Add this line to initialize puzzles dictionary

        # DEBUG: Verify grid content
        #print(f"EnhancedDungeonState initialized with grid size: {len(self.grid)}x{len(self.grid[0])}")
        for i in range(min(5, len(self.grid))):
            for j in range(min(5, len(self.grid[0]))):
                cell = self.grid[i][j]
                #print(f"Cell({i},{j}): {type(cell)}, base={cell.base_type}, current={cell.current_type}")

    def validate_grid(self):
        """Check all cells for required attributes"""
        errors = []
        for x in range(len(self.grid)):
            for y in range(len(self.grid[0])):
                cell = self.grid[x][y]
                if not hasattr(cell, 'current_type'):
                    errors.append(f"Cell ({x},{y}) missing current_type")
                elif not isinstance(cell.current_type, int):
                    errors.append(f"Cell ({x},{y}) has invalid current_type: {type(cell.current_type)}")
        
        if errors:
            print(f"GRID VALIDATION FAILED: {len(errors)} errors")
            for e in errors[:5]:  # Print first 5 errors
                print(e)
        else:
            print("Grid validation passed")
            
        return not errors

    def render_to_image(self, cell_size=18, grid_color=(200, 200, 200)):
        """Render dungeon with visibility control"""
        try:
            # Calculate dimensions
            width = len(self.grid[0]) * cell_size
            height = len(self.grid) * cell_size
            img = Image.new('RGB', (width, height), (52, 73, 94))
            draw = ImageDraw.Draw(img)
            
            # Debug: Count different cell types
            cell_type_counts = {
                "NOTHING": 0,
                "ROOM": 0,
                "CORRIDOR": 0,
                "DOOR": 0,
                "STAIRS": 0,
                "OTHER": 0
            }
            
            for x in range(len(self.grid)):
                for y in range(len(self.grid[0])):
                    cell = self.grid[x][y]
                    pos = (x, y)
                    visibility = self.visibility.get_visibility(pos)
                    
                    # Calculate drawing positions
                    pos_y = y * cell_size
                    pos_x = x * cell_size
                    
                    if not visibility['explored']:
                        continue  # Skip unexplored cells
                    
                    # Count cell types for debugging
                    if cell.base_type & DungeonGenerator.STAIRS:
                        cell_type_counts["STAIRS"] += 1
                    elif cell.base_type & DungeonGenerator.DOORSPACE:
                        cell_type_counts["DOOR"] += 1
                    elif cell.base_type & DungeonGenerator.ROOM:
                        cell_type_counts["ROOM"] += 1
                    elif cell.base_type & DungeonGenerator.CORRIDOR:
                        cell_type_counts["CORRIDOR"] += 1
                    elif cell.base_type == DungeonGenerator.NOTHING:
                        cell_type_counts["NOTHING"] += 1
                    else:
                        cell_type_counts["OTHER"] += 1
                    
                    # # Print detailed info for first 10 cells
                    # if cell_type_counts["NOTHING"] < 10:
                    #     print(f"Cell ({x},{y}) - "
                    #           f"Base: {hex(cell.base_type)}, "
                    #           f"Current: {hex(cell.current_type)}, "
                    #           f"Visible: {visibility['visible']}, "
                    #           f"Room ID: {self.get_current_room_id((x,y))}")
                    
                    if visibility['visible']:
                        self.draw_visible_cell(draw, pos_x, pos_y, cell_size, cell)
                    else:
                        self.draw_explored_cell(draw, pos_x, pos_y, cell_size, cell)
            
            # Print summary of cell types
            print("\n==== CELL TYPE SUMMARY ====")
            for k, v in cell_type_counts.items():
                print(f"{k}: {v}")
            print(f"Total cells: {len(self.grid)*len(self.grid[0])}")
            print("===========================\n")
            
            # Add grid lines
            if grid_color:
                self.draw_grid(draw, width, height, cell_size, grid_color)
                
            return img

        except Exception as e:
            print(f"Rendering error: {str(e)}")
            # Create error image with diagnostic information
            error_img = Image.new('RGB', (800, 600), (255, 200, 200))
            draw = ImageDraw.Draw(error_img)
            draw.text((10, 10), f"Rendering Error: {str(e)}", fill=(0, 0, 0))
            
            debug_info = [
                f"Grid size: {len(self.grid)}x{len(self.grid[0]) if self.grid else 'N/A'}",
                f"First cell type: {type(self.grid[0][0]) if self.grid and self.grid[0] else 'N/A'}",
                f"First cell has 'current_type': {hasattr(self.grid[0][0], 'current_type') if self.grid and self.grid[0] else 'N/A'}",
                f"Stairs count: {len(self.stairs)}",
                f"First stair: {self.stairs[0] if self.stairs else 'N/A'}"
            ]
            
            y_pos = 40
            for info in debug_info:
                draw.text((10, y_pos), info, fill=(0, 0, 0))
                y_pos += 20
                
            return error_img

    def get_door_type_from_cell(self, cell):
        """Get door type directly from cell's current_type"""
        if cell.current_type & DungeonGenerator.ARCH: return 'arch'
        if cell.current_type & DungeonGenerator.LOCKED: return 'locked'
        if cell.current_type & DungeonGenerator.TRAPPED: return 'trapped'
        if cell.current_type & DungeonGenerator.SECRET: return 'secret'
        if cell.current_type & DungeonGenerator.PORTC: return 'portc'
        return 'door'

    def draw_visible_cell(self, draw, x, y, size, cell):
        try:
            #print(f"🐛 DEBUG: Drawing door at ({cell.x},{cell.y})")
            # Base cell drawing (WORKS FINE)

            if cell.current_type & DungeonGenerator.ROOM:
                draw.rectangle([x, y, x+size, y+size], fill=(255, 255, 255))  # White for rooms
            elif cell.current_type & DungeonGenerator.CORRIDOR:
                draw.rectangle([x, y, x+size, y+size], fill=(220, 220, 220))  # Light gray for corridors
            elif cell.current_type & DungeonGenerator.BLOCKED:
                draw.rectangle([x, y, x+size, y+size], fill=(50, 50, 50))     # Dark gray for walls
            
            # DIRECT DOOR HANDLING (NO HELPER METHODS)
            if cell.current_type & DungeonGenerator.DOORSPACE:
                # Determine door type directly
                if cell.current_type & DungeonGenerator.ARCH: 
                    door_type = 'arch'
                elif cell.current_type & DungeonGenerator.LOCKED: 
                    door_type = 'locked'
                elif cell.current_type & DungeonGenerator.TRAPPED: 
                    door_type = 'trapped'
                elif cell.current_type & DungeonGenerator.SECRET: 
                    door_type = 'secret'
                elif cell.current_type & DungeonGenerator.PORTC: 
                    door_type = 'portc'
                else: 
                    door_type = 'door'

                # print(f"  Door type: {door_type}")
                    
                # SIMPLIFIED ORIENTATION DETECTION
                orientation = 'vertical'  # Default
                if (cell.x > 0 and cell.x < len(self.grid)-1 and
                    self.grid[cell.x-1][cell.y].current_type & (DungeonGenerator.ROOM | DungeonGenerator.CORRIDOR) and
                    self.grid[cell.x+1][cell.y].current_type & (DungeonGenerator.ROOM | DungeonGenerator.CORRIDOR)):
                    orientation = 'horizontal'

                # # Draw temporary marker to verify position
                # center_x = x + size//2
                # center_y = y + size//2
                # draw.ellipse([
                #     center_x-3, center_y-3,
                #     center_x+3, center_y+3
                # ], fill=(0, 0, 255))  # Blue dot
                
                # Use your original door drawing code
                self.draw_door_basic(draw, x, y, size, door_type, orientation)

            # Draw other features (water, rubble, etc.)
            if cell.features:
                self.draw_features(draw, x, y, size, cell.features)
            
            # STAIRS (WORKS FINE)
            if cell.current_type & DungeonGenerator.STAIRS:
                for stair in self.stairs:
                    if (cell.x, cell.y) == stair['position']:
                        dr = stair['next_position'][0] - cell.x
                        dc = stair['next_position'][1] - cell.y
                        orientation = 'horizontal' if abs(dc) > abs(dr) else 'vertical'
                        self.draw_stairs(draw, x, y, size, stair['key'], orientation)

            # Draw labels LAST so they're on top
            if cell.current_type & DungeonGenerator.LABEL:
                self.draw_label(draw, x, y, size, cell)
            
        except Exception as e:
            print(f"Error drawing cell at ({cell.x},{cell.y}): {str(e)}")
            draw.rectangle([x, y, x+size, y+size], fill=(255, 0, 0))
            draw.text((x+5, y+5), "ERR", fill=(0, 0, 0))


    def draw_door_basic(self, draw, x, y, size, door_type, orientation):
        """Your door drawing code with enhanced visibility"""
        is_horizontal = (orientation == 'horizontal')
        center_x = x + size // 2
        center_y = y + size // 2
        door_width = size // 3
        arch_height = size // 6
        
        # Use distinct colors for better visibility
        door_color = (160, 120, 40)    # Medium brown
        arch_color = (100, 100, 100)   # Gray
        outline_color = (0, 0, 0)      # Black
        
        # Draw arches for all visible doors
        if door_type != 'secret':
            if is_horizontal:
                # Top arch
                draw.rectangle([
                    center_x - door_width//2, y,
                    center_x + door_width//2, y + arch_height
                ], fill=arch_color, outline=outline_color)
                # Bottom arch
                draw.rectangle([
                    center_x - door_width//2, y + size - arch_height,
                    center_x + door_width//2, y + size
                ], fill=arch_color, outline=outline_color)
            else:
                # Left arch
                draw.rectangle([
                    x, center_y - door_width//2,
                    x + arch_height, center_y + door_width//2
                ], fill=arch_color, outline=outline_color)
                # Right arch
                draw.rectangle([
                    x + size - arch_height, center_y - door_width//2,
                    x + size, center_y + door_width//2
                ], fill=arch_color, outline=outline_color)

        # Draw door slab for appropriate types
        if door_type in ['door', 'locked', 'trapped', 'portc']:
            if is_horizontal:
                draw.rectangle([
                    center_x - door_width//2, y + arch_height,
                    center_x + door_width//2, y + size - arch_height
                ], fill=door_color, outline=outline_color)
            else:
                draw.rectangle([
                    x + arch_height, center_y - door_width//2,
                    x + size - arch_height, center_y + door_width//2
                ], fill=door_color, outline=outline_color)

        # Add special symbols
        if door_type == 'locked':
            # Diamond lock symbol
            lock_size = size // 6
            diamond = [
                (center_x, center_y - lock_size//2),
                (center_x + lock_size//2, center_y),
                (center_x, center_y + lock_size//2),
                (center_x - lock_size//2, center_y)
            ]
            draw.polygon(diamond, fill=(200, 200, 200), outline=outline_color)
        
        elif door_type == 'portc':
            # Portcullis bars as 3 filled circles
            dot_radius = max(2, size // 12)  # Increased size for visibility
            dot_count = 3
            dot_spacing = size / (dot_count + 1)
            
            if is_horizontal:
                # Vertical bars
                for i in range(1, dot_count + 1):
                    dot_y = y + i * dot_spacing
                    draw.ellipse([
                        center_x - dot_radius, dot_y - dot_radius,
                        center_x + dot_radius, dot_y + dot_radius
                    ], fill=(80, 80, 80))
            else:
                # Horizontal bars
                for i in range(1, dot_count + 1):
                    dot_x = x + i * dot_spacing
                    draw.ellipse([
                        dot_x - dot_radius, center_y - dot_radius,
                        dot_x + dot_radius, center_y + dot_radius
                    ], fill=(80, 80, 80))
        
        elif door_type == 'secret':
            # Cover with wall color but add subtle indicator
            draw.rectangle([x, y, x+size, y+size], fill=(52, 73, 94))
            # Small secret symbol
            draw.line([
                (x + size//4, y + size//2),
                (x + 3*size//4, y + size//2)
            ], fill=(150, 150, 200), width=2)

    def draw_label(self, draw, x, y, size, cell):
        """Draw cell label if present"""
        char = self.cell_label(cell.current_type)
        if char:
            # Use a basic font
            try:
                from PIL import ImageFont
                font = ImageFont.load_default()
            except ImportError:
                font = None
            
            text_x = x + size // 2
            text_y = y + size // 2
            draw.text((text_x, text_y), char, fill=(0, 0, 0), 
                     font=font, anchor="mm")

    def cell_label(self, cell_value):
        """Extract character label from cell"""
        char_code = (cell_value >> 24) & 0xFF
        return chr(char_code) if 32 <= char_code <= 126 else None

    def draw_explored_cell(self, draw, x, y, size, cell):
        """Draw an explored but not currently visible cell"""
        # Grayed out version
        draw.rectangle([x, y, x+size, y+size], fill=(100, 100, 100))
        
        # Add subtle indicators
        if cell.current_type & DungeonGenerator.STAIRS:
            # Small stair indicator
            center_x = x + size // 2
            center_y = y + size // 2
            draw.rectangle([center_x-2, center_y-2, center_x+2, center_y+2], fill=(100, 100, 100))
        elif cell.current_type & DungeonGenerator.DOOR:
            # Small door indicator
            center_x = x + size // 2
            center_y = y + size // 2
            draw.rectangle([center_x-4, center_y-1, center_x+4, center_y+1], fill=(100, 100, 100))

    def draw_grid(self, draw, width, height, cell_size, color):
        """Draw grid lines"""
        # Horizontal lines
        for r in range(0, len(self.grid) + 1):
            y_pos = r * cell_size
            draw.line([0, y_pos, width, y_pos], fill=color, width=1)
        
        # Vertical lines
        for c in range(0, len(self.grid[0]) + 1):
            x_pos = c * cell_size
            draw.line([x_pos, 0, x_pos, height], fill=color, width=1)

    def get_door_type(self, cell_value):
        """Get door type from cell flags"""
        if cell_value & DungeonGenerator.ARCH: return 'arch'
        if cell_value & DungeonGenerator.LOCKED: return 'locked'
        if cell_value & DungeonGenerator.TRAPPED: return 'trapped'
        if cell_value & DungeonGenerator.SECRET: return 'secret'
        if cell_value & DungeonGenerator.PORTC: return 'portc'
        return 'door'

    def is_open_space(self, x, y):
        """Check if cell is open space"""
        if not self.is_valid_position((x, y)):
            return False
        cell = self.grid[x][y]
        return bool(self.current_type & (DungeonGenerator.ROOM | DungeonGenerator.CORRIDOR))

    def draw_door(self, draw, x, y, size, door_type, orientation):
        """Draw a door with proper detail and orientation"""
        try:
            is_horizontal = (orientation == 'vertical')
            center_x = x + size // 2
            center_y = y + size // 2
            door_width = size // 3
            arch_height = size // 6
            
            # Draw arches for all visible doors (except secrets)
            if door_type != 'secret':
                if is_horizontal:
                    # Top and bottom arches
                    draw.rectangle([
                        center_x - door_width//2, y,
                        center_x + door_width//2, y + arch_height
                    ], outline=(0, 0, 0))
                    draw.rectangle([
                        center_x - door_width//2, y + size - arch_height,
                        center_x + door_width//2, y + size
                    ], outline=(0, 0, 0))
                else:
                    # Left and right arches
                    draw.rectangle([
                        x, center_y - door_width//2,
                        x + arch_height, center_y + door_width//2
                    ], outline=(0, 0, 0))
                    draw.rectangle([
                        x + size - arch_height, center_y - door_width//2,
                        x + size, center_y + door_width//2
                    ], outline=(0, 0, 0))

            # Draw door slab for appropriate types
            if door_type in ['door', 'locked', 'trapped', 'portc']:
                if is_horizontal:
                    draw.rectangle([
                        center_x - door_width//2, y + arch_height,
                        center_x + door_width//2, y + size - arch_height
                    ], fill=(139, 69, 19), outline=(0, 0, 0))
                else:
                    draw.rectangle([
                        x + arch_height, center_y - door_width//2,
                        x + size - arch_height, center_y + door_width//2
                    ], fill=(139, 69, 19), outline=(0, 0, 0))

            # Add special symbols
            if door_type == 'locked':
                # Diamond lock symbol
                lock_size = size // 6
                diamond = [
                    (center_x, center_y - lock_size//2),
                    (center_x + lock_size//2, center_y),
                    (center_x, center_y + lock_size//2),
                    (center_x - lock_size//2, center_y)
                ]
                draw.polygon(diamond, fill=(100, 100, 100), outline=(0, 0, 0))
            
            elif door_type == 'portc':
                # Portcullis bars as 3 filled circles
                dot_radius = max(1, size // 12)
                dot_count = 3
                dot_spacing = size / (dot_count + 1)
                
                if is_horizontal:
                    # Vertical bars
                    for i in range(1, dot_count + 1):
                        dot_y = y + i * dot_spacing
                        draw.ellipse([
                            center_x - dot_radius, dot_y - dot_radius,
                            center_x + dot_radius, dot_y + dot_radius
                        ], fill=(0, 0, 0))
                else:
                    # Horizontal bars
                    for i in range(1, dot_count + 1):
                        dot_x = x + i * dot_spacing
                        draw.ellipse([
                            dot_x - dot_radius, center_y - dot_radius,
                            dot_x + dot_radius, center_y + dot_radius
                        ], fill=(0, 0, 0))
            
            elif door_type == 'secret':
                # Cover with wall color
                draw.rectangle([x, y, x+size, y+size], fill=(52, 73, 94))
                
        except Exception as e:
            print(f"Error drawing door at ({x},{y}): {str(e)}")
            # Draw error indicator
            draw.rectangle([x, y, x+size, y+size], fill=(255, 0, 0))
            draw.text((x+5, y+5), "DOOR ERR", fill=(0, 0, 0))


    def generate_legend_icons(self, icon_size=30):
        """Generate consistent legend icons using our drawing methods"""
        icons = {}
        elements = [
            'room', 'corridor', 'arch', 'open_door', 'locked_door',
            'trapped_door', 'secret_door', 'portcullis', 
            'stairs_up', 'stairs_down'
        ]
        
        for element in elements:
            icons[element] = self.create_legend_icon(element, icon_size)
        
        return icons

    def create_legend_icon(self, element_type, size):
        """Create a single legend icon"""
        img = Image.new('RGB', (size, size), (52, 73, 94))
        draw = ImageDraw.Draw(img)
        
        # Draw cell background
        margin = 1
        draw.rectangle([margin, margin, size-margin-1, size-margin-1], 
                      fill=(255, 255, 255))
        
        # Calculate centered drawing area
        scale_factor = 0.8
        scaled_size = int(size * scale_factor)
        x_offset = (size - scaled_size) // 2
        y_offset = (size - scaled_size) // 2
        
        # Draw element using our unified drawing methods
        if element_type == 'room':
            # Simple room representation
            draw.rectangle([
                x_offset + scaled_size//4, 
                y_offset + scaled_size//4,
                x_offset + 3*scaled_size//4,
                y_offset + 3*scaled_size//4
            ], outline=(0, 0, 0))
        
        elif element_type == 'corridor':
            # Simple corridor line
            draw.line([
                x_offset + scaled_size//4, 
                y_offset + scaled_size//2,
                x_offset + 3*scaled_size//4,
                y_offset + scaled_size//2
            ], fill=(0, 0, 0), width=2)
        
        elif element_type == 'arch':
            self.draw_door(draw, x_offset, y_offset, scaled_size, 'arch', 'horizontal')
        elif element_type == 'open_door':
            self.draw_door(draw, x_offset, y_offset, scaled_size, 'door', 'horizontal')
        elif element_type == 'locked_door':
            self.draw_door(draw, x_offset, y_offset, scaled_size, 'locked', 'horizontal')
        elif element_type == 'trapped_door':
            self.draw_door(draw, x_offset, y_offset, scaled_size, 'trapped', 'horizontal')
        elif element_type == 'secret_door':
            self.draw_door(draw, x_offset, y_offset, scaled_size, 'secret', 'horizontal')
        elif element_type == 'portcullis':
            self.draw_door(draw, x_offset, y_offset, scaled_size, 'portc', 'horizontal')
        elif element_type == 'stairs_up':
            self.draw_stairs(draw, x_offset, y_offset, scaled_size, 'up', 'horizontal')
        elif element_type == 'stairs_down':
            self.draw_stairs(draw, x_offset, y_offset, scaled_size, 'down', 'horizontal')
        
        return img

    def draw_features(self, draw, x, y, size, features):
        """Draw cell features (water, rubble, etc.)"""
        for feature in features:
            ftype = feature['type']
            if ftype == 'water':
                self.draw_water(draw, x, y, size)
            elif ftype == 'rubble':
                self.draw_rubble(draw, x, y, size)
            # Add more feature types as needed

    def draw_water(self, draw, x, y, size):
        """Draw water feature"""
        center_x = x + size // 2
        center_y = y + size // 2
        radius = size // 3
        draw.ellipse([
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius
        ], fill=(100, 100, 255), outline=(0, 0, 100))

    def draw_rubble(self, draw, x, y, size):
        """Draw rubble feature"""
        for i in range(5):
            rx = x + size * 0.2 + (i * size * 0.15)
            ry = y + size * 0.2 + (i * size * 0.15) % (size * 0.6)
            draw.rectangle([rx, ry, rx+size//8, ry+size//8], fill=(150, 150, 150))

    def draw_cell(self, draw, x, y, size, cell):
        """Draw a single cell based on its state"""
        # Calculate position
        x_pos = y * size
        y_pos = x * size
        
        # Determine color based on visibility
        if cell.visibility['visible']:
            fill = (255, 255, 255)  # Visible - white
        else:
            fill = (150, 150, 150)  # Explored but not visible - gray
        
        # Draw cell background
        draw.rectangle([x_pos, y_pos, x_pos+size, y_pos+size], fill=fill)
        
        # Draw cell features (doors, stairs, etc.)
        if cell.current_type & DungeonGenerator.DOOR:
            self.draw_door(draw, x_pos, y_pos, size)
        elif cell.current_type & DungeonGenerator.STAIRS:
            self.draw_stairs(draw, x_pos, y_pos, size, cell)

    def draw_stairs(self, draw, x, y, size, stair_type, orientation):
        """Draw stairs that look identical whether in grid or legend"""
        step_count = 5
        spacing = size / (step_count + 1)
        max_length = size * 0.8

        if orientation == 'vertical':
            center_y = y + size // 2
            for i in range(1, step_count + 1):
                if stair_type == 'up':
                    length = max_length
                else:  # Down stairs
                    length = max_length * (i / step_count)
                x_pos = x + i * spacing
                draw.line([
                    x_pos, center_y - length//2,
                    x_pos, center_y + length//2
                ], fill=(0, 0, 0), width=1)
        else:
            center_x = x + size // 2
            for i in range(1, step_count + 1):
                if stair_type == 'up':
                    length = max_length
                else:  # Down stairs
                    length = max_length * (i / step_count)
                y_pos = y + i * spacing
                draw.line([
                    center_x - length//2, y_pos,
                    center_x + length//2, y_pos
                ], fill=(0, 0, 0), width=1)
    
    def convert_to_generator_grid(self):
        """Convert state grid back to generator format with visibility"""
        grid = []
        for x in range(len(self.grid)):
            row = []
            for y in range(len(self.grid[0])):
                cell = self.grid[x][y]
                # Apply visibility masking
                if not cell.visibility['explored']:
                    row.append(DungeonGenerator.BLOCKED)
                elif not cell.visibility['visible']:
                    row.append(DungeonGenerator.PERIMETER)
                else:
                    row.append(cell.current_type)
            grid.append(row)
        return grid

    def add_puzzle(self, position, puzzle_data):
        """Register a puzzle created by the generator"""
        if not self.is_valid_position(position):
            return False
            
        self.puzzles[position] = puzzle_data
        return True
        
    def get_puzzle_at_position(self, position):
        """Get puzzle at a specific position, if any"""
        return self.puzzles.get(position)

    def get_current_room(self, position):
        """Get the room object at the given position"""
        room_id = self.get_current_room_id(position)
        if room_id is None:
            return None
            
        # Find the room by ID
        for room in self.rooms:
            if room['id'] == room_id:
                return room
        return None

    def get_current_room_id(self, position):
        """Get the ID of the room containing the given position"""
        x, y = position
        for room in self.rooms:
            if (room['north'] <= x <= room['south'] and 
                room['west'] <= y <= room['east']):
                return room['id']
        return None  # Position not in any room

    def get_room_description(self, position):
        """Get a description of the area at the given position"""
        room = self.get_current_room(position)
        if room:
            size = f"{room['width']}x{room['height']}"
            description = f"room {room['id']} ({size} feet)"
        else:
            # Describe corridor or other area
            cell = self.grid[position[0]][position[1]]
            if cell.base_type & DungeonGenerator.ROOM:
                description = "a mysterious chamber"
            elif cell.base_type & DungeonGenerator.CORRIDOR:
                description = "a stone corridor"
            elif cell.base_type & DungeonGenerator.STAIRS:
                description = "a stairwell"
            else:
                description = "an unknown area"
                
        # Check for puzzle
        if self.get_puzzle_at_position(position):
            description += " with a puzzling feature"
            
        return description
        
    def is_valid_position(self, position):
        """Check if position is within grid bounds"""
        x, y = position
        return (0 <= x < len(self.grid)) and (0 <= y < len(self.grid[0]))

    def add_feature(self, position, feature_type, data):
        if not self.is_valid_position(position):
            return False
            
        cell = self.grid[position[0]][position[1]]
        if not hasattr(cell, 'features'):
            cell.features = []
            
        cell.features.append({
            'type': feature_type,
            'data': data
        })
        return True
        
    def get_cell_features(self, position):
        """Get features at a specific position"""
        if not self.is_valid_position(position):
            return []
            
        cell = self.grid[position[0]][position[1]]
        return getattr(cell, 'features', [])
        
    def transform_cell(self, position, new_type):
        if not self.is_valid_position(position):
            return False
            
        self.grid[position[0]][position[1]]['base_type'] = new_type
        self.grid[position[0]][position[1]]['current_type'] = new_type
        return True
        
    def add_ai_note(self, position, note):
        """Add DM's private note about a location"""
        self.ai_notes[position] = note
        
    def populate_with_ai_content(self, ai_agent):
        """Use AI to populate dungeon with content"""
        # Add descriptive notes to special rooms
        for room in self.rooms:
            if room['id'] % 3 == 0:  # Every 3rd room gets special treatment
                note = ai_agent.generate_room_lore(room)
                self.add_ai_note(room['center'], note)
                
        # Place quest items
        for quest in self.game_state.active_quests.values():
            if quest['type'] == "fetch":
                item_room = random.choice(self.rooms)
                self.quest_items[item_room['id']] = quest['item_id']
        
    def break_door(self, position):
        x, y = position
        self.grid[x][y].break_door()
        self.modification_history.append(('break_door', position))
    
    def get_visible_area(self):
        """Get currently visible cells based on party position"""
        return self.visibility.get_visible_cells()