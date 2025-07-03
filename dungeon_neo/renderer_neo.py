from PIL import Image, ImageDraw, ImageFont
from dungeon_neo.state_neo import DungeonStateNeo
from dungeon_neo.generator_neo import DungeonGeneratorNeo

class DungeonRendererNeo:
    COLORS = {
        'room': (255, 255, 255),
        'corridor': (220, 220, 220),
        'wall': (50, 50, 50),
        'door': (139, 69, 19),      # Brown
        'arch': (160, 120, 40),     # Light brown
        'secret': (52, 73, 94),     # Dark blue-gray
        'locked': (101, 67, 33),    # Darker brown
        'trapped': (150, 10, 10),   # Blood red
        'portc': (80, 80, 80),      # Dark gray
        'stairs_up': (27, 174, 96), # Green
        'stairs_down': (231, 76, 60), # Red
        'grid': (200, 200, 200),
        'background': (52, 73, 94),
        'explored': (100, 100, 100),
        'legend_bg': (45, 45, 45),
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
        
    def render(self, state: DungeonStateNeo, debug_show_all=False, include_legend=False):
        dungeon_img = self._render_dungeon(state, debug_show_all)
        
        if include_legend:
            icons = self.generate_legend_icons()
            return self.create_composite_image(dungeon_img, icons)
        return dungeon_img

    def _render_dungeon(self, state: DungeonStateNeo, debug_show_all=False):
        width = state.width * self.cell_size
        height = state.height * self.cell_size
        img = Image.new('RGB', (width, height), self.COLORS['background'])
        draw = ImageDraw.Draw(img)
        
        # Draw grid
        self._draw_grid(draw, width, height)
        
        # Precompute stair positions for efficient lookup
        stair_dict = {(stair['row'], stair['col']): stair for stair in state.stairs}
        
        # Draw cells
        for x in range(state.height):
            for y in range(state.width):
                cell = state.grid[x][y]
                visibility = state.visibility.get_visibility((x, y))
                
                if debug_show_all or visibility['explored']:
                    self._draw_cell(
                        draw, x, y, cell, 
                        visibility['visible'] or debug_show_all,
                        stair_dict
                    )
        return img
    
    def _draw_grid(self, draw, width, height):
        # Horizontal lines
        for y in range(0, height, self.cell_size):
            draw.line([(0, y), (width, y)], fill=self.COLORS['grid'], width=1)
        # Vertical lines
        for x in range(0, width, self.cell_size):
            draw.line([(x, 0), (x, height)], fill=self.COLORS['grid'], width=1)
    
    def _draw_cell(self, draw, x, y, cell, is_visible, stair_dict=None):
        x_pixel = y * self.cell_size
        y_pixel = x * self.cell_size
        
        if not is_visible:
            self._draw_explored_cell(draw, x_pixel, y_pixel, cell)
            return
            
        if cell.base_type & DungeonGeneratorNeo.BLOCKED:
            self._draw_wall(draw, x_pixel, y_pixel)
        elif cell.base_type & DungeonGeneratorNeo.ROOM:
            self._draw_room(draw, x_pixel, y_pixel)
        elif cell.base_type & DungeonGeneratorNeo.CORRIDOR:
            self._draw_corridor(draw, x_pixel, y_pixel)
            
        if cell.base_type & DungeonGeneratorNeo.DOORSPACE:
            self._draw_door(draw, x_pixel, y_pixel, cell)
        if cell.base_type & DungeonGeneratorNeo.STAIRS:
            stair = stair_dict.get((x, y))
            self._draw_stairs(draw, x_pixel, y_pixel, cell, stair)
    
    def _draw_wall(self, draw, x, y):
        draw.rectangle([
            x, y, 
            x + self.cell_size, y + self.cell_size
        ], fill=self.COLORS['wall'])
    
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
    
    def _draw_explored_cell(self, draw, x, y, cell):
        draw.rectangle([
            x, y, 
            x + self.cell_size, y + self.cell_size
        ], fill=self.COLORS['explored'])
    
    def _draw_door(self, draw, x, y, cell):
        # Get door type
        door_type = self._get_door_type(cell.base_type)
        orientation = self._get_door_orientation(cell)
        color = self.COLORS.get(door_type, self.COLORS['door'])
        
        is_horizontal = (orientation == 'horizontal')
        center_x = x + self.cell_size // 2
        center_y = y + self.cell_size // 2
        door_width = self.cell_size // 3
        arch_height = self.cell_size // 6
        
        # Draw door slab
        if door_type != 'secret':
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
        
        # Draw arch for all doors except secrets
        if door_type != 'secret':
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
            # Portcullis bars
            bar_thickness = max(2, self.cell_size // 12)
            bar_count = 3
            bar_spacing = self.cell_size / (bar_count + 1)
            
            if is_horizontal:
                for i in range(1, bar_count + 1):
                    bar_y = y + i * bar_spacing
                    draw.rectangle([
                        center_x - door_width//2, bar_y - bar_thickness//2,
                        center_x + door_width//2, bar_y + bar_thickness//2
                    ], fill=(40, 40, 40))
            else:
                for i in range(1, bar_count + 1):
                    bar_x = x + i * bar_spacing
                    draw.rectangle([
                        bar_x - bar_thickness//2, center_y - door_width//2,
                        bar_x + bar_thickness//2, center_y + door_width//2
                    ], fill=(40, 40, 40))
        
        elif door_type == 'secret':
            # Add subtle indicator
            draw.line([
                (x + self.cell_size//4, y + self.cell_size//2),
                (x + 3*self.cell_size//4, y + self.cell_size//2)
            ], fill=(150, 150, 200), width=2)
    
    def _draw_stairs(self, draw, x, y, cell, stair):
        stair_type = 'up' if cell.base_type & DungeonGeneratorNeo.STAIR_UP else 'down'
        color = self.COLORS['stairs_up'] if stair_type == 'up' else self.COLORS['stairs_down']
        
        step_count = 5
        spacing = self.cell_size / (step_count + 1)
        max_length = self.cell_size * 0.7
        step_color = (80, 80, 80)
        
        # Determine orientation based on next cell position
        if stair and 'next_row' in stair and 'next_col' in stair:
            dr = stair['next_row'] - stair['row']
            dc = stair['next_col'] - stair['col']
            orientation = 'horizontal' if abs(dc) > abs(dr) else 'vertical'
        else:
            orientation = 'horizontal'
        
        if orientation == 'horizontal':
            center_y = y + self.cell_size // 2
            for i in range(1, step_count + 1):
                # Tapered for down stairs, uniform for up
                length = max_length * (i / step_count) if stair_type == 'down' else max_length
                x_pos = x + i * spacing
                draw.line([
                    x_pos, center_y - length//2,
                    x_pos, center_y + length//2
                ], fill=step_color, width=2)
        else:
            center_x = x + self.cell_size // 2
            for i in range(1, step_count + 1):
                length = max_length * (i / step_count) if stair_type == 'down' else max_length
                y_pos = y + i * spacing
                draw.line([
                    center_x - length//2, y_pos,
                    center_x + length//2, y_pos
                ], fill=step_color, width=2)
                
        # Add directional indicator for down stairs
        if stair_type == 'down':
            arrow_size = self.cell_size // 8
            center_x = x + self.cell_size // 2
            center_y = y + self.cell_size // 2
            
            if orientation == 'horizontal':
                points = [
                    (x + self.cell_size - arrow_size, center_y),
                    (x + self.cell_size - arrow_size*2, center_y - arrow_size),
                    (x + self.cell_size - arrow_size*2, center_y + arrow_size)
                ]
            else:
                points = [
                    (center_x, y + self.cell_size - arrow_size),
                    (center_x - arrow_size, y + self.cell_size - arrow_size*2),
                    (center_x + arrow_size, y + self.cell_size - arrow_size*2)
                ]
            draw.polygon(points, fill=(200, 0, 0))
    
    def _get_door_type(self, base_type):
        if base_type & DungeonGeneratorNeo.ARCH:
            return 'arch'
        elif base_type & DungeonGeneratorNeo.DOOR:
            return 'door'
        elif base_type & DungeonGeneratorNeo.LOCKED:
            return 'locked'
        elif base_type & DungeonGeneratorNeo.TRAPPED:
            return 'trapped'
        elif base_type & DungeonGeneratorNeo.SECRET:
            return 'secret'
        elif base_type & DungeonGeneratorNeo.PORTC:
            return 'portc'
        return 'door'
    
    def _get_door_orientation(self, cell):
        # Simplified orientation based on typical door placement
        # In practice, this would check adjacent cells
        return 'vertical' if cell.x % 2 == 0 else 'horizontal'

    def generate_legend_icons(self, icon_size=30):
        """Generate consistent legend icons"""
        elements = [
            ('room', 'Room'),
            ('corridor', 'Corridor'),
            ('arch', 'Archway'),
            ('door', 'Open Door'),
            ('locked', 'Locked Door'),
            ('trapped', 'Trapped Door'),
            ('secret', 'Secret Door'),
            ('portc', 'Portcullis'),
            ('stairs_up', 'Stairs Up'),
            ('stairs_down', 'Stairs Down')
        ]
        
        icons = {}
        for element, label in elements:
            img = Image.new('RGB', (icon_size, icon_size), self.COLORS['legend_bg'])
            draw = ImageDraw.Draw(img)
            
            # Draw cell background
            margin = 2
            draw.rectangle([
                margin, margin, 
                icon_size - margin, icon_size - margin
            ], fill=self.COLORS['background'])
            
            # Draw element
            if element == 'room':
                self._draw_room(draw, 0, 0, icon_size)
            elif element == 'corridor':
                self._draw_corridor(draw, 0, 0, icon_size)
            elif element in ['arch', 'door', 'locked', 'trapped', 'secret', 'portc']:
                self._draw_door_icon(draw, 0, 0, icon_size, element, 'horizontal')
            elif 'stairs' in element:
                stair_type = element.split('_')[1]
                self._draw_stair_icon(draw, 0, 0, icon_size, stair_type, 'horizontal')
            
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

    def _draw_door_icon(self, draw, x, y, size, door_type, orientation):
        """Draw door icon for legend"""
        is_horizontal = (orientation == 'horizontal')
        center_x = x + size // 2
        center_y = y + size // 2
        door_width = size // 3
        arch_height = size // 6
        color = self.COLORS.get(door_type, self.COLORS['door'])
        
        # Draw door slab
        if door_type != 'secret':
            if is_horizontal:
                draw.rectangle([
                    center_x - door_width//2, y + arch_height,
                    center_x + door_width//2, y + size - arch_height
                ], fill=color)
            else:
                draw.rectangle([
                    x + arch_height, center_y - door_width//2,
                    x + size - arch_height, center_y + door_width//2
                ], fill=color)
        
        # Draw arch for all doors except secrets
        if door_type != 'secret':
            if is_horizontal:
                # Top arch
                draw.rectangle([
                    center_x - door_width//2, y,
                    center_x + door_width//2, y + arch_height
                ], fill=self.COLORS['arch'])
                # Bottom arch
                draw.rectangle([
                    center_x - door_width//2, y + size - arch_height,
                    center_x + door_width//2, y + size
                ], fill=self.COLORS['arch'])
            else:
                # Left arch
                draw.rectangle([
                    x, center_y - door_width//2,
                    x + arch_height, center_y + door_width//2
                ], fill=self.COLORS['arch'])
                # Right arch
                draw.rectangle([
                    x + size - arch_height, center_y - door_width//2,
                    x + size, center_y + door_width//2
                ], fill=self.COLORS['arch'])
        
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
            draw.polygon(diamond, fill=(100, 100, 100))
        
        elif door_type == 'portc':
            # Portcullis bars
            bar_thickness = max(2, size // 12)
            bar_count = 3
            bar_spacing = size / (bar_count + 1)
            
            if is_horizontal:
                for i in range(1, bar_count + 1):
                    bar_y = y + i * bar_spacing
                    draw.rectangle([
                        center_x - door_width//2, bar_y - bar_thickness//2,
                        center_x + door_width//2, bar_y + bar_thickness//2
                    ], fill=(40, 40, 40))
            else:
                for i in range(1, bar_count + 1):
                    bar_x = x + i * bar_spacing
                    draw.rectangle([
                        bar_x - bar_thickness//2, center_y - door_width//2,
                        bar_x + bar_thickness//2, center_y + door_width//2
                    ], fill=(40, 40, 40))
        
        elif door_type == 'secret':
            # Add subtle indicator
            draw.line([
                (x + size//4, y + size//2),
                (x + 3*size//4, y + size//2)
            ], fill=(150, 150, 200), width=2)

    def _draw_stair_icon(self, draw, x, y, size, stair_type, orientation):
        """Draw stair icon for legend"""
        color = self.COLORS['stairs_up'] if stair_type == 'up' else self.COLORS['stairs_down']
        step_count = 5
        spacing = size / (step_count + 1)
        max_length = size * 0.7
        step_color = (80, 80, 80)
        
        if orientation == 'horizontal':
            center_y = y + size // 2
            for i in range(1, step_count + 1):
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
                
        # Add directional indicator for down stairs
        if stair_type == 'down':
            arrow_size = size // 8
            center_x = x + size // 2
            center_y = y + size // 2
            
            if orientation == 'horizontal':
                points = [
                    (x + size - arrow_size, center_y),
                    (x + size - arrow_size*2, center_y - arrow_size),
                    (x + size - arrow_size*2, center_y + arrow_size)
                ]
            else:
                points = [
                    (center_x, y + size - arrow_size),
                    (center_x - arrow_size, y + size - arrow_size*2),
                    (center_x + arrow_size, y + size - arrow_size*2)
                ]
            draw.polygon(points, fill=(200, 0, 0))

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
