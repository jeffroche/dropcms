from flask import current_app, Blueprint, render_template
import dropcms

page_router = Blueprint("page_router", __name__)
cms = None


def get_or_create_cms():
    # This is ugly but Flask won't let you access the application
    # context until you are in an app function
    global cms
    if cms is None:
        # http://stackoverflow.com/questions/13454507/is-it-possible-to-import-flask-configuration-values-in-modules-without-circular
        DROPBOX_ACCESS_TOKEN = current_app.config.get('DROPBOX_ACCESS_TOKEN')
        DROPBOX_ROOT_FOLDER = current_app.config.get('DROPBOX_ROOT_FOLDER')
        cms = dropcms.DropCMS(DROPBOX_ACCESS_TOKEN, DROPBOX_ROOT_FOLDER)
    return cms


@page_router.route('/')
def index():
    cms = get_or_create_cms()
    page, page_list = cms.get_root_index()
    if page:
        return render_template('page.html', markup=page.html())
    else:
        return render_template('index.html', list=page_list)


@page_router.route('/<folder_name>/')
def folder_index(folder_name):
    cms = get_or_create_cms()
    page, page_list = cms.get_folder_index(folder_name)
    if page is not None:
        return render_template('page.html', markup=page.html())
    else:
        return render_template('index.html', list=page_list)


@page_router.route('/<folder_name>/<page_name>/')
def render_page(folder_name, page_name):
    cms = get_or_create_cms()
    page = cms.get_page(folder_name, page_name)
    return render_template('page.html', markup=page.html())
