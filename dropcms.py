from dropbox.client import DropboxClient
from flask import Flask, abort, request
from hashlib import sha256
import hmac
import json
from markdown import markdown
import os
import redis
import threading

if os.environ.get('HEROKU'):
    redis_url = os.environ['REDISTOGO_URL']
    redis_client = redis.from_url(redis_url)
else:
    redis_client = redis.StrictRedis(host='localhost', port=6379)

# App key and secret from the App console (dropbox.com/developers/apps)
APP_KEY = os.environ['APP_KEY']
APP_SECRET = os.environ['APP_SECRET']

app = Flask(__name__)
app.debug = True

# A random secret used by Flask to encrypt session data cookies
app.secret_key = os.environ['FLASK_SECRET_KEY']

DROPBOX_TOKEN = os.environ['DROPBOX_TOKEN']
DROPBOX_ROOT = os.environ['DROPBOX_ROOT']


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


def update():
    """Generate the html and upload to S3 only for the files that have
    changed
    """
    cursor = redis_client.get('cursor')
    client = DropboxClient(DROPBOX_TOKEN)

    has_more = True

    while has_more:
        if cursor:
            result = client.delta(cursor=cursor, path_prefix=DROPBOX_ROOT)
        else:
            result = client.delta(path_prefix=DROPBOX_ROOT)

        for path, metadata in result['entries']:

            # Ignore deleted files, folders, and non-markdown files
            if (metadata is None or
                    metadata['is_dir'] or
                    not path.endswith('.md')):
                continue

            # Convert to Markdown and store as <basename>.html
            html = markdown(client.get_file(path).read())
            # client.put_file(path[:-3] + '.html', html, overwrite=True)
            s3_upload(html, path)

        # Update cursor
        cursor = result['cursor']
        redis_client.set('cursor', cursor)

        # Repeat only if there's more to do
        has_more = result['has_more']


def s3_upload(html, path):
    print "Loaded %s to S3" % path


def validate_request():
    '''Validate that the request is properly signed by Dropbox.
       (If not, this is a spoofed webhook.)'''

    signature = request.headers.get('X-Dropbox-Signature')
    return signature == hmac.new(APP_SECRET, request.data, sha256).hexdigest()


@app.route('/webhook')
def webhook():
    """Receive a list of changed user IDs from Dropbox and process each.
    """

    # Make sure this is a valid request from Dropbox
    if not validate_request():
        abort(403)

    for uid in json.loads(request.data)['delta']['users']:
        # We need to respond quickly to the webhook request, so we do the
        # actual work in a separate thread. For more robustness, it's a
        # good idea to add the work to a reliable queue and process the queue
        # in a worker process.
        threading.Thread(target=update, args=()).start()
    return ''

if __name__ == '__main__':
    app.run(debug=True)
