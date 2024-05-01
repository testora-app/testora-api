from apiflask import APIBlueprint
from flask import jsonify

from app._shared.schemas import SuccessMessage

main = APIBlueprint('main', __name__)

#routes
@main.get("/")
@main.output(SuccessMessage, 200)
def index():
    return jsonify({'message': 'Hello from your friends at Testora or is it?!!!'})
