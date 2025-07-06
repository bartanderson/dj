from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def dungeon_view():
    return render_template('dungeon.html')