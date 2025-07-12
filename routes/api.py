from flask import Blueprint, jsonify, current_app, send_file, request
import io

api_bp = Blueprint('api', __name__)

@api_bp.route('/status')
def status_check():
    return jsonify({"status": "active"})

@api_bp.route('/move/<direction>', methods=['POST'])
def move_party(direction):
    success, message, new_position = current_app.game_state.dungeon.move_party(direction)
    return jsonify({
        "success": success,
        "message": message,
        "new_position": new_position
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