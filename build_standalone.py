# -*- coding: utf-8 -*-


import boto3
import hashlib
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
BUF_SIZE = 65536


ABOUT = {}
with open(Path(CWD, "wakatime/__about__.py")) as fh:
    exec(fh.read(), ABOUT)


if __name__ == '__main__':
    print('{timestamp} Building standalone binary wakatime-{ver}-{os}-{arch}'.format(
        timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        ver=ABOUT["__version__"],
        os=OS,
        arch=ARCH,
    ))
    start = datetime.utcnow()
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
    seconds = (datetime.utcnow() - start).total_seconds()
    minutes = seconds // 60

    filename = Path(CWD, 'dist', 'wakatime.exe' if OS == 'windows' else 'wakatime')

    print('{timestamp} Created standalone binary wakatime-{ver}-{os}-{arch} in {minutes}minute{mplural} {seconds}second{splural}'.format(
        timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        ver=ABOUT["__version__"],
        os=OS,
        arch=ARCH,
        minutes=minutes,
        mplural='' if minutes == 1 else 's',
        seconds=seconds,
        splural='' if seconds == 1 else 's',
    ))

    sha3 = hashlib.sha3_512()
    with open(filename, 'rb') as fh:
        while True:
            data = fh.read(BUF_SIZE)
            if not data:
                break
            sha3.update(data)
    sha3sum = sha3.hexdigest()
    print('{timestamp} SHA3-512: {sha3}'.format(
        timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        sha3=sha3sum,
    ))

    if os.environ.get('UPLOAD_ARTIFACTS'):
        bucket = os.environ['ARTIFACTS_BUCKET']
        client = boto3.client(
            's3',
            aws_access_key_id=os.environ['ARTIFACTS_KEY'],
            aws_secret_access_key=os.environ['ARTIFACTS_SECRET'],
        )

        shafile = str(Path(CWD, 'dist', 'wakatime.sha3-512'))
        with open(shafile, 'w') as fh:
            fh.write(sha3sum)

        s3_filename = '{os}-{arch}/wakatime-{ver}-{os}-{arch}'.format(
            ver=ABOUT["__version__"],
            os=OS,
            arch=ARCH,
        )
        client.upload_file(shafile, bucket, s3_filename + '.sha3-512', ExtraArgs={'ACL': 'public-read'})
        with open(filename, 'rb') as fh:
            client.upload_fileobj(fh, bucket, s3_filename, ExtraArgs={'ACL': 'public-read'})
        print('{timestamp} Uploaded artifact {filename} to s3.'.format(
            timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            filename=s3_filename,
        ))

        s3_filename = '{os}-{arch}/wakatime'.format(
            os=OS,
            arch=ARCH,
        )
        client.upload_file(shafile, bucket, s3_filename + '.sha3-512', ExtraArgs={'ACL': 'public-read'})
        with open(filename, 'rb') as fh:
            client.upload_fileobj(fh, bucket, s3_filename, ExtraArgs={'ACL': 'public-read'})
        print('{timestamp} Uploaded artifact {filename} to s3.'.format(
            timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            filename=s3_filename,
        ))
