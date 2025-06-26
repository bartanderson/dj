import os
import sys
from dungeon.generator import DungeonGenerator
from dungeon.state import EnhancedDungeonState  # Correct import path
from src.game.state import UnifiedGameState
from PIL import Image, ImageDraw  # Import for error image creation

# Delete previous test image if exists
test_image = 'test_dungeon.png'
if os.path.exists(test_image):
    os.remove(test_image)
    print(f"Deleted previous test image: {test_image}")

# Add module directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Detailed options
options = {
    'n_rows': 39,  # only odd
    'n_cols': 39,  # only odd
    'room_min': 3,
    'room_max': 9,
    'corridor_layout': 'Bent',  # Labyrinth - 0, Bent - 50, Straight - 100
    'remove_deadends': 80,      # 0 50 100
    'add_stairs': 2,            # min 2 for my purposes
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
    dungeon_state = EnhancedDungeonState(generator)
    game_state.dungeon_state = dungeon_state
except Exception as e:
    print(f"Error creating dungeon state: {str(e)}")
    raise

# Initialize visibility system
print("Initializing visibility system...")
game_state.dungeon_state.visibility.init_true_state()

# Set visibility mode
VISIBILITY_MODE = "full"  # "full", "fog", or "none"

if VISIBILITY_MODE == "full":
    print("Making entire dungeon visible...")
    game_state.dungeon_state.visibility.set_view(True, True)
elif VISIBILITY_MODE == "fog":
    print("Enabling fog of war with partial visibility...")
    # Reveal area around stairs
    for stair in game_state.dungeon_state.stairs:
        x, y = stair['position']
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = x+dx, y+dy
                if 0 <= nx < len(game_state.dungeon_state.grid) and 0 <= ny < len(game_state.dungeon_state.grid[0]):
                    game_state.dungeon_state.visibility.set_view_at((nx, ny), True, True)
else:  # "none"
    print("Hiding all cells...")
    game_state.dungeon_state.visibility.set_view(False, False)

# Debug: Print grid information
if game_state.dungeon_state.grid:
    print(f"Dungeon state grid size: {len(game_state.dungeon_state.grid)}x{len(game_state.dungeon_state.grid[0])}")
    # Check a center cell instead of corner
    mid_x = len(game_state.dungeon_state.grid) // 2
    mid_y = len(game_state.dungeon_state.grid[0]) // 2
    test_cell = game_state.dungeon_state.grid[mid_x][mid_y]
    print(f"Cell at ({mid_x},{mid_y}):")
    print(f"  Base type: {test_cell.base_type}")
    print(f"  Current type: {test_cell.current_type}")
    print(f"  Features: {test_cell.features}")
    print(f"  Visibility: {test_cell.visibility}")
    print(f"  Room ID: {game_state.dungeon_state.get_current_room_id((mid_x, mid_y))}")
else:
    print("Grid is empty!")

print("Rendering dungeon...")
try:
    img = game_state.dungeon_state.render_to_image(cell_size=options['cell_size'])
    print("Rendering completed successfully")
except Exception as e:
    print(f"Rendering failed: {str(e)}")
    # Create error image
    img = Image.new('RGB', (800, 600), (255, 200, 200))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), f"Rendering Error: {str(e)}", fill=(0, 0, 0))
    # Add debug info
    debug_info = [
        f"Grid: {len(game_state.dungeon_state.grid)}x{len(game_state.dungeon_state.grid[0]) if game_state.dungeon_state.grid else 'N/A'}",
        f"Stairs: {len(game_state.dungeon_state.stairs)}",
        f"Rooms: {len(game_state.dungeon_state.rooms)}"
    ]
    y_pos = 40
    for info in debug_info:
        draw.text((10, y_pos), info, fill=(0, 0, 0))
        y_pos += 20

print("Saving image...")
img.save(test_image)
print(f"Image saved as {test_image}")