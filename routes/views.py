from flask import Blueprint, render_template, request
import io
import base64
from dungeon.generator import DungeonGenerator  # Updated import path
from src.ai.dm_agent import EnhancedDMAgent
from src.game.state import UnifiedGameState 
from src.AIDMFramework import EnhancedGameContext#, GameState, PuzzleEntity, Character
from dungeon.state import EnhancedDungeonState

views_bp = Blueprint('views', __name__)

# Use a fixed seed for consistent results
DEFAULT_SEED = 12345

@views_bp.route('/')
def generate_dungeon():
    # Create a game state instance
    game_state = UnifiedGameState()
    game_context = EnhancedGameContext()
    dm_agent = EnhancedDMAgent(game_state, game_context)
    
    # Get seed from URL parameter or use default
    seed = request.args.get('seed', DEFAULT_SEED)
    try:
        seed = int(seed)
    except ValueError:
        seed = DEFAULT_SEED

    options = {
        'seed': seed,
        'n_rows': 39,
        'n_cols': 39,
        'room_min': 3,
        'room_max': 9,
        'corridor_layout': 'Bent',
        'remove_deadends': 50,
        'add_stairs': 2
    }

    # Create dungeon and add to state
    generator = DungeonGenerator(options)
    generator.create_dungeon()
    game_state.dungeon_state = EnhancedDungeonState(generator)
    
    # Generate images
    img = game_state.dungeon_state.render_to_image()
    icons = game_state.dungeon_state.generate_legend_icons(icon_size=30)
    
    # Convert images to base64
    def img_to_base64(img):
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return base64.b64encode(img_byte_arr.getvalue()).decode('ascii')

    dungeon_base64 = img_to_base64(img)
    icon_base64 = {key: img_to_base64(img) for key, img in icons.items()}

    # Add AI description
    description = dm_agent.describe_dungeon()
    
    return render_template('dungeon.html', 
                          dungeon_img=dungeon_base64, 
                          icons=icon_base64,
                          seed=seed,
                          description=description)  # Add to template