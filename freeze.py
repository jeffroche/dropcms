from flask_frozen import Freezer
from web import create_app
from web.views import get_or_create_cms


def build(config_overrides):
    app = create_app(config_overrides)
    app.config['FREEZER_REMOVE_EXTRA_FILES'] = True
    freezer = Freezer(app)

    @freezer.register_generator
    def page_url_generator():
        cms = get_or_create_cms()
        contents = cms.structure()
        folder_names = contents['folders'].keys()
        for folder in folder_names:
            yield 'page_router.folder_index', {'folder_name': folder}
            page_names = contents['folders'][folder]['pages'].keys()
            for page in page_names:
                yield 'page_router.render_page', {'folder_name': folder,
                                                  'page_name': page}

    freezer.freeze()
