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
    app.game_state = UnifiedGameState()
        
    # Register blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)