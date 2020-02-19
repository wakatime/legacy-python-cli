# -*- coding: utf-8 -*-


import boto3
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path


CWD = Path(__file__).resolve().parent
OS = platform.system().lower().replace('darwin', 'mac')
IS_64BIT = sys.maxsize > 2**32
ARCH = 'x86-' + ('64' if IS_64BIT else '32')


ABOUT = {}
with open(Path(CWD, "wakatime/__about__.py")) as f:
    exec(f.read(), ABOUT)


if __name__ == '__main__':
    subprocess.run(
        [
            'pyinstaller',
            '--onefile',
            '--noconfirm',
            '--clean',
            '--name', 'wakatime',
            '--distpath', str(Path(CWD, 'dist')),
            '--hidden-import', 'pkg_resources.py2_warn',
            str(Path(CWD, 'wakatime', 'cli.py')),
        ],
        check=True,
    )

    bucket = os.environ['ARTIFACTS_BUCKET']
    client = boto3.client(
        's3',
        aws_access_key_id=os.environ['ARTIFACTS_KEY'],
        aws_secret_access_key=os.environ['ARTIFACTS_SECRET'],
    )
    filename = 'wakatime.exe' if OS == 'windows' else 'wakatime'
    binary = Path(CWD, 'dist', filename)

    s3_filename = '{os}-{arch}/wakatime-{ver}-{os}-{arch}'.format(
        ver=ABOUT["__version__"],
        os=OS,
        arch=ARCH,
    )
    with open(binary, 'rb') as fh:
        client.upload_fileobj(fh, bucket, s3_filename, ExtraArgs={'ACL': 'public-read'})
    print('{timestamp} Uploaded artifact {filename} to s3.'.format(
        timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        filename=s3_filename,
    ))

    s3_filename = '{os}-{arch}/wakatime'.format(
        os=OS,
        arch=ARCH,
    )
    with open(binary, 'rb') as fh:
        client.upload_fileobj(fh, bucket, s3_filename, ExtraArgs={'ACL': 'public-read'})
    print('{timestamp} Uploaded artifact {filename} to s3.'.format(
        timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        filename=s3_filename,
    ))
