#!/usr/bin/env python3

import argparse
import os
import re
import json


def get_version(path):
    with open(path, 'r') as fh:
        version_re = re.compile('VERSION = *')
        lines = fh.readlines()
        for index, line in enumerate(lines):
            if version_re.match(line):
                version = line.split('=')[1].strip(' "\'').split('+')[0]
                return version
        else:
            raise ValueError('In the setup file {}, version is not found.'.format(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('module_path', nargs='+', help='The path to the module for creating release pull request.')
    parser.add_argument('--version', help='The release version.')
    args = parser.parse_args()

    versions = {}   
    for path in args.module_path:
        if os.path.isfile(path) and os.path.basename(path) == 'setup.py':
            working_dir = os.path.abspath(os.path.dirname(path))
        else:
            raise ValueError('The path {} does not point to a setup.py file.'.format(path))

        module_name = os.path.basename(working_dir)
        
        if module_name != 'azure-cli-testsdk':
            versions[module_name] = get_version(path)
    
    with open('cli-components.json', 'w') as fp:
        print(json.dump(versions, fp, indent='  ', sort_keys=True))
