from .dungeon import DungeonSystem

class GameState:
    def __init__(self):
        #========= remove when done=======================
        #
        # Create asymmetric test dungeon (15x19x15)
        test_options = {
            'seed': 'OrientationTest',
            'n_rows': 29,  # Vertical dimension (height)
            'n_cols': 29,  # Horizontal dimension (width)
            'dungeon_layout': 'None',
            'room_min': 3,
            'room_max': 5,
            'room_layout': 'Scattered',
            'corridor_layout': 'Straight',
            'remove_deadends': 0,
            'add_stairs': 2,
            'map_style': 'Standard',
            'grid': 'Square'
        }
        self.dungeon = DungeonSystem(options=test_options)
        self.dungeon.generate()
        #=================================================

        # self.dungeon = DungeonSystem()
        # self.dungeon.generate()  # Generate initial dungeon
    
    def move(self, direction):
        self.dungeon.move_party(direction)
    
    def get_dungeon_image(self, debug=False):
        img = self.dungeon.get_image(debug)
        
        if img.mode == 'RGBA':
            return img.convert('RGB')
        return img
    
    def get_current_room(self):
        return self.dungeon.get_current_room_description()

    def reset(self):
        self.dungeon.generate()