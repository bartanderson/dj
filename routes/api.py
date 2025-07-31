from flask import Blueprint, jsonify, current_app, send_file, request, session
import io
from dungeon_neo.constants import *
from dungeon_neo.ai_integration import DungeonAI
from dungeon_neo.movement_service import MovementService
from dungeon_neo.character import Character

api_bp = Blueprint('api', __name__)

# World state endpoints
@api_bp.route('/world-state')
def get_world_state():
    return jsonify({
        "worldMap": current_app.game_state.world.get_map_data(),
        "currentLocation": current_app.game_state.session.current_location,
        "party": [c.__dict__ for c in current_app.game_state.party],
        "activeQuests": [q.to_dict() for q in current_app.game_state.narrative.active_quests]
    })

@api_bp.route('/travel/<location_id>', methods=['POST'])
def travel_to_location(location_id):
    game_state = current_app.game_state
    location = game_state.world.get_location(location_id)
    
    if not location:
        return jsonify({"success": False, "message": "Location not found"})
    
    # Move party to new location
    game_state.session.move_party(location_id)
    
    return jsonify({
        "success": True,
        "location": location.to_dict(),
        "worldMap": game_state.world.get_map_data()
    })

@api_bp.route('/generate-dungeon', methods=['POST'])
def generate_dungeon():
    game_state = current_app.game_state
    current_location = game_state.session.current_location
    
    # Generate dungeon based on location type
    dungeon_type = game_state.world.get_location(current_location).dungeon_type
    game_state.dungeon.generate(type=dungeon_type)
    
    return jsonify({"success": True})
# End World state endpoints ###


@api_bp.route('/generate-content', methods=['POST'])
def generate_content():
    entity_type = request.json['entity_type']
    params = request.json.get('params', {})
    
    generator = current_app.game_state.world_builder
    result = generator.generate(entity_type, **params)
    
    # Add image if requested
    if request.json.get('include_image', False):
        image_gen = ImageGenerator(current_app.game_state.ai)
        image_url = image_gen.generate_image(result.get('image_prompt', ''))
        result['image_url'] = image_url
    
    return jsonify(result)

@api_bp.route('/regenerate-location', methods=['POST'])
def regenerate_location():
    location_name = request.json['location_name']
    game_state = current_app.game_state
    
    # Regenerate location
    location = game_state.world.locations[location_name]
    new_version = game_state.world_builder.generate(
        "location",
        location_type=location['type'],
        context="Regenerated version"
    )
    
    # Update world state
    game_state.world.update_location(location_name, new_version)
    return jsonify(new_version)

@api_bp.route('/town/describe', methods=['GET'])
def get_town_description():
    town_name = current_app.game_state.session.current_location
    description = current_app.game_state.campaign.get_location_description(town_name)
    return jsonify({"description": description})

@api_bp.route('/character/customize', methods=['POST'])
def customize_character():
    char_id = request.json['character_id']
    icon = request.json.get('icon')
    equipment = request.json.get('equipment')
    
    char = current_app.game_state.get_character(char_id)
    if not char:
        return jsonify({"success": False})
    
    customizer = CharacterCustomizer()
    customizer.customize_character(char, icon, equipment)
    return jsonify({"success": True})

@api_bp.route('/party/form', methods=['POST'])
def form_party():
    character_ids = request.json['character_ids']
    characters = [c for c in current_app.game_state.characters 
                 if c.id in character_ids]
    
    if len(characters) < 1:
        return jsonify({"success": False, "message": "No characters selected"})
    
    coordinator = PartyCoordinator()
    party = coordinator.form_party(characters)
    current_app.game_state.parties.append(party)
    return jsonify({"success": True, "party_id": party.id})

# Party management endpoints
@api_bp.route('/party/create', methods=['POST'])
def create_party():
    char_id = request.json['character_id']
    party_id = current_app.game_state.party_system.create_party(char_id)
    return jsonify({"success": True, "party_id": party_id})

@api_bp.route('/party/join', methods=['POST'])
def join_party():
    char_id = request.json['character_id']
    party_id = request.json['party_id']
    success = current_app.game_state.party_system.join_party(char_id, party_id)
    return jsonify({"success": success})

@api_bp.route('/party/leave', methods=['POST'])
def leave_party():
    char_id = request.json['character_id']
    result = current_app.game_state.party_system.leave_party(char_id)
    return jsonify({"success": result is not False, "result": result})

@api_bp.route('/party/transfer-leadership', methods=['POST'])
def transfer_leadership():
    party_id = request.json['party_id']
    new_leader_id = request.json['new_leader_id']
    success = current_app.game_state.party_system.transfer_leadership(party_id, new_leader_id)
    return jsonify({"success": success})

# movement endpoints
@api_bp.route('/move', methods=['POST'])
def handle_party_movement():
    data = request.json
    direction = data.get('direction')
    steps = data.get('steps', 1)
    
    result = current_app.game_state.move_party(direction, steps)
    return jsonify(result)

@api_bp.route('/character/move', methods=['POST'])
def handle_character_movement():
    data = request.json
    char_id = data['character_id']
    direction = data['direction']
    steps = data.get('steps', 1)
    
    char = current_app.game_state.get_character(char_id)
    if not char:
        return jsonify({"success": False, "message": "Character not found"})
    
    result = current_app.game_state.character_movement.move_character(
        char, direction, steps
    )
    return jsonify(result)

#character endopoints
@api_bp.route('/character/create', methods=['POST'])
def create_character():
    name = request.json.get('name', 'Unnamed')
    user_id = session.get('user_id')
    
    # Create character
    char = Character(name, user_id)
    
    # Set position to current party position
    state = current_app.game_state.dungeon.state
    char.position = state.party_position
    
    # Add to game state
    current_app.game_state.add_character(char)
    
    return jsonify({"success": True, "character": char.__dict__})

@api_bp.route('/character/set-active', methods=['POST'])
def set_active_character():
    char_id = request.json['character_id']
    user_id = session.get('user_id')
    
    if not any(c.id == char_id for c in current_app.game_state.get_user_characters(user_id)):
        return jsonify({"success": False, "message": "Character not owned by user"})
        
    current_app.game_state.set_active_character(user_id, char_id)
    return jsonify({"success": True})

@api_bp.route('/character/delete', methods=['POST'])
def delete_character():
    char_id = request.json['character_id']
    user_id = session.get('user_id')
    
    # Verify ownership
    char = current_app.game_state.get_character(char_id)
    if not char or char.owner_id != user_id:
        return jsonify({"success": False})
    
    # Remove from game state
    current_app.game_state.characters = [c for c in current_app.game_state.characters if c.id != char_id]
    return jsonify({"success": True})

# User info endpoint
@api_bp.route('/user-info', methods=['GET'])
def user_info():
    user_id = session.get('user_id')
    characters = current_app.game_state.get_user_characters(user_id)
    active_char = next((c for c in characters if c.active), None)
    
    return jsonify({
        "user_id": user_id,
        "username": session.get('username'),
        "character_count": len(characters),
        "active_character": active_char.id if active_char else None
    })

@api_bp.route('/party/list', methods=['GET'])
def list_parties():
    party_system = current_app.game_state.party_system
    return jsonify({
        "parties": [
            {
                "id": pid,
                "leader": data["leader"],
                "members": data["members"]
            }
            for pid, data in party_system.parties.items()
        ]
    })

@api_bp.route('/character/select', methods=['POST'])
def select_character():
    char_id = request.json['character_id']
    session_id = request.headers.get('X-Session-ID')
    
    char = current_app.game_state.get_character(char_id)
    if not char:
        return jsonify({"success": False, "message": "Character not found"})
    
    # Try to lock character
    if char.lock(session_id):
        return jsonify({
            "success": True,
            "character": {
                "id": char.id,
                "name": char.name,
                "position": char.position,
                "stats": char.stats
            }
        })
    
    return jsonify({"success": False, "message": "Character is already in use"})

@api_bp.route('/character/list', methods=['GET'])
def list_characters():
    chars = [{
        "id": c.id,
        "name": c.name,
        "position": c.position,
        "type": c.type
    } for c in current_app.game_state.characters]
    
    return jsonify({"characters": chars})

