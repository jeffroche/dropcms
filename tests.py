# -*- coding: utf-8 -*-

import unittest
import mock
import dropcms
import dropbox
import json


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
        raise NameError('No fixture for %s', target)
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

        self.assertEqual(len(content), 2)
        self.assertIn('lists', content.keys())
        self.assertIn('One Pagers', content.keys())
        self.assertEqual(len(content['lists']['pages']), 4)
        self.assertEqual(len(content['One Pagers']['pages']), 4)
        self.assertIn('brooklyn',
                      content['lists']['pages'].keys())
        self.assertIn('python',
                      content['One Pagers']['pages'].keys())
        self.assertNotIn('windows.txt',
                         content['One Pagers']['pages'].keys())

    @mock.patch.object(dropbox.client.DropboxClient, 'metadata',
                       side_effect=metadata_side_effects)
    @mock.patch.object(dropbox.client.DropboxClient, 'get_file')
    def test_load_file(self, patched_get_file, patched_metadata):
        """Tests loading a file from dropbox
        """
        dbc = dropcms.DropCMS('token', '/')
        dbc.get_page('lists', 'brooklyn')
        patched_get_file.assert_called_with('/cms/lists/brooklyn.md')

    def test_page_index(self):
        """Tests that index file is loaded for a folder or generated
        properly based on the files in the folder
        """
        dbc = dropcms.DropCMS('token', '/')
        index_file, file_list = dbc.get_folder_index('/')
        self.assertIsNotNone(index_file)
        expexted_file_list = [
            {}
        ]
        self.assertEqual(file_list, expexted_file_list)
        index_file, file_list = dbc.get_folder_index('lists')


if __name__ == '__main__':
    unittest.main()
