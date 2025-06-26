from PIL import Image, ImageDraw

# ============================================================================
# DUNGEON RENDERER (SVG)
# ============================================================================

class DungeonRenderer:
    def __init__(self, cell_size=20):
        self.cell_size = cell_size
        self.colors = {
            'room': '#F9E79F',
            'corridor': '#FCF3CF',
            'wall': '#566573',
            'water': '#85C1E9',
            'rubble': '#B7950B',
            'party': '#2E86C1',
            'monster': '#CB4335',
            'door': '#784212',
            'stairs_up': '#27AE60',
            'stairs_down': '#E74C3C'
        }
    
    def render_to_svg(self, dungeon_state, visible_area=None):
        """Render dungeon state to SVG string"""
        width = len(dungeon_state.grid[0]) * self.cell_size
        height = len(dungeon_state.grid) * self.cell_size
        
        svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        
        # Draw grid
        for x in range(len(dungeon_state.grid)):
            for y in range(len(dungeon_state.grid[0])):
                if visible_area and (x, y) not in visible_area:
                    continue
                    
                self._draw_cell(svg, x, y, dungeon_state)
        
        # Draw features
        for (x, y), feature in dungeon_state.features.items():
            if visible_area and (x, y) not in visible_area:
                continue
            self._draw_feature(svg, x, y, feature)
        
        # Draw monsters
        for monster_id, (x, y) in dungeon_state.monsters.items():
            if visible_area and (x, y) not in visible_area:
                continue
            self._draw_monster(svg, x, y, monster_id)
        
        # Draw party
        px, py = dungeon_state.party_position
        self._draw_party(svg, px, py)
        
        svg += '</svg>'
        return svg
    
    def _draw_cell(self, svg, x, y, dungeon_state):
        """Draw base dungeon cell"""
        cell = dungeon_state.grid[x][y]
        color = self.colors['wall']
        
        if cell & DungeonGenerator.ROOM:
            color = self.colors['room']
        elif cell & DungeonGenerator.CORRIDOR:
            color = self.colors['corridor']
        elif cell & DungeonGenerator.STAIR_UP:
            color = self.colors['stairs_up']
        elif cell & DungeonGenerator.STAIR_DN:
            color = self.colors['stairs_down']
        
        self._draw_rect(svg, x, y, color)
        
        # Draw doors
        if cell & (DungeonGenerator.DOOR | DungeonGenerator.LOCKED | 
                  DungeonGenerator.TRAPPED | DungeonGenerator.SECRET):
            self._draw_door(svg, x, y)
    
    def _draw_feature(self, svg, x, y, feature):
        pass
        
    def _draw_feature(self, x, y, feature):
        # Custom feature rendering
        feature_type = feature['type']
        if feature_type == 'water':
            self._draw_water(x, y)
        elif feature_type == 'rubble':
            self._draw_rubble(x, y)
        elif feature_type == 'statue':
            self._draw_statue(x, y, feature['data'])
        # Add other features
    
    def _draw_water(self, svg, x, y):
        """Draw water feature"""
        self._draw_rect(svg, x, y, self.colors['water'], opacity=0.6)
        # Add wave patterns
        cx, cy = self._get_center(x, y)
        svg += f'<path d="M{cx-5} {cy+2} C{cx-2} {cy-2}, {cx+2} {cy-2}, {cx+5} {cy+2}" stroke="#3498DB" fill="none" />'
    
    def _draw_rubble(self, svg, x, y):
        """Draw rubble feature"""
        self._draw_rect(svg, x, y, self.colors['rubble'], opacity=0.7)
        # Add rock shapes
        cx, cy = self._get_center(x, y)
        for i in range(5):
            rx = cx - 4 + random.randint(0, 8)
            ry = cy - 4 + random.randint(0, 8)
            size = random.randint(1, 3)
            svg += f'<circle cx="{rx}" cy="{ry}" r="{size}" fill="#7D6608" />'
    
    def _draw_door(self, svg, x, y):
        """Draw door"""
        cx, cy = self._get_center(x, y)
        svg += f'<rect x="{cx-4}" y="{cy-8}" width="8" height="16" fill="{self.colors["door"]}" />'
    
    def _draw_monster(self, svg, x, y, monster_id):
        """Draw monster"""
        cx, cy = self._get_center(x, y)
        svg += f'<circle cx="{cx}" cy="{cy}" r="6" fill="{self.colors["monster"]}" />'
        svg += f'<text x="{cx}" y="{cy+5}" font-size="8" text-anchor="middle" fill="white">M</text>'
    
    def _draw_party(self, svg, x, y):
        """Draw party position"""
        cx, cy = self._get_center(x, y)
        svg += f'<circle cx="{cx}" cy="{cy}" r="8" fill="{self.colors["party"]}" />'
        svg += f'<text x="{cx}" y="{cy+5}" font-size="10" text-anchor="middle" fill="white">P</text>'
    
    def _draw_rect(self, svg, x, y, color, opacity=1.0):
        """Draw rectangle for cell"""
        size = self.cell_size
        svg += f'<rect x="{y*size}" y="{x*size}" width="{size}" height="{size}" fill="{color}" opacity="{opacity}" />'
    
    def _get_center(self, x, y):
        """Get center coordinates of a cell"""
        half = self.cell_size / 2
        return (y * self.cell_size + half, x * self.cell_size + half)
    
    def render(self, dungeon_state, visible_area=None):
        for x in range(len(dungeon_state.grid)):
            for y in range(len(dungeon_state.grid[0])):
                cell = dungeon_state.grid[x][y]
                
                # Skip unexplored cells
                if not cell.visibility['explored']:
                    self._draw_unexplored(x, y)
                    continue
                    
                # Draw base type
                self._draw_base_cell(x, y, cell.current_type)
                
                # Draw features
                for feature in cell.features:
                    self._draw_feature(x, y, feature)
                    
                # Draw visibility overlay
                if not cell.visibility['visible']:
                    self._draw_fog(x, y)