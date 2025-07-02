from flask import Blueprint, render_template, request, current_app
import io
import base64
from dungeon.generator import DungeonGenerator  # Updated import path
from src.ai.dm_agent import EnhancedDMAgent
from src.game.state import UnifiedGameState 
from dungeon.state import EnhancedDungeonState
from dungeon.renderers.image_renderer import ImageRenderer

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def generate_dungeon():
    # Use the app's game state
    game_state = current_app.game_state
    
    # Initialize visibility if needed
    if not hasattr(game_state.dungeon_state.visibility, 'true_state'):
        game_state.dungeon_state.visibility.init_true_state()

    # Handle reveal_all parameter
    reveal_all = request.args.get('reveal_all', 'false').lower() == 'true'
    
    if reveal_all:
        print("Revealing entire dungeon")
        game_state.dungeon_state.visibility.set_reveal_all(True)
    else:
        print("Resetting to normal visibility")
        game_state.dungeon_state.visibility.set_reveal_all(False)

    # Get parameters from request
    seed = request.args.get('seed')
    theme = request.args.get('theme', 'abandoned-mine')
    difficulty = request.args.get('difficulty', 'hard')

    # Reinitialize if parameters changed
    if seed or theme or difficulty:
        game_state.initialize_dungeon(
            seed=int(seed) if seed else game_state.generation_seed,
            theme=theme,
            difficulty=difficulty
        )

    # Create renderer
    renderer = ImageRenderer(game_state.dungeon_state)
    img = renderer.render(debug_show_all=reveal_all)
    
    # Generate legend icons
    icons = game_state.dungeon_state.generate_legend_icons(icon_size=30)
    
    # Convert images to base64
    def img_to_base64(img):
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return base64.b64encode(img_byte_arr.getvalue()).decode('ascii')

    dungeon_base64 = img_to_base64(img)
    icon_base64 = {key: img_to_base64(img) for key, img in icons.items()}
    
    # Add AI description
    dm_agent = EnhancedDMAgent(game_state, game_state.game_context)
    description = dm_agent.describe_dungeon()
    
    return render_template('dungeon.html', 
                          dungeon_img=dungeon_base64, 
                          icons=icon_base64,
                          seed=game_state.generation_seed,
                          description=description)
    
    return render_template('dungeon.html', 
                          dungeon_img=dungeon_base64, 
                          icons=icon_base64,
                          seed=game_state.generation_seed,
                          description=description)