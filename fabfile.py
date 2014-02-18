from fabric.api import local
import os


S3_BUCKET = os.environ.get('DROPCMS_S3_BUCKET')


def sync():
    local('python freeze.py')
    push_s3()


def push_s3():
    local('aws s3 sync web/build s3://%s --acl=public-read --delete' %
          S3_BUCKET)
