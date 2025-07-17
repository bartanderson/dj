from flask import Blueprint, jsonify, current_app, send_file, request
import io
from dungeon_neo.constants import *
from dungeon_neo.ai_integration import DungeonAI


api_bp = Blueprint('api', __name__)

@api_bp.route('/move', methods=['POST'])
def handle_movement():
    """Unified movement endpoint for all movement types"""
    data = request.json
    direction = data.get('direction')
    steps = data.get('steps', 1)
    
    try:
        game_state = current_app.game_state
        result = game_state.dungeon.state.movement.move(direction, steps)
        
        if result["success"]:
            game_state.dungeon.update_visibility()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Movement error: {str(e)}"
        })

@api_bp.route('/move/<direction>', methods=['POST'])
def move_party(direction):
    try:
        game_state = current_app.game_state
        state = game_state.dungeon.state
        
        # Use the same move_party method as AI commands
        success, message = state.move_party(direction, 1)
        
        if success:
            game_state.dungeon.update_visibility()
            return jsonify({
                "success": True,
                "message": message,
                "new_position": state.party_position
            })
        return jsonify({"success": False, "message": message})
    
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Movement error: {str(e)}"
        })

@api_bp.route('/ai-command', methods=['POST'])
def handle_ai_command():
    data = request.json
    command = data.get('command', '')
    
    try:
        game_state = current_app.game_state
        state = game_state.dungeon.state
        
        # Directly handle movement commands
        if command.lower().startswith(('move', 'go', 'walk', 'head')):
            # Parse direction and steps
            parts = command.split()
            direction = parts[1] if len(parts) > 1 else None
            steps = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
            
            if direction and direction in DIRECTION_VECTORS:
                result = state.movement.move(direction, steps)
                if result["success"]:
                    game_state.dungeon.update_visibility()
                return jsonify(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()  # Add this to see detailed error
        return jsonify({
            "success": False,
            "message": f"AI processing error: {str(e)}"
        })

@api_bp.route('/debug-state')
def debug_state():
    state = current_app.game_state.dungeon.state
    return jsonify({
        "party_position": state.party_position,
        "visibility_system": {
            "party_position": current_app.game_state.dungeon.visibility_system.party_position,
            "visible_cells": [
                [current_app.game_state.dungeon.visibility_system.is_visible(x, y) 
                 for x in range(state.width)] 
                for y in range(state.height)
            ]
        }
    })

@api_bp.route('/dungeon-image')
def get_dungeon_image():
    debug = request.args.get('debug', 'false').lower() == 'true'
    print(f"Generating dungeon image - debug mode: {debug}")
    img = current_app.game_state.get_dungeon_image(debug)
    
    # Convert to bytes
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

# Add reset endpoint
@api_bp.route('/reset', methods=['POST'])
def reset_dungeon():
    current_app.game_state.dungeon.generate()
    return jsonify({"success": True, "message": "Dungeon reset"})

@api_bp.route('/debug-toggle', methods=['POST'])
def dev_reveal_all():
    try:
        game_state = current_app.game_state
        game_state.dungeon_state.visibility.set_reveal_all(True)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/reset', methods=['POST'])
def dev_reset_view():
    try:
        game_state = current_app.game_state
        game_state.dungeon_state.visibility.set_reveal_all(False)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500