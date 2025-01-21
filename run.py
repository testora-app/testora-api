from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(threaded=True, use_reloader=False)
