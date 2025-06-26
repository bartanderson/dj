from dungeon.generator import DungeonGenerator
from dungeon.state import EnhancedDungeonState
from src.game.state import UnifiedGameState

# Detailed options
options = {
    'n_rows': 39, # only odd
    'n_cols': 39, # only odd
    'room_min': 3,
    'room_max': 9,
    'corridor_layout': 'Bent',     # Labyrinth - 0, Bent - 50 , Straight - 100
    'remove_deadends': 80,         # 0 50 100 # letting 80 go cause thats what AI picked
    'add_stairs': 2,               # min 2 for my purposes
    'cell_size': 18
}

print("Creating dungeon generator...")
generator = DungeonGenerator(options)
print("Generating dungeon...")
dungeon_data = generator.create_dungeon()
print("Dungeon created successfully!")

print("Creating game state...")
game_state = UnifiedGameState()

print("Creating dungeon state...")
try:
    # Create and assign dungeon state
    dungeon_state = EnhancedDungeonState(generator)
    dungeon_state.visibility.init_true_state()  # Initialize the true state
	dungeon_state.visibility.update_true_visibility()  # Update visibility
    game_state.dungeon_state = dungeon_state
except Exception as e:
    print(f"Error creating dungeon state: {str(e)}")
    raise

# Initialize visibility system
game_state.dungeon_state.visibility.init_true_state()

# Set visibility mode
VISIBILITY_MODE = "full"  # "full", "fog", or "none"

if VISIBILITY_MODE == "full":
    print("Making entire dungeon visible...")
    game_state.dungeon_state.visibility.set_view(True, True)
elif VISIBILITY_MODE == "fog":
    print("Enabling fog of war with partial visibility...")
    game_state.dungeon_state.visibility.fog_enabled = True
    
    # Reveal area around stairs
    for stair in game_state.dungeon_state.stairs:
        x, y = stair['position']
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = x+dx, y+dy
                if 0 <= nx < len(game_state.dungeon_state.grid) and 0 <= ny < len(game_state.dungeon_state.grid[0]):
                    game_state.dungeon_state.visibility.set_view_at(
                        (nx, ny), True, True
                    )
else:  # "none"
    print("Hiding all cells...")
    game_state.dungeon_state.visibility.set_view(False, False)

# Debug: Print grid information
if game_state.dungeon_state.grid:
    print(f"Dungeon state grid size: {len(game_state.dungeon_state.grid)}x{len(game_state.dungeon_state.grid[0])}")
    test_cell = game_state.dungeon_state.grid[0][0]
    print(f"Cell at (0,0):")
    print(f"  Type: {test_cell.base_type} (base), {test_cell.current_type} (current)")
    print(f"  Position: ({test_cell.x}, {test_cell.y})")
    print(f"  Features: {test_cell.features}")
    print(f"  Visibility: {test_cell.visibility}")

# Make sure to update true visibility
game_state.dungeon_state.visibility.update_true_visibility()

print("Rendering dungeon...")
try:
    img = game_state.dungeon_state.render_to_image(cell_size=options['cell_size'])
except Exception as e:
    print(f"Rendering failed: {str(e)}")
    # Create error image
    img = Image.new('RGB', (800, 600), (255, 200, 200))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), f"Rendering Error: {str(e)}", fill=(0, 0, 0))

print("Saving image...")
img.save('test_dungeon.png')
print("Image saved as test_dungeon.png")
