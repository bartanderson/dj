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

@api_bp.route('/download-debug', methods=['GET'])
def download_debug():
    """Download debug grid file"""
    try:
        filename = "dungeon_debug_grid.txt"
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
        
        # Use AI for all commands - simpler and more robust
        ai = DungeonAI(state)
        result = ai.process_command(command)
        
        # Update visibility if movement occurred
        if result.get('success') and 'MOVE' in result.get('message', ''):
            game_state.dungeon.update_visibility()
            
        return jsonify(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
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