from flask import Blueprint, jsonify, current_app, send_file, request
import io

api_bp = Blueprint('api', __name__)

@api_bp.route('/status')
def status_check():
    return jsonify({"status": "active"})

@api_bp.route('/move/<direction>', methods=['POST'])
def move_party(direction):
    current_app.game_state.move(direction)
    return jsonify({
        "message": f"Moved {direction}",
        "room": current_app.game_state.get_current_room()
    })

@api_bp.route('/dungeon-image')  # Make sure this route is defined
def get_dungeon_image():
    debug = request.args.get('debug', 'false').lower() == 'true'
    img = current_app.game_state.get_dungeon_image(debug)
    
    # Convert image to bytes
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