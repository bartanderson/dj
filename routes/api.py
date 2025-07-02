from flask import Blueprint, jsonify, current_app, request, send_file
import io
from dungeon.renderers.image_renderer import ImageRenderer
from dungeon.renderers.web_renderer import WebRenderer

api_bp = Blueprint('api', __name__)

@api_bp.route('/status')
def status_check():
    return jsonify({
        'status': 'online',
        'version': '0.1.0',
        'routes': ['/']
    })

@api_bp.route('/move/<direction>', methods=['POST'])
def move_party(direction):
    game_state = current_app.game_state
    new_pos = game_state.move_party(direction)
    game_state.dungeon_state.visibility.update_visibility()
    
    return jsonify({
        'success': new_pos != game_state.party_position,
        'position': new_pos,
        'visible_cells': game_state.dungeon_state.visibility.get_visible_cells()
    })

@api_bp.route('/dungeon-image')
def get_dungeon_image():
    game_state = current_app.game_state
    renderer = ImageRenderer(game_state.dungeon_state)
    img = renderer.render()
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return send_file(img_byte_arr, mimetype='image/png')

@api_bp.route('/dungeon-data')
def get_dungeon_data():
    game_state = current_app.game_state
    renderer = WebRenderer(game_state.dungeon_state)
    return jsonify(renderer.render())

@api_bp.route('/dev/reveal-all', methods=['POST'])
def dev_reveal_all():
    try:
        game_state = current_app.game_state
        game_state.dungeon_state.visibility.set_reveal_all(True)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/dev/reset-view', methods=['POST'])
def dev_reset_view():
    try:
        game_state = current_app.game_state
        game_state.dungeon_state.visibility.set_reveal_all(False)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/dev/normal-view', methods=['POST'])
def normal_view():
    try:
        game_state = current_app.game_state
        game_state.dungeon_state.visibility.set_reveal_all(False)
        game_state.dungeon_state.visibility.update_visibility()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500