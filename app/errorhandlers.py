from flask import jsonify

def page_not_found(e):
    return jsonify({'message': 'Not Found'})

def method_not_allowed(e):
    return jsonify({'message': 'Method Not Allowed'})

def internal_server_error(e):
    return jsonify({'message': 'Yie! Something happened and we are fixing it!'})


def forbidden(e):
    return jsonify({'message': 'You cannot do that.'})