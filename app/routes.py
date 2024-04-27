from flask import Blueprint


main = Blueprint('main', __name__)

#routes
@main.route("/", methods=['GET'])
def lhome():
    return 'Hello World!'
