from flask import Flask
from core.game_state import GameState
from routes.api import api_bp
from routes.views import views_bp

def create_app():
    app = Flask(__name__)
    app.game_state = GameState()  # Single game state instance
    
    # Register blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)