from dungeon_neo.constants import CELL_FLAGS
class DungeonCellNeo:

    BLOCKED = CELL_FLAGS['BLOCKED']
    ROOM = CELL_FLAGS['ROOM']
    CORRIDOR = CELL_FLAGS['CORRIDOR']
    PERIMETER = CELL_FLAGS['PERIMETER']
    # ENTRANCE = CELL_FLAGS['ENTRANCE']
    # ROOM_ID = CELL_FLAGS['ROOM_ID']
    # ARCH = CELL_FLAGS['ARCH']
    # DOOR = CELL_FLAGS['DOOR']
    # LOCKED = CELL_FLAGS['LOCKED']
    # TRAPPED = CELL_FLAGS['TRAPPED']
    SECRET = CELL_FLAGS['SECRET']

    # Composite flags
    DOORSPACE = CELL_FLAGS['DOORSPACE']
    # ESPACE = CELL_FLAGS['ESPACE']
    # STAIRS = CELL_FLAGS['STAIRS']
    # BLOCK_ROOM = CELL_FLAGS['BLOCK_ROOM']
    # BLOCK_CORR = CELL_FLAGS['BLOCK_CORR']
    # BLOCK_DOOR = CELL_FLAGS['BLOCK_DOOR']

    def __init__(self, base_type, x, y):
        self.base_type = base_type
        self.x = x
        self.y = y
        self.features = []
        self.objects = []
        self.npcs = []
        self.items = []
        self.visibility = {'explored': False, 'visible': False}
        self.search_difficulty = 10
        self.searched = False
        self.discovered = False
        self.modifications = []
        self.temporary_effects = []

    @property
    def position(self):
        return (self.x, self.y)

    @property
    def is_blocked(self):
        return bool(self.base_type & self.BLOCKED)

    @property
    def is_room(self):
        return bool(self.base_type & self.ROOM)

    @property
    def is_corridor(self):
        return bool(self.base_type & self.CORRIDOR)

    @property
    def is_door(self):
        return bool(self.base_type & self.DOORSPACE)
        
    def reveal_secret(self):
        if self.base_type == self.SECRET:
            self.discovered = True
            return True
        return False