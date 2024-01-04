from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object('config.DevelopmentConfig')

    # from .live_routes import video_blueprint
    # app.register_blueprint(video_blueprint)

    from .jpeg_routes import jpeg_blueprint
    app.register_blueprint(jpeg_blueprint)

    return app
