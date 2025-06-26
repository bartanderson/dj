from dungeon.generator import DungeonGenerator
from dungeon.state import EnhancedDungeonState
from src.game.state import UnifiedGameState 

# Add this near the top
VISIBILITY_MODE = "full"  # Options: "full", "fog", "none"

# Then after creating dungeon_state:
if VISIBILITY_MODE == "full":
    # Make all cells visible
    print("Making entire dungeon visible...")
    dungeon_state.visibility.set_view(True, True)
elif VISIBILITY_MODE == "fog":
    # Enable fog but reveal some cells
    print("Enabling fog of war with partial visibility...")
    dungeon_state.visibility.update_true_visibility()  # True state
    # Reveal area around stairs
    for stair in dungeon_state.stairs:
        x, y = stair['position']
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                nx, ny = x+dx, y+dy
                if 0 <= nx < len(dungeon_state.grid) and 0 <= ny < len(dungeon_state.grid[0]):
                    cell = dungeon_state.grid[nx][ny]
                    cell.visibility['explored'] = True
                    cell.visibility['visible'] = (abs(dx) <= 2 and abs(dy) <= 2)
else:  # "none"
    # No visibility - everything hidden
    print("Hiding all cells...")
    dungeon_state.visibility.set_global_visibility(False, False)

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

# Debug: Print generator output
print(f"Generator cell grid size: {len(generator.cell)}x{len(generator.cell[0])}")

print("Creating game state...")
game_state = UnifiedGameState()

print("Creating dungeon state...")
try:
    dungeon_state = EnhancedDungeonState(generator)
    dungeon_state.visibility.init_true_state()  # Critical initialization
    game_state.dungeon_state = dungeon_state

    if TEST_MODE == "full_visibility":
        # Temporary view override for testing
        dungeon_state.visibility.set_view(True, True)
    elif TEST_MODE == "partial_visibility":
        # Partial reveal for testing
        dungeon_state.visibility.set_view(True, False)
        # Reveal area around stairs
        for stair in dungeon_state.stairs:
            x, y = stair['position']
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    dungeon_state.visibility.set_view_at((x+dx, y+dy), True, True)
    else:  # "default"
        # No overrides - true visibility state
        pass

    # Always update true visibility
    dungeon_state.visibility.update_true_visibility()

    game_state.dungeon_state = dungeon_state
except Exception as e:
    print(f"Error creating dungeon state: {str(e)}")
    raise

# After creating dungeon_state
print("Validating dungeon state...")
if not dungeon_state.validate_grid():
    print("Critical grid errors found!")
else:
    print("Rendering dungeon...")
    img = dungeon_state.render_to_image(cell_size=options['cell_size'])

# Debug: Print grid information
if dungeon_state.grid:
    print(f"Dungeon state grid size: {len(dungeon_state.grid)}x{len(dungeon_state.grid[0])}")
    test_cell = dungeon_state.grid[0][0]
    print(f"Cell at (0,0):")
    print(f"  Type: {test_cell.base_type} (base), {test_cell.current_type} (current)")
    print(f"  Position: ({test_cell.x}, {test_cell.y})")
    print(f"  Features: {test_cell.features}")
    print(f"  Visibility: {test_cell.visibility}")
else:
    print("Dungeon state grid not created!")

# Make all cells visible
print("Making entire dungeon visible...")
for x in range(len(dungeon_state.grid)):
    for y in range(len(dungeon_state.grid[0])):
        cell = dungeon_state.grid[x][y]
        cell.visibility['explored'] = True
        cell.visibility['visible'] = True

print("Rendering dungeon...")
try:
    img = dungeon_state.render_to_image(cell_size=options['cell_size'])
except Exception as e:
    print(f"Rendering failed: {str(e)}")
    # Create error image
    img = Image.new('RGB', (800, 600), (255, 200, 200))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), f"Rendering Error: {str(e)}", fill=(0, 0, 0))

print("Saving image...")
img.save('test_dungeon.png')
print("Image saved as test_dungeon.png")