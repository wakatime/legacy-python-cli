# -*- coding: utf-8 -*-


import boto3
import hashlib
import inspect
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from pygments.lexer import Lexer
from shutil import make_archive


CWD = Path(__file__).resolve().parent
OS = platform.system().lower().replace('darwin', 'mac')
IS_64BIT = sys.maxsize > 2**32
ARCH = 'x86-' + ('64' if IS_64BIT else '32')
BUF_SIZE = 65536


ABOUT = {}
with open(Path(CWD, "wakatime/__about__.py")) as fh:
    exec(fh.read(), ABOUT)


def build_command(tool):
    if tool == 'pyinstaller':
        return [
            'pyinstaller',
            '--noconfirm',
            '--clean',
            '--name', 'wakatime-cli',
            '--distpath', str(Path(CWD, 'dist')),
            '--hidden-import', 'pkg_resources.py2_warn',
            str(Path(CWD, 'wakatime', 'wakatime-cli.py')),
        ]
    elif tool == 'nuitka':
        hidden_folder = Path(inspect.getfile(Lexer.__class__)).resolve().parent.joinpath('lexers')
        extra_args = ['--include-module=pygments.lexers.' + x.stem for x in hidden_folder.iterdir() if x.suffix == '.py']
        return [
            'python',
            '-m',
            'nuitka',
            '--standalone',
            '--follow-imports',
            '--include-plugin-files', str(Path('wakatime', 'languages', 'default.json').resolve()),
            '--include-plugin-files', str(Path('wakatime', 'languages', 'vim.json').resolve()),
            '--include-module', 'hashlib.md5',
            '--include-module', 'hashlib.sha1',
            '--include-module', 'hashlib.sha256',
            '--output-dir', str(Path(CWD, 'dist')),
            '--remove-output',
            '--show-modules',
        ] + extra_args + [str(Path(CWD, 'wakatime', 'wakatime-cli.py'))]


def main():
    tool = os.environ.get('BUILD_WAKA_USING') or 'pyinstaller'
    if tool not in ['pyinstaller', 'nuitka']:
        raise Exception('Invalid build tool: {}'.format(tool))

    print('{timestamp} Building standalone wakatime-{ver}-{os}-{arch} using {tool}'.format(
        timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        ver=ABOUT["__version__"],
        os=OS,
        arch=ARCH,
        tool=tool,
    ))
    start = datetime.utcnow()
    subprocess.run(build_command(tool), check=True)
    seconds = int((datetime.utcnow() - start).total_seconds())
    minutes = int(seconds // 60)

    print('{timestamp} Created standalone wakatime-{ver}-{os}-{arch} in {minutes} minute{mplural} {seconds} second{splural}.'.format(
        timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        ver=ABOUT["__version__"],
        os=OS,
        arch=ARCH,
        minutes=minutes,
        mplural='' if minutes == 1 else 's',
        seconds=seconds,
        splural='' if seconds == 1 else 's',
    ))

    distFolder = str(Path(CWD, 'dist'))
    if tool == 'nuitka':
        Path(distFolder, 'wakatime-cli.dist').rename(Path(distFolder, 'wakatime-cli'))
    zipfile = str(Path(distFolder, 'wakatime-cli'))
    make_archive(zipfile, 'zip', distFolder, 'wakatime-cli')
    zipfile = zipfile + '.zip'

    sha3 = hashlib.sha3_512()
    with open(zipfile, 'rb') as fh:
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

        shafile = str(Path(distFolder, 'wakatime-cli.zip.sha3-512'))
        with open(shafile, 'w') as fh:
            fh.write(sha3sum)

        s3_filename = '{os}-{arch}/{tool}/releases/wakatime-cli-{ver}-{os}-{arch}.zip'.format(
            ver=ABOUT["__version__"],
            os=OS,
            arch=ARCH,
            tool=tool,
        )
        client.upload_file(shafile, bucket, s3_filename + '.sha3-512', ExtraArgs={'ACL': 'public-read'})
        with open(zipfile, 'rb') as fh:
            client.upload_fileobj(fh, bucket, s3_filename, ExtraArgs={'ACL': 'public-read'})
        print('{timestamp} Uploaded artifact {filename} to s3.'.format(
            timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            filename=s3_filename,
        ))

        s3_filename = '{os}-{arch}/{tool}/wakatime-cli.zip'.format(
            os=OS,
            arch=ARCH,
            tool=tool,
        )
        client.upload_file(shafile, bucket, s3_filename + '.sha3-512', ExtraArgs={'ACL': 'public-read'})
        with open(zipfile, 'rb') as fh:
            client.upload_fileobj(fh, bucket, s3_filename, ExtraArgs={'ACL': 'public-read'})
        print('{timestamp} Uploaded artifact {filename} to s3.'.format(
            timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            filename=s3_filename,
        ))

        verfile = str(Path(distFolder, 'current_version.txt'))
        with open(verfile, 'w') as fh:
            fh.write(ABOUT["__version__"])
        s3_filename = '{os}-{arch}/{tool}/current_version.txt'.format(
            os=OS,
            arch=ARCH,
            tool=tool,
        )
        client.upload_file(verfile, bucket, s3_filename, ExtraArgs={'ACL': 'public-read'})
        print('{timestamp} Uploaded {filename} to s3.'.format(
            timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            filename=s3_filename,
        ))


if __name__ == '__main__':
    main()
