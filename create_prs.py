#!/usr/bin/env python3

import argparse
import os.path
import re
from datetime import datetime
from subprocess import check_output, check_call, CalledProcessError

parser = argparse.ArgumentParser()
parser.add_argument('src', help='The path to root folder for the source repo.')
args = parser.parse_args()

branches = [b.decode('utf-8').strip() for b in check_output(['git', 'branch'], cwd=args.src).split(b'\n')]
branches = [b for b in branches if b.startswith('release')]

for b in branches:
    check_call(['git', 'checkout', b], cwd=args.src)
    message = check_output(['git', 'log', '-1', '--pretty=format:%s'], cwd=args.src)
    try:
        check_call(['hub', 'pull-request', '-m', message, '-b', 'Azure/azure-cli:master'], cwd=args.src)
    except CalledProcessError:
        pass

check_call(['git', 'checkout', 'master'], cwd=args.src)