#!/usr/bin/env python3

import argparse
import os.path
import re
from datetime import datetime
from subprocess import check_output, check_call

BASE_COMMIT='f7002429d43a92b4f65a91309a2adc6ed91cd952'

def update_version(path):
    """ Update version in the setup file """
    with open(path, 'r') as fh:
        version_re = re.compile('VERSION = *')
        lines = fh.readlines()
        for index, line in enumerate(lines):
            if version_re.match(line):
                old_version = line.split('=')[1].strip(' "\'').split('+')[0]
                major, minor, rev = old_version.split('.')
                rev = int(rev) + 1
                version = '{}.{}.{}'.format(major, minor, rev)
                lines[index] = 'VERSION = "{}+dev"'.format(version)
                update_setup = lines
                break
        else:
            raise ValueError('In the setup file {}, version is not found.'.format(path))

    if update_setup:
        with open(path, 'w') as fh:
            fh.writelines(update_setup)
    else:
        raise ValueError('No updated content for setup.py in {}.'.format(module_name))

    return old_version, version


def update_history(working_dir, old_version, new_version):
    path = os.path.join(working_dir, 'HISTORY.rst')
    with open(path,'r') as fq:
        lines = fq.readlines() 
    
    for index, line in enumerate(lines):
        if line.startswith('Release History'):
            begin = index + 2
        
        if old_version in line: 
            end = index
            break

    # get commits
    rev_range = '{}..HEAD'.format(BASE_COMMIT)
    commit_comments = check_output(['git', 'log', rev_range, '--pretty=format:"%s"', '--', working_dir, ":(exclude)*/tests/*"],
                                   cwd=working_dir).split(b'\n')
    commit_comments = set([bstr.decode('utf-8') for bstr in commit_comments])
    print('comments {}'.format(len(commit_comments)))

    for line in lines[begin: end]:
        if line.startswith('*'):
            commit_comments.add(line.lstrip(' *').strip())
    
    commit_comments = sorted([c for c in commit_comments if c])
    
    # form history
    release_notes = ['{} ({})\n'.format(new_version, datetime.utcnow().strftime('%Y-%m-%d')), '^^^^^^^^^^^^^^^^^^\n']

    if any(commit_comments): 
        for comment in commit_comments:
             release_notes.append('* {}\n'.format(comment.strip(' "')))
    else:
        release_notes.append('* no changes\n')
    release_notes.append('\n')
    
    updated_lines = lines[:begin] + release_notes + lines[end:]
    with open(path, 'w') as fq:
        fq.writelines(updated_lines)


def commit_changes(path, name, branch, version):
    commit_message = f'Release {name} {version}'
    check_call(['git', 'commit', '-am', commit_message], cwd=working_dir)
    check_call(['git', 'push', '-f', 'origin', branch], cwd=working_dir)


parser = argparse.ArgumentParser()
parser.add_argument('module_path', nargs='+', help='The path to the module for creating release pull request.')
args = parser.parse_args()

for path in args.module_path:
    if os.path.isfile(path) and os.path.basename(path) == 'setup.py':
        working_dir = os.path.abspath(os.path.dirname(path))
    else:
        raise ValueError('The path {} does not point to a setup.py file.'.format(path))

    module_name = os.path.basename(working_dir)

    if module_name == 'azure-cli-testsdk':
        continue

    check_call(['git', 'checkout', 'master'], cwd=working_dir)

    rev_range='{}..HEAD'.format(BASE_COMMIT)
    commits=check_output(['git', 'rev-list', rev_range, '.'], cwd=working_dir).split()

    if not any(commits) and module_name not in ('azure-cli', 'azuer-cli-core'):
        print('Skip {} since there is not commits since {}'.format(module_name, BASE_COMMIT))
        continue

    try:
        branch_name = 'release-' + module_name
        check_call(['git', 'checkout', '-b', branch_name], cwd=working_dir)
        old_version, new_version = update_version(path)
        update_history(working_dir, old_version, new_version)
        commit_changes(working_dir, module_name, branch_name, new_version)
    except ValueError:
        check_call(['git', 'checkout', '.'], cwd=working_dir)
        check_call(['git', 'checkout', 'master'], cwd=working_dir)
        check_call(['git', 'branch', '-D', 'release-' + module_name], cwd=working_dir)
