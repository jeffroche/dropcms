# Reference:
# https://github.com/dfm/osrc/blob/master/osrc/__init__.py

__all__ = ["create_app"]

import flask


def create_app(config_overrides={}):
    app = flask.Flask(__name__)
    app.config.update(config_overrides)

    from views import page_router
    app.register_blueprint(page_router)
    return app
