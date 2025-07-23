from PIL import Image, ImageDraw, ImageFont
from dungeon_neo.state_neo import DungeonStateNeo
from dungeon_neo.generator_neo import DungeonGeneratorNeo
from dungeon_neo.constants import CELL_FLAGS, DIRECTION_VECTORS, OPPOSITE_DIRECTIONS
from dungeon_neo.cell_neo import DungeonCellNeo
from dungeon_neo.overlay import Overlay

class DungeonRendererNeo:
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

    COLORS = {
        'room': (255, 255, 255),
        'corridor': (200, 200, 200),
        'blocked': (52, 73, 94),    # blocked
        'door': (101, 67, 33),      # Darker brown
        'arch': (160, 120, 40),     # Light brown
        'secret': (101, 67, 33),    # Darker brown
        'locked': (101, 67, 33),    # Darker brown
        'trapped': (101, 67, 33),   # Darker brown
        'portc': (10, 10, 10),      # Dark gray
        'stairs_up': (10, 10, 10),
        'stairs_down': (10, 10, 10),
        'grid': (100, 100, 100),
        'explored': (100, 100, 100),
        'legend_bg': (25, 25, 25),
        'legend_text': (255, 255, 255)
    }

    @property
    def cell_size(self):
        return self._cell_size

    @cell_size.setter
    def cell_size(self, value):
        self._cell_size = max(5, value)  # Minimum 5px

    @property
    def colors(self):
        return self._colors

    @colors.setter
    def colors(self, value):
        self._colors = {**self.COLORS, **value}
    
    def __init__(self, cell_size=18):
        self.cell_size = cell_size
        
    def render(self, state: DungeonStateNeo, debug_show_all=False, include_legend=True, visibility_system=None):
        # Pass visibility_system to _render_dungeon
        dungeon_img = self._render_dungeon(state, debug_show_all, visibility_system)
        print(f"Render in render_neo.py")
        if include_legend:
            icons = self.generate_legend_icons()
            return self.create_composite_image(dungeon_img, icons)
        return dungeon_img

    def _render_dungeon(self, state: DungeonStateNeo, debug_show_all=False, visibility_system=None):
        width = state.width * self.cell_size
        height = state.height * self.cell_size
        base_img = Image.new('RGB', (width, height), self.COLORS['blocked'])
        base_draw = ImageDraw.Draw(base_img)
        cs = self.cell_size
        
        # Draw grid
        self._draw_grid(base_draw, width, height)
        
        # DEBUG: Draw red dot at party position
        party_x, party_y = state.party_position
        base_draw.ellipse([
            party_y*cs + cs//3,
            party_x*cs + cs//3,
            party_y*cs + 2*cs//3,
            party_x*cs + 2*cs//3
        ], fill="red")

        print(f"Rendering dungeon at size {width}x{height}")
        print(f"Party position why is it coming out x/y flipped here?: {state.party_position}")

        explored_count = 0

        print(f"Rendering with visibility_system: {visibility_system is not None}")
        
        # Draw cells with visibility handling
        for x in range(state.width):
            for y in range(state.height):
            
                cell = state.get_cell(x, y)
                x_pix = y * cs
                y_pix = x * cs

                is_explored = visibility_system and visibility_system.is_explored(x, y)
                
                if is_explored:
                    explored_count += 1
                
                # Handle secrets first
                if cell.is_secret:
                    
                    if not state.secret_mask[y][x]:
                        # Undiscovered secret - normal view
                        if debug_show_all:
                            # Debug view: show door overlay
                            base_draw.rectangle([x_pix, y_pix, x_pix+cs, y_pix+cs], fill=self.COLORS['corridor'])
                            self._draw_door(base_draw, x_pix, y_pix, cell, state)
                            # Add red outline
                            base_draw.rectangle(
                                [x_pix, y_pix, x_pix+cs, y_pix+cs],
                                outline="red",
                                width=2
                            )
                        else:
                            base_draw.rectangle([x_pix, y_pix, x_pix+cs, y_pix+cs], fill=self.COLORS['blocked'])

                        # Continue to prevent double-rendering
                        continue
                    else:
                        # Discovered secret
                        base_draw.rectangle([x_pix, y_pix, x_pix+cs, y_pix+cs], fill=self.COLORS['corridor'])
                        self._draw_door(base_draw, x_pix, y_pix, cell, state)
                        if debug_show_all:
                            # Add red outline in debug mode
                            base_draw.rectangle(
                                [x_pix, y_pix, x_pix+cs, y_pix+cs],
                                outline="red",
                                width=2
                            )
                        # Continue to prevent double-rendering
                        continue


                # Then handle room cells normally
                elif cell.is_room:
                    base_draw.rectangle([x_pix, y_pix, x_pix+cs, y_pix+cs], fill=self.COLORS['room'])
                if cell.is_room:
                    base_draw.rectangle([x_pix, y_pix, x_pix+cs, y_pix+cs], fill=self.COLORS['room'])
                elif cell.is_corridor:
                    base_draw.rectangle([x_pix, y_pix, x_pix+cs, y_pix+cs], fill=self.COLORS['corridor'])
                elif cell.is_blocked:
                    base_draw.rectangle([x_pix, y_pix, x_pix+cs, y_pix+cs], fill=self.COLORS['blocked'])
                elif cell.is_door:
                    # Draw door space as corridor base
                    base_draw.rectangle([x_pix, y_pix, x_pix+cs, y_pix+cs], fill=self.COLORS['corridor'])
                    # Actual door will be drawn later
                
                # Draw doors
                if cell.is_door:
                    orientation = state.get_door_orientation(cell.x, cell.y)
                    self._draw_door(base_draw, x_pix, y_pix, cell, state)
                
                # Draw stairs
                if cell.is_stairs:
                    stair_type = 'up' if cell.is_stair_up else 'down'
                    orientation = state.get_stair_orientation(x, y)
                    self._draw_stairs(base_draw, x_pix, y_pix, stair_type, orientation)
                
                # Draw labels
                if cell.has_label:
                    self._draw_label(base_draw, x_pix, y_pix, cell)

                # Render entities as text overlays
                for entity in cell.entities:
                    # Create text overlay for entity
                    overlay = Overlay(
                        primitive="text",
                        content=entity.get_symbol(),
                        color=(255, 255, 255),
                    )
                    overlay.render(draw, x_pix, y_pix, cs)
                
                # Render other overlays
                for overlay in cell.overlays:
                    overlay.render(draw, x_pix, y_pix, cs)
                
        # Draw grid on top of cells
        self._draw_grid(base_draw, width, height)

        # In the _render_dungeon method, after drawing the base cell:
        # Render entities as text overlays
        for entity in cell.entities:
            overlay = Overlay(
                primitive="text",
                content=entity.get_symbol(),
                color=(255, 255, 255),
                size=1.0
            )
            overlay.render(draw, y, x, self.cell_size)  # Note: x and y swapped

        # Render other overlays
        for overlay in cell.overlays:
            overlay.render(draw, y, x, self.cell_size)  # Note: x and y swapped

        # Draw party icon last
        self._draw_party_icon(base_draw, party_y * cs, party_x * cs)

        # --- Fog layer
        
        print(f"Rendered explored cells: {explored_count}/{state.width*state.height}")
        myexplored_count = 0
        if not debug_show_all and visibility_system:
            # Create fog layer
            fog_img = Image.new('RGBA', (width, height), (0, 0, 0, 255))  # Opaque black
            fog_draw = ImageDraw.Draw(fog_img)
            
            # Cut holes in fog layer for explored cells

            for y in range(state.height):
                for x in range(state.width):
                    if visibility_system.is_explored(x, y):
                        myexplored_count += 1
                        # Make this cell transparent in fog layer
                        fog_draw.rectangle(
                            [y*cs, x*cs, (y+1)*cs, (x+1)*cs], # swapping x and y because it needs to be but I wish I knew why it needed to be here
                            fill=(0, 0, 0, 0)  # Fully transparent
                        )
            # this proves I can cut a hole in the fog, but need to fix above so that there are positions to cut
            test = False
            if test:
                fog_draw.rectangle(
                                [0*cs, 0*cs, (0+1)*cs, (0+1)*cs],
                                fill=(0, 0, 0, 0) )
            
            # Composite layers
            base_rgba = base_img.convert('RGBA')
            composite = Image.alpha_composite(base_rgba, fog_img)
            result_img = composite.convert('RGB')
            print(f"my explored cells: {myexplored_count}/{state.width*state.height}")

            print("fog")
        else:
            result_img = base_img  # No fog in debug mode
            print("no fog")

        return result_img
    
    def _draw_party_icon(self, draw, x, y):
        """Draw party icon at position"""
        size = self.cell_size
        center_x = x + size // 2
        center_y = y + size // 2
        radius = size // 3
        draw.ellipse([
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius
        ], fill="#FF0000")  # Red circle

    def _draw_label(self, draw, x, y, cell):
        """Draw room label"""
        size = self.cell_size
        char_code = (cell.base_type & self.LABEL) >> 24
        if char_code:
            char = chr(char_code)
            font = ImageFont.load_default()
            text_x = x + (size - font.getlength(char)) // 2
            text_y = y + (size - 10) // 2
            draw.text((text_x, text_y), char, fill=(0, 0, 0), font=font)
            
    def _draw_grid(self, draw, width, height):
        # Horizontal lines
        for y in range(0, height, self.cell_size):
            draw.line([(0, y), (width, y)], fill=self.COLORS['grid'], width=1)
        # Vertical lines
        for x in range(0, width, self.cell_size):
            draw.line([(x, 0), (x, height)], fill=self.COLORS['grid'], width=1)
    
    def _draw_cell(self, draw, x, y, cell, stair_dict=None):
        x_pixel = y * self.cell_size
        y_pixel = x * self.cell_size
            
        if cell.base_type & self.BLOCKED:
            self._draw_block(draw, x_pixel, y_pixel)
        elif cell.base_type & self.ROOM:
            self._draw_room(draw, x_pixel, y_pixel)
        elif cell.base_type & self.CORRIDOR:
            self._draw_corridor(draw, x_pixel, y_pixel)
            
        if cell.base_type & self.DOORSPACE:
            self._draw_door(draw, x_pixel, y_pixel, cell)
        if cell.base_type & self.STAIRS:
            stair = stair_dict.get((x, y))
            self._draw_stairs(draw, x_pixel, y_pixel, cell, stair)
    
    def _draw_block(self, draw, x, y, size=None):
        """Draw block icon for legend"""
        if size is None:
            size = self.cell_size
        draw.rectangle([x, y, x + size, y + size], fill=self.COLORS['blocked'])
    
    def _draw_room(self, draw, x, y):
        draw.rectangle([
            x, y, 
            x + self.cell_size, y + self.cell_size
        ], fill=self.COLORS['room'])
    
    def _draw_corridor(self, draw, x, y):
        draw.rectangle([
            x, y, 
            x + self.cell_size, y + self.cell_size
        ], fill=self.COLORS['corridor'])

    def has_open_space(self, r, c):
        """Check if coordinates contain open space"""
        if not hasattr(self, 'state') or not self.state:
            return False
        if r < 0 or r >= self.state.height or c < 0 or c >= self.state.width:
            return False
        cell = self.state.grid[r][c]
        return cell and (cell.is_room or cell.is_corridor)
    
    def _draw_door(self, draw, x, y, cell, state, size=None):
        """Draw door with consistent appearance at any scale"""
        size = size or self.cell_size
        rev_orientation = 'vertical'
        # Get reversed orientation from state
        if state:
            rev_orientation = state.get_door_orientation(cell.x, cell.y)

        # Reverse all orientations
        if rev_orientation == 'horizontal':
            orientation = 'vertical'
        else:
            orientation = 'horizontal'

        #print(f"Rendering door at ({cell.x},{cell.y}) with orientation: {orientation}")

        # Determine door type from cell properties
        if cell.is_arch: door_type = 'arch'
        elif cell.is_door_unlocked: door_type = 'door'
        elif cell.is_locked: door_type = 'locked'
        elif cell.is_trapped: door_type = 'trapped'
        #elif cell.is_secret: door_type = 'secret'
        elif cell.is_portc: door_type = 'portc'
        else: door_type = 'door'

        color = self.COLORS.get(door_type, self.COLORS['door'])
        
        is_horizontal = (orientation == 'horizontal')
        center_x = x + self.cell_size // 2
        center_y = y + self.cell_size // 2
        door_width = self.cell_size // 3
        arch_height = self.cell_size // 6
        
        # Draw door slab
        if door_type not in ['arch', 'portc']: # allow secret door to be rendered like regular door we will cover with Fog of War
            if is_horizontal:
                draw.rectangle([
                    center_x - door_width//2, y + arch_height,
                    center_x + door_width//2, y + self.cell_size - arch_height
                ], fill=color)
            else:
                draw.rectangle([
                    x + arch_height, center_y - door_width//2,
                    x + self.cell_size - arch_height, center_y + door_width//2
                ], fill=color)
        
        # Draw arch for all doors even secrets
        if is_horizontal:
            # Top arch
            draw.rectangle([
                center_x - door_width//2, y,
                center_x + door_width//2, y + arch_height
            ], fill=self.COLORS['arch'])
            # Bottom arch
            draw.rectangle([
                center_x - door_width//2, y + self.cell_size - arch_height,
                center_x + door_width//2, y + self.cell_size
            ], fill=self.COLORS['arch'])
        else:
            # Left arch
            draw.rectangle([
                x, center_y - door_width//2,
                x + arch_height, center_y + door_width//2
            ], fill=self.COLORS['arch'])
            # Right arch
            draw.rectangle([
                x + self.cell_size - arch_height, center_y - door_width//2,
                x + self.cell_size, center_y + door_width//2
            ], fill=self.COLORS['arch'])
        
        # Add special symbols
        if door_type == 'locked':
            # Diamond lock symbol
            lock_size = self.cell_size // 6
            diamond = [
                (center_x, center_y - lock_size//2),
                (center_x + lock_size//2, center_y),
                (center_x, center_y + lock_size//2),
                (center_x - lock_size//2, center_y)
            ]
            draw.polygon(diamond, fill=(100, 100, 100))
        
        elif door_type == 'portc':
            # Portcullis vertical bars represented as circles
            bar_count = 5  # Number of vertical bars
            bar_radius = max(.5, self.cell_size // 20)
            bar_spacing = self.cell_size / (bar_count + 1)

            if is_horizontal:
                # Horizontal portcullis - bars vertical
                bar_x = x + self.cell_size // 2  # Center horizontally
                for i in range(1, bar_count + 1):
                    bar_y = y + i * bar_spacing
                    # Draw circle for each bar
                    bbox = [
                        bar_x - bar_radius,
                        bar_y - bar_radius,
                        bar_x + bar_radius,
                        bar_y + bar_radius
                    ]
                    draw.ellipse(bbox, fill=color)
            else:
                # Vertical portcullis - bars horizontal
                bar_y = y + self.cell_size // 2  # Center vertically
                for i in range(1, bar_count + 1):
                    bar_x = x + i * bar_spacing
                    # Draw circle for each bar
                    bbox = [
                        bar_x - bar_radius,
                        bar_y - bar_radius,
                        bar_x + bar_radius,
                        bar_y + bar_radius
                    ]
                    draw.ellipse(bbox, fill=color)

        elif door_type == 'secret':
            # no indication at all but you can turn on for debug
            show_secret = False
            if show_secret:
                draw.line([
                    (x + self.cell_size//4, y + self.cell_size//2),
                    (x + 3*self.cell_size//4, y + self.cell_size//2)
                ], fill=(200, 10, 20), width=2)
    
    def _draw_stairs(self, draw, x, y, stair_type, orientation, size=None):
        """Draw stair visualization with proper parameters"""
        """Draw stairs with consistent appearance at any scale"""
        size = size or self.cell_size
        color = self.COLORS['stairs_up'] if stair_type == 'up' else self.COLORS['stairs_down']
        
        step_count = 5
        spacing = size / (step_count + 1)
        max_length = size * 0.7
        step_color = (80, 80, 80)  # Dark gray for steps
        
        if orientation == 'horizontal':
            center_y = y + size // 2
            for i in range(1, step_count + 1):
                # Tapered for down stairs, uniform for up
                length = max_length * (i / step_count) if stair_type == 'down' else max_length
                x_pos = x + i * spacing
                draw.line([
                    x_pos, center_y - length//2,
                    x_pos, center_y + length//2
                ], fill=step_color, width=2)
        else:
            center_x = x + size // 2
            for i in range(1, step_count + 1):
                length = max_length * (i / step_count) if stair_type == 'down' else max_length
                y_pos = y + i * spacing
                draw.line([
                    center_x - length//2, y_pos,
                    center_x + length//2, y_pos
                ], fill=step_color, width=2)
    
    def _get_door_type(self, cell_flags):
        if cell_flags & self.ARCH:
            return 'arch'
        elif cell_flags & self.DOOR:
            return 'door'
        elif cell_flags & self.LOCKED:
            return 'locked'
        elif cell_flags & self.TRAPPED:
            return 'trapped'
        elif cell_flags & self.SECRET:
            return 'secret'
        elif cell_flags & self.PORTC:
            return 'portc'
        return 'door'

    def generate_legend_icons(self, icon_size=20):
        elements = [
            ('room', 'Room'),
            ('corridor', 'Corridor'),
            ('arch', 'Archway'),
            ('door', 'Open Door'),
            ('locked', 'Locked Door'),
            ('trapped', 'Trapped Door'),
            ('secret', 'Secret Door'),
            ('secret_debug', 'Secret Door (Debug)'),  # New entry
            ('portc', 'Portcullis'),
            ('stairs_up', 'Stairs Up'),
            ('stairs_down', 'Stairs Down')
        ]
        
        # Create mock state for consistent rendering
        mock_state = type('MockState', (), {
            'get_door_orientation': lambda self, x, y: 'horizontal'
        })()
        
        icons = {}
        for element, label in elements:
            img = Image.new('RGB', (icon_size, icon_size), self.COLORS['legend_bg'])
            draw = ImageDraw.Draw(img)
            
            # Reduced margin for better fitting
            margin = 1
            cell_size = icon_size - 2 * margin
            
            # Draw element with proper background
            if element == 'room':
                self._draw_room(draw, margin, margin, cell_size)
            elif element == 'corridor':
                self._draw_corridor(draw, margin, margin, cell_size)
            elif element in ['arch', 'door', 'locked', 'trapped', 'portc']:
                # Create mock cell
                mock_cell = type('MockCell', (object,), {
                    'is_arch': element == 'arch',
                    'is_door_unlocked': element == 'door',
                    'is_locked': element == 'locked',
                    'is_trapped': element == 'trapped',
                    'is_portc': element == 'portc',
                    'x': 0,
                    'y': 0
                })
                # Draw on corridor background
                self._draw_corridor(draw, margin, margin, cell_size)
                self._draw_door(draw, margin, margin, mock_cell, mock_state, cell_size)
            elif element == 'secret':
                # Normal secret door
                self._draw_block(draw, margin, margin, cell_size)
            elif element == 'secret_debug':
                # Debug secret door
                self._draw_block(draw, margin, margin, cell_size)
                mock_cell = type('MockCell', (object,), {
                    'is_arch': element == 'arch',
                    'is_door_unlocked': element == 'door',
                    'is_locked': element == 'locked',
                    'is_trapped': element == 'trapped',
                    'is_portc': element == 'portc',
                    'x': 0,
                    'y': 0
                })
                self._draw_door(draw, margin, margin, mock_cell, mock_state, cell_size)
                # Add red outline
                draw.rectangle(
                    [margin, margin, margin+cell_size, margin+cell_size],
                    outline="red",
                    width=1
                )
            elif 'stairs' in element:
                stair_type = element.split('_')[1]
                # Draw on corridor background
                self._draw_corridor(draw, margin, margin, cell_size)
                self._draw_stairs(draw, margin, margin, stair_type, 'horizontal', cell_size)
            
            icons[element] = (img, label)
        
        return icons

    def create_composite_image(self, dungeon_img, icons, position='right', padding=20):
        """Create image with dungeon on left and legend on right"""
        # Calculate dimensions
        icon_size = next(iter(icons.values()))[0].size[0] if icons else 30
        legend_width = 200
        total_width = dungeon_img.width + legend_width + padding * 3
        total_height = max(dungeon_img.height, 400)
        
        # Create composite image
        composite = Image.new('RGB', (total_width, total_height), self.COLORS['legend_bg'])
        draw = ImageDraw.Draw(composite)
        
        # Paste dungeon
        composite.paste(dungeon_img, (padding, padding))
        
        # Draw legend title
        font = ImageFont.load_default()
        draw.text((dungeon_img.width + padding * 2, padding), "LEGEND", 
                 fill=self.COLORS['legend_text'], font=font)
        
        # Draw legend items
        y_offset = padding + 30
        for element, (icon, label) in icons.items():
            composite.paste(icon, (dungeon_img.width + padding * 2, y_offset))
            draw.text((dungeon_img.width + padding * 2 + icon_size + 10, y_offset + icon_size//2 - 5), 
                     label, fill=self.COLORS['legend_text'], font=font)
            y_offset += icon_size + 10
        
        return composite

    def _draw_room(self, draw, x, y, size=None):
        """Draw room icon, works for both grid and legend"""
        if size is None:
            size = self.cell_size
        draw.rectangle([x, y, x + size, y + size], fill=self.COLORS['room'])

    def _draw_corridor(self, draw, x, y, size=None):
        """Draw corridor icon, works for both grid and legend"""
        if size is None:
            size = self.cell_size
        draw.rectangle([x, y, x + size, y + size], fill=self.COLORS['corridor'])

class EnhancedRenderer(DungeonRendererNeo):
    def render_entity(self, draw, x, y, cs, entity):
        """Render entity using overlay system instead of icons"""
        # Skip direct icon rendering
        pass

    def render_cell(self, x, y, cell, state, debug=False):
        super().render_cell(x, y, cell, state, debug)
        cs = self.cell_size
        x_pix = y * cs
        y_pix = x * cs
        
        # Render entities as text overlays
        for entity in cell.entities:
            # Create text overlay for entity
            overlay = Overlay(
                primitive="text",
                text=entity.get_symbol(),
                color=(255, 255, 255),
                size=1.0
            )
            overlay.render(self.draw, x_pix, y_pix, cs)
        
        # Render other overlays
        for overlay in cell.overlays:
            overlay.render(self.draw, x_pix, y_pix, cs)

