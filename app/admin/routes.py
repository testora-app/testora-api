from apiflask import APIBlueprint
from flask import jsonify

from app._shared.schemas import SuccessMessage

admin = APIBlueprint('admin', __name__)


@admin.get('/admin/')
@admin.output(SuccessMessage, 200)
def index():
    return jsonify({'message': 'hi'})