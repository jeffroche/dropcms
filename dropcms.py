import os
import dropbox
import markdown
import redis as r
import json


class Page(object):

    def __init__(self, file_path):
        self.path = file_path

    def load(self, dropbox):
        """Loads the file from dropbox and returns the rendered html
        """
        file_meta = dropbox.metadata(self.path)
        rev = file_meta['rev']
        f = dropbox.get_file(self.path)
        html = markdown.markdown(f.read())
        return html

    def rev(self):
        file_meta = self.client.metadata(self.path)
        return file_meta['rev']

    def load_and_cache(self):
        """Caches the page in redis
        """
        data = json.dumps({'html': self.html(),
                           'rev': self.rev()})
        redis.set(self.name, data)
        return data

    def cached(self):
        """Returns cached page from redis
        """
        raw = redis.get(self.path)
        if raw:
            return json.loads(raw)
        else:
            return None

    def html(self):
        """Loads file from Dropbox and generates html
        """
        f = self.client.get_file(self.path)
        return markdown.markdown(f.read())


class Folder(object):

    def __init__(self, path, rev, pages):
        self.path = path
        self.pages = {}
        self.last_rev = rev
        for page in pages:
            self.pages[page['name']] = Page(page['path'])

    def has_index(self):
        return 'index' in self.pages.keys()

    def index(self):
        """Generates a list of all the pages in the folder
        """
        return self.pages.keys()

    def rev(self):
        folder_meta = self.client.metadata(self.path)
        return folder_meta['rev']


class DropCMS(object):
    """The main manager class which holds the handle to Dropbox and
    Redis and reloads the data if necessary
    """

    VALID_EXTENSIONS = ('.md', '.markdown')

    def __init__(self, token, root_folder):
        self.dropbox = dropbox.client.DropboxClient(token)
        self.root = root_folder

    def structure(self):
        """Returns a list of folders with their file contents
        """
        folders = {}
        root_metadata = self.dropbox.metadata(self.root)
        for item in root_metadata['contents']:
            if item['is_dir']:
                folder_name, _ = self.parse_name(item['path'])
                folder_meta = self.dropbox.metadata(item['path'])
                files = self.get_files(folder_meta['contents'])
                folders[folder_name] = {
                    'path': item['path'], 'pages': files
                }
        return folders

    def get_files(self, contents):
        """Returns a ``Page`` object for each markdown file in the
        folder
        """
        files = {}
        for item in contents:
            if not item['is_dir']:
                file_name, extn = self.parse_name(item['path'])
                if extn.lower() in self.VALID_EXTENSIONS:
                    files[file_name] = {'path': item['path']}
        return files

    def parse_name(self, path):
        """Returns the name and extension of the file/folder derived from
        the full path
        """
        file_name_with_extension = os.path.basename(path)
        file_name, extn = os.path.splitext(file_name_with_extension)
        return file_name, extn

    def refresh_folder(self, folder_name):
        """Reloads all metadata for the given folder
        """
        metadata = self.dropbox.metadata(self.folders[folder_name].path)
        self.folders[folder_name] = build_folder()

    def get_folder_index(self, folder_name):
        return self.folders[folder_name].index()

    def get_page(self, folder_name, page_name):
        """Loads the page from Dropbox if it's changed,
        otherwise loads it from Redis
        """
        content = self.structure()
        page_data = content[folder_name]['pages'][page_name]
        page = Page(page_data['path'])
        html = page.load(self.dropbox)
        return html


# app = Flask(__name__)

# if not HEROKU:
#     app.debug = True


# content = DropboxContent(DROPBOX_ACCESS_TOKEN, DROPBOX_ROOT_FOLDER)


# @app.route('/')
# def index():
#     render_folder('/')


# @app.route('/<folder_name>/')
# def render_folder(folder_name):
#     if content.folders[folder_name].has_index():
#         page = content.get_page(folder_name, 'index')
#         return render_template('index.html', content=page)
#     else:
#         page_list = content.get_folder(folder_name).page_list()
#         return render_template('list.html', list=page_list)


# @app.route('/<folder_name>/<page_name>/')
# def render_page(folder_name, page_name):
#     page = content.get_page(folder_name, page_name)
#     return render_template('page.html', content=page)
