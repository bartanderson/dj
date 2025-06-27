from flask import Blueprint, jsonify, current_app

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
    success, message = game_state.dungeon_state.move_party(direction)
    
    # Update visibility after moving
    game_state.dungeon_state.visibility.update_visibility()
    
    return jsonify({
        'success': success,
        'message': message,
        'position': game_state.dungeon_state.party_position,
        'visible_cells': game_state.dungeon_state.visibility.get_visible_cells()
    })

@api_bp.route('/dungeon-image')
def get_dungeon_image():
    game_state = current_app.game_state
    img = game_state.dungeon_state.render_to_image()
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return send_file(img_byte_arr, mimetype='image/png')

@api_bp.route('/interact/<npc_id>', methods=['POST'])
def interact_with_npc(npc_id):
    game_state = current_app.game_state
    result = game_state.interact_with_npc(npc_id)
    return jsonify(result)

@api_bp.route('/search', methods=['POST'])
def search_current_cell():
    game_state = current_app.game_state
    position = game_state.dungeon_state.party_position
    # Get character's search skill from request
    search_skill = request.json.get('search_skill', 0)
    success, message, items = game_state.dungeon_state.search_cell(position, search_skill)
    return jsonify({
        'success': success,
        'message': message,
        'items': items
    })

    @api_bp.route('/toggle-fog', methods=['POST'])
    def toggle_fog():
        try:
            game_state = current_app.game_state
            fog_enabled = game_state.dungeon_state.visibility.toggle_fog()
            return jsonify({
                'success': True,
                'fog_enabled': fog_enabled,
                'message': f'Fog of war {"enabled" if fog_enabled else "disabled"}'
            })
        except AttributeError as e:
            return jsonify({'error': f'Application context error: {str(e)}'}), 500

    @api_bp.route('/dev/reveal-all', methods=['POST'])
    def dev_reveal_all():
        try:
            if not current_app.config.get('DEBUG_MODE', False):
                return jsonify({'error': 'Not available in production'}), 403
                
            game_state = current_app.game_state
            game_state.dungeon_state.visibility.set_view(True, True)
            return jsonify({'success': True})
        except AttributeError as e:
            return jsonify({
                'error': f'Application context error: {str(e)}'
            }), 500

    @api_bp.route('/dev/reset-view', methods=['POST'])
    def dev_reset_view():
        try:
            if not current_app.config.get('DEBUG_MODE', False):
                return jsonify({'error': 'Not available in production'}), 403
                
            game_state = current_app.game_state
            game_state.dungeon_state.visibility.clear_view()
            return jsonify({'success': True})
        except AttributeError as e:
            return jsonify({
                'error': f'Application context error: {str(e)}'
            }), 500
@api_bp.route('/check-trap/<int:x>/<int:y>', methods=['GET'])
def check_trap(x, y):
    game_state = current_app.game_state
    result = game_state.dm_agent.handle_trap((x, y))
    return jsonify({'trap_effect': result})

@api_bp.route('/combat/<npc_id>', methods=['POST'])
def initiate_combat(npc_id):
    game_state = current_app.game_state
    result = game_state.dm_agent.resolve_combat(npc_id)
    return jsonify({'result': result})
