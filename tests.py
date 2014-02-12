# -*- coding: utf-8 -*-

import unittest
import mock
import dropcms
import dropbox
import json
import web


def metadata_side_effects(target):
    if target == '/':
        fixture_file = 'test_data/sample_metadata_response.json'
    elif target == '/cms/index.md':
        fixture_file = 'test_data/index.json'
    elif target == '/cms/lists':
        fixture_file = 'test_data/lists.json'
    elif target == '/cms/One Pagers':
        fixture_file = 'test_data/one_pagers.json'
    elif target == '/cms/lists/brooklyn.md':
        fixture_file = 'test_data/brooklyn.json'
    else:
        raise NameError('No fixture for %s' % target)
    return json.loads(open(fixture_file).read())


class DropboxContentTestSuite(unittest.TestCase):

    @mock.patch.object(dropbox.client.DropboxClient, 'metadata',
                       side_effect=metadata_side_effects)
    def test_structure(self, patched_metadata):
        """Tests that the list of folders is returned by
        ``get_content_structure``
        """
        dbc = dropcms.DropCMS('token', '/')
        content = dbc.structure()
        folders = content['folders']

        self.assertEqual(len(folders), 2)
        self.assertIn('lists', folders.keys())
        self.assertIn('One Pagers', folders.keys())
        self.assertEqual(len(folders['lists']['pages']), 4)
        self.assertEqual(len(folders['One Pagers']['pages']), 4)
        self.assertIn('brooklyn',
                      folders['lists']['pages'].keys())
        self.assertIn('python',
                      folders['One Pagers']['pages'].keys())
        self.assertNotIn('windows.txt',
                         folders['One Pagers']['pages'].keys())

    @mock.patch.object(dropbox.client.DropboxClient, 'metadata',
                       side_effect=metadata_side_effects)
    @mock.patch.object(dropbox.client.DropboxClient, 'get_file')
    def test_load_file(self, patched_get_file, patched_metadata):
        """Tests loading a file from dropbox
        """
        dbc = dropcms.DropCMS('token', '/')
        dbc.get_page('lists', 'brooklyn')
        patched_get_file.assert_called_with('/cms/lists/brooklyn.md')

    @mock.patch.object(dropbox.client.DropboxClient, 'metadata',
                       side_effect=metadata_side_effects)
    @mock.patch.object(dropbox.client.DropboxClient, 'get_file')
    def test_root_index(self, patched_get_file, patched_metadata):
        """Tests that the root folder index file is loaded for a folder
        or generated properly based on the files in the folder
        """
        dbc = dropcms.DropCMS('token', '/')
        index_file, file_list = dbc.get_root_index()
        self.assertIsNotNone(index_file)
        self.assertEqual(file_list, ['One Pagers', 'lists'])

    @mock.patch.object(dropbox.client.DropboxClient, 'metadata',
                       side_effect=metadata_side_effects)
    @mock.patch.object(dropbox.client.DropboxClient, 'get_file')
    def test_folder_index(self, patched_get_file, patched_metadata):
        """Tests that the folder index file is loaded for a folder
        or generated properly based on the files in the folder
        """
        dbc = dropcms.DropCMS('token', '/')
        expected_files = ['cocktails', 'bars', 'books', 'brooklyn']
        index_file, file_list = dbc.get_folder_index('lists')
        self.assertIsNone(index_file)
        self.assertEqual(file_list, expected_files)


class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        self.patch1 = mock.patch('dropbox.client.DropboxClient.metadata',
                                 side_effect=metadata_side_effects)
        self.patch2 = mock.patch('dropbox.client.DropboxClient.get_file')
        self.patched_metadata = self.patch1.start()
        self.patched_get_file = self.patch2.start()
        app = web.create_app('test_settings.py')
        self.app = app.test_client()

    def tearDown(self):
        self.patch1.stop()
        self.patch2.stop()

    def test_root_index(self):
        self.app.get('/')
        self.patched_get_file.assert_called_with('/cms/index.md')


if __name__ == '__main__':
    unittest.main()
