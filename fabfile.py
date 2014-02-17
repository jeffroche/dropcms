from fabric.api import local

S3_BUCKET = 'cms.jeffroche.me'


def refresh():
    local('python freeze.py')


def s3():
    local('aws s3 sync web/build s3://%s --acl=public-read --delete' % S3_BUCKET)
