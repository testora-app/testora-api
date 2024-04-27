import pytest
from app import create_app
from flask import template_rendered, current_app, Flask
from contextlib import contextmanager

#setting up routes import
from app.routes import main


@pytest.fixture
def client():
    app = create_app()
    
    with app.test_client() as testing_client:
        
    #establish an application context
        with app.app_context():
            app.config.from_object('config.TestingConfig')
            yield testing_client
    
    
    
@pytest.fixture
def app():
    app = create_app() 
    with app.app_context():
        app.config.from_object('config.TestingConfig')
    yield app
    
    
@pytest.fixture
def captured_templates(app):
        recorded = []
        

        def record(sender, template, context, **extra):
            recorded.append((template, context))

        template_rendered.connect(record, app)
        try:
            yield recorded
        finally:
            template_rendered.disconnect(record, app)