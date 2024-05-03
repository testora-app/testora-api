from app import create_app
from flask_migrate import migrate

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        migrate()
    app.run(threaded=True)