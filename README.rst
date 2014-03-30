DROPCMS
=======

Static site generator using content synced from Dropbox.

Installation
------------

::

  $ pip install dropcms


Setup
-----

Set the following environmental variables:

==================== ==================================
Variable             Description
==================== ==================================
DROPBOX_ACCESS_TOKEN Generate a Dropbox API token that
                     has access to your account (see
                     `here <https://www.dropbox.com/developers/core/start/python>`_
                     for instructions)
DROPBOX_ROOT_FOLDER  The folder within your Dropbox
                     root folder that will be the root
                     of the content to render on your
                     site
REDIS_URL            (Optional) to reduce the amount of
                     time it takes to refresh the data,
                     set up Redis caching by setting
                     the URL here
DROPCMS_S3_BUCKET    The S3 buck to sync content with
==================== ==================================

Folder Structure
----------------

``dropcms`` will render markdown files one folder deep in ``DROPBOX_ROOT_FOLDER``. If there's an ``index.md`` file in any folder, it will act as the index of the folder. Otherwise, ``dropcms`` will render a unordered list of the pages in the folder as the folder index.

For example, if the ``DROPBOX_ROOT_FOLDER`` is set to ``my_content`` and the folder structure is as follows::

  ~/Dropbox/my_content/index.md
  ~/Dropbox/my_content/file1.md
  ~/Dropbox/my_content/folder1/file2.md
  ~/Dropbox/my_content/folder1/file3.md
  ~/Dropbox/my_content/folder1/folder2

``file2.md``, ``file3.md`` will be rendered but ``file1.md`` and ``folder2`` will be ignored. The root index of the site will be read from ``index.md`` but the index of ``folder1`` will be automatically generated.

Syncing With Amazon S3
----------------------

Note: to sync with S3, you must have AWS configured. See `here <http://docs.aws.amazon.com/cli/latest/reference/configure/index.html?highlight=config>`_ for instrucitons.

::

  $ fab sync


CLI Usage
=========

Build static files locally::

  dropcms build -s config.json -o _build

Run the site locally (to test)::

  dropcms run -s config.json -u 0.0.0.0:5000

Sync to S3::

  dropcms s3sync -s config.json

Configuration
=============

JSON file containing settings. Parameters:

- ``dropbox_root``: the folder within your Dropbox to load content from
- ``dropbox_token``: API token. Generate a Dropbox API token that has access to your account (see `here <https://www.dropbox.com/developers/core/start/python>`_ for instructions). Alternatively, the token can be set as the environmental variable ``DROPBOX_ACCESS_TOKEN``
- ``S3_bucket`` The S3 buck to sync content with
- ``redis_url`` (Optional) to reduce the amount of time it takes to refresh the data, set up Redis caching by setting the URL here