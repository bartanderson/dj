import uuid, random
from flask import Flask, send_file, g, session
from core.game_state import GameState
from routes.api import api_bp

def create_app():
    app = Flask(__name__)
    app.game_state = GameState()  # Single game state instance
    app.secret_key = 'bobs your uncle'  # Important for sessions!

    @app.before_request
    def load_user():
        # Create session-based user identity
        if 'user_id' not in session:
            session['user_id'] = f"user_{uuid.uuid4().hex[:8]}"
            session['username'] = f"Adventurer-{random.randint(1000,9999)}"
        
        g.user = {
            'id': session['user_id'],
            'name': session['username']
        }

    # Configure logging
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler('dungeon.log', maxBytes=1024*1024, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
            
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    # Add root route directly
    @app.route('/')
    def dungeon_view():
        return send_file('templates\\dungeon.html')  # Serve HTML directly
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

