# Reference:
# https://github.com/dfm/osrc/blob/master/osrc/__init__.py

__all__ = ["create_app"]

import flask


def create_app(config_filename=None):
    app = flask.Flask(__name__)
    app.config.from_object("web.default_settings")
    if config_filename is not None:
        app.config.from_pyfile(config_filename)

    from views import page_router
    app.register_blueprint(page_router)
    return app