# Unified movement endpoint -- buttons use this
@api_bp.route('/move', methods=['POST'])
def handle_movement():
    data = request.json
    direction = data.get('direction')
    steps = data.get('steps', 1)
    
    try:
        game_state = current_app.game_state
        # Access movement service directly
        result = game_state.dungeon.state.movement.move(direction, steps)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Movement error: {str(e)}"
        })

@api_bp.route('/download-debug', methods=['GET'])
def download_debug():
    filename = request.args.get('file', 'dungeon_debug_grid.txt')
    try:
        return send_file(
            filename,
            as_attachment=True,
            download_name="dungeon_debug.txt",
            mimetype='text/plain'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@api_bp.route('/debug-grid', methods=['GET'])        
def get_debug_grid(self, show_blocking=True, show_types=False):
    """
    Generate a text-based grid representation for debugging
    - show_blocking: Highlight movement-blocking cells
    - show_types: Show cell type abbreviations
    """
    grid = []
    px, py = self.party_position
    
    for y in range(self.height):
        row = []
        for x in range(self.width):
            cell = self.get_cell(x, y)
            if not cell:
                row.append('?')
                continue
            
            # Party position
            if x == px and y == py:
                row.append('P')
                continue
            
            # Movement blocking status
            if show_blocking:
                if self.movement.is_passable(x, y):
                    symbol = '·'  # Passable
                else:
                    symbol = '#'  # Blocked
            # Cell type display
            elif show_types:
                if cell.is_room: symbol = 'R'
                elif cell.is_corridor: symbol = 'C'
                elif cell.is_blocked: symbol = 'B'
                elif cell.is_perimeter: symbol = 'P'
                elif cell.is_door: symbol = 'D'
                elif cell.is_stairs: symbol = 'S'
                else: symbol = '?'
            # Simple view
            else:
                if cell.is_room: symbol = '■'
                elif cell.is_corridor: symbol = '·'
                else: symbol = ' '  # Empty/blocked
            
            row.append(symbol)
        grid.append(''.join(row))
    
    return grid

@api_bp.route('/ai-command', methods=['POST'])
def handle_ai_command():
    data = request.json
    command = data.get('command', '')
    
    try:
        game_state = current_app.game_state
        state = game_state.dungeon.state
        
        # Use AI for all commands - simpler and more robust
        ai = DungeonAI(state)
        result = ai.process_command(command)

        # Log successful command
        current_app.logger.info(f"AI command executed: {command}")
        current_app.logger.debug(f"AI result: {result}")
        
        if result.get('success'):
            if 'MOVE' in result.get('message', ''):
                game_state.dungeon.update_visibility() # Update visibility if movement occurred
            return jsonify(result)
        else:
            # Add detailed error to response
            result['command'] = command
            result['ai_response'] = result.get('ai_response', 'No AI response')
            return jsonify(result)
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        current_app.logger.error(f"AI processing error: {str(e)}\n{tb}")
        
        return jsonify({
            "success": False,
            "message": f"AI processing error: {str(e)}",
            "command": command,
            "traceback": tb if current_app.config['DEBUG'] else None
        })

@api_bp.route('/debug-state')
def debug_state():
    state = current_app.game_state.dungeon.state
    return jsonify({
        "dungeon_active": current_app.game_state.dungeon_active,
        "state_exists": bool(state),
        "party_position": getattr(state, 'party_position', None),
        "visibility_system_exists": hasattr(state, 'visibility_system'),
        "width": getattr(state, 'width', None),
        "height": getattr(state, 'height', None),
        "grid_system_exists": hasattr(state, 'grid_system'),
        "rooms_exists": hasattr(state, 'rooms'),
        "stairs_exists": hasattr(state, 'stairs')
    })
    # return jsonify({
    #     "party_position": state.party_position,
    #     "visibility_system": {
    #         "party_position": current_app.game_state.dungeon.visibility_system.party_position,
    #         "visible_cells": [
    #             [current_app.game_state.dungeon.visibility_system.is_visible(x, y) 
    #              for x in range(state.width)] 
    #             for y in range(state.height)
    #         ]
    #     }
    # })

@api_bp.route('/debug-test')
def debug_test():
    return "Debug test successful - API is working"

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
