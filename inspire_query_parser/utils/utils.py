# coding=utf-8
from __future__ import print_function

import sys


class Colors(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


if sys.version_info[0] == 3:  # pragma: no cover (Python 2/3 specific code)
    string_types = str,
else:  # pragma: no cover (Python 2/3 specific code)
    string_types = basestring,
