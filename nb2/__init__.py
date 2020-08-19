from flask import Flask


def create_app(config=None):
    """Create and configure an instance of Nostalgiabot2"""

    app = Flask(__name__, instance_relative_config=True)
    # app.config.from_mapping(
    #     SECRET_KEY=""
    # )

    from nb2 import api

    app.register_blueprint(api.bp)

    return app


