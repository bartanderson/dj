class VisibilitySystemNeo:
    def __init__(self, grid, party_position):
        self.grid = grid
        self.party_position = party_position
        self.true_state = {}  # Initialize first
        self._init_true_state()  # Then populate
        self._reveal_all = False  # Set private attribute directly
        # Now it's safe to update visibility
        self.update_visibility()

    @property
    def reveal_all(self):
        return self._reveal_all

    @reveal_all.setter
    def reveal_all(self, value):
        self._reveal_all = value
        self.update_visibility()
        
    def _init_true_state(self):
        for x, row in enumerate(self.grid):
            for y, _ in enumerate(row):
                self.true_state[(x, y)] = {
                    'explored': False,
                    'visible': False
                }
    
    def set_reveal_all(self, reveal: bool):
        self.reveal_all = reveal
        self.update_visibility()
        
    def update_visibility(self):
        visible_cells = self._calculate_visible_cells()
        for pos in self.true_state:
            explored = self.true_state[pos]['explored']
            visible = pos in visible_cells
            self.true_state[pos] = {
                'explored': explored or visible,
                'visible': visible
            }
            
        # Update cells
        for pos, state in self.true_state.items():
            x, y = pos
            cell = self.grid[x][y]
            cell.visibility = state.copy()
    
    def _calculate_visible_cells(self):
        if self.reveal_all:
            return set(self.true_state.keys())
        return self._shadowcast(self.party_position)
    
    def _shadowcast(self, start_pos, max_distance=8):
        # Implement shadowcasting algorithm here
        # (Copy from your existing visibility.py)
        visible = set()
        visible.add(start_pos)
        return visible
    
    def get_visibility(self, pos):
        if self.reveal_all:
            return {'explored': True, 'visible': True}
        return self.true_state.get(pos, {'explored': False, 'visible': False})
    
    def get_visible_cells(self):
        return [pos for pos, state in self.true_state.items() if state['visible']]