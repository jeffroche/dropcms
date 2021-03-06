# import tempfile
from dropbox.client import DropboxClient
from flask import Flask, abort, request
from hashlib import sha256
from jinja2 import Environment, PackageLoader
from markdown import markdown
from boto import s3 as boto_s3
from boto.s3.connection import S3Connection
import hmac
import json
import logging
import os
import redis
import threading


app = Flask(__name__)

if os.environ.get('HEROKU'):
    app.config.from_object('config_heroku')
    redis_url = os.environ['REDISTOGO_URL']
    redis_client = redis.from_url(redis_url)
    stream_handler = logging.StreamHandler()
    app.logger.addHandler(stream_handler)
    log_fmt = logging.Formatter('%(asctime)s %(levelname)s: %(message)s \
        [in %(pathname)s:%(lineno)d]')
    stream_handler.setFormatter(log_fmt)
else:
    app.debug = True
    app.config.from_object('config')
    redis_client = redis.StrictRedis(host='localhost', port=6379)


# Set logging info
app.logger.setLevel(logging.INFO)

# App key and secret from the App console (dropbox.com/developers/apps)
APP_SECRET = app.config['DROPBOX_APP_SECRET']


# A random secret used by Flask to encrypt session data cookies
app.secret_key = app.config['FLASK_SECRET_KEY']

DROPBOX_TOKEN = app.config['DROPBOX_TOKEN']
DROPBOX_ROOT = app.config['DROPBOX_ROOT']

template_env = Environment(loader=PackageLoader('web', 'templates'))

# S3
s3 = S3Connection(app.config['AWS_ACCESS_KEY_ID'],
                  app.config['AWS_SECRET_ACCESS_KEY'])
s3_bucket = s3.get_bucket(app.config['S3_BUCKET'])
s3_bucket.set_acl('public-read')


def init():
    """Generate the html and upload to S3
    """
    client = DropboxClient(DROPBOX_TOKEN)
    root = client.metadata(DROPBOX_ROOT)
    for f in root['contents']:
        # Ignore deleted files, folders, and non-markdown files
        if f['is_dir'] or not f['path'].endswith('.md'):
            continue

        # Convert to Markdown and store as <basename>.html
        html = markdown(client.get_file(f['path']).read())
        s3_upload(html, f['path'])


def update(init=False):
    """Generate the html and upload to S3 only for the files that have
    changed
    """
    if init:
        cursor = None
    else:
        cursor = redis_client.get('cursor')
    client = DropboxClient(DROPBOX_TOKEN)

    has_more = True

    while has_more:
        result = client.delta(cursor=cursor, path_prefix=DROPBOX_ROOT)

        for path, metadata in result['entries']:

            # Ignore deleted files, folders, and non-markdown files
            if (metadata is None or
                    metadata['is_dir'] or
                    not path.endswith('.md')):
                continue

            # Extract file name from full path
            filename = parse_name(path)

            # Convert to Markdown
            html_raw = markdown(client.get_file(path).read())
            html = add_template(html_raw)

            # Upload the file to S3
            s3_upload(html, filename)

        # Update cursor
        cursor = result['cursor']
        redis_client.set('cursor', cursor)

        # Repeat only if there's more to do
        has_more = result['has_more']


def s3_upload(html, filename):
    s3_file_path = "%s/index.html" % filename
    key = s3_bucket.get_key(s3_file_path)
    if not key:
        key = boto_s3.key.Key(s3_bucket)
        key.key = s3_file_path

    key.content_type = 'text/html; charset=UTF-8'
    key.set_contents_from_string(html, policy='public-read')
    app.logger.info("Uploaded %s", filename)


def add_template(html):
    template = template_env.get_template('page.html')
    return template.render(markup=html)


def parse_name(path):
    """Returns the name and extension of the file/folder derived from
    the full path
    """
    file_name_with_extension = os.path.basename(path)
    file_name, extn = os.path.splitext(file_name_with_extension)
    return file_name


def validate_request():
    '''Validate that the request is properly signed by Dropbox.
       (If not, this is a spoofed webhook.)'''

    signature = request.headers.get('X-Dropbox-Signature')
    return signature == hmac.new(APP_SECRET, request.data, sha256).hexdigest()


@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive a list of changed user IDs from Dropbox and process each.
    """

    app.logger.info("Received dropbox webhook")
    # Make sure this is a valid request from Dropbox
    if not validate_request():
        app.logger.info("Dropbox webhook was invalid")
        abort(403)

    for uid in json.loads(request.data)['delta']['users']:
        # We need to respond quickly to the webhook request, so we do the
        # actual work in a separate thread. For more robustness, it's a
        # good idea to add the work to a reliable queue and process the queue
        # in a worker process.
        threading.Thread(target=update, args=()).start()
    return ''


@app.route('/webhook', methods=['GET'])
def challenge():
    """Respond to the webhook challenge (GET request) by echoing back
    the challenge parameter.
    """

    return request.args.get('challenge')


@app.route('/hello')
def hello():
    app.logger.info("Hello world")
    return "Hello world"


if __name__ == '__main__':
    app.run(debug=True)
