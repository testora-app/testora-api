from flask import render_template

def page_not_found(e):
    return 'Error 404', 404


def method_not_allowed(e):
    return 'Error 405', 405


def internal_server_error(e):
    return 'Error 500', 500


def forbidden(e):
    return 'Error 403', 403