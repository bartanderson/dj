from flask import Flask
from routes.views import views_bp
from routes.api import api_bp
import os

from src.game.state import UnifiedGameState 
from src.AIDMFramework import EnhancedGameContext#, GameState, PuzzleEntity, Character

def create_app():
    app = Flask(__name__)
    app.config['DEBUG_MODE'] = os.environ.get('DEBUG_MODE', False)
    
    # Basic configuration
    app.config['SECRET_KEY'] = 'ollama-deepseek-never-guess-this12309'  # Change this for production! # os.environ.get('SECRET_KEY', 'dev_key')

    # Initialize game state
    game_state = UnifiedGameState("dark-fantasy")
    game_state.initialize_dungeon(
        seed=42,
        theme='abandoned-mine',
        difficulty='hard'
    )

    # Initialize game context with dungeon generator
    dungeon_generator = game_state.dungeon_state.generator
    game_context = EnhancedGameContext(dungeon_generator)
    game_context.dungeon_state = game_state.dungeon_state

    # Attach game context to game state
    game_state.game_context = game_context
    
    # Attach game state to app
    app.game_state = game_state
        
    # Register blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)