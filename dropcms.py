import os
import dropbox
import markdown


class Page(object):

    def __init__(self, file_path, dropbox):
        self.path = file_path
        f = dropbox.get_file(self.path)
        self.text = f.read()

    def html(self):
        html = markdown.markdown(self.text)
        return html


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
        s = {
            'index_page': None,
            'folders': {}
        }
        root_metadata = self.dropbox.metadata(self.root)
        # Check for index file
        for item in root_metadata['contents']:
            name, extn = self.parse_name(item['path'])
            if name == 'index' and not item['is_dir']:
                s['index_page'] = {'path': item['path']}
            elif item['is_dir']:
                folder_meta = self.dropbox.metadata(item['path'])
                files = self.get_files(folder_meta['contents'])
                s['folders'][name] = {
                    'path': item['path'], 'pages': files
                }
        return s

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

    def get_root_index(self):
        """Returns the index page, if there is one, otherwise returns a
        list of the folders
        """
        content = self.structure()
        index = content['index_page']
        if index:
            index_page = Page(content['index_page']['path'], self.dropbox)
        else:
            index_page = None
        folder_names = content['folders'].keys()
        return index_page, folder_names

    def get_folder_index(self, folder_name):
        """Returns the index file, if it exists, and the list of files
        in the folder.
        """
        index_page = None
        content = self.structure()
        if 'index' in content['folders'][folder_name]['pages']:
            index_page = content['folders'][folder_name]['pages']['index']
        page_names = content['folders'][folder_name]['pages'].keys()
        return index_page, page_names

    def get_page(self, folder_name, page_name):
        """Loads the page from Dropbox if it's changed,
        otherwise loads it from Redis
        """
        content = self.structure()
        page_data = content['folders'][folder_name]['pages'][page_name]
        page = Page(page_data['path'], self.dropbox)
        return page
