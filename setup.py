# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2014-2017 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""A PEG-based query parser for INSPIRE"""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()

tests_require = [
    'coverage>=4.4',
    'isort>=4.2.2',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-flake8>=0.8.1',
    'pytest>=2.8.0',
    'six>=1.10.0'
]

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'tests': tests_require,
    'all': []
}

for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
    'autosemver',
]

packages = find_packages(exclude=['docs'])

url = 'https://github.com/inspirehep/inspire-query-parser'

setup(
    name='inspire-query-parser',
    description=__doc__,
    long_description=readme,
    keywords='inspirehep query parser',
    license='GPLv3',
    author='CERN',
    author_email='admin@inspirehep.net',
    url=url,
    packages=packages,
    autosemver={'bugtracker_url': url + '/issues'},
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    extras_require=extras_require,
    install_requires=[
        'pypeg2>=2.15.2',
        'six>=1.10.0',
        'python-dateutil>=2.6.1',
    ],
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Development Status :: 2 - Pre-Alpha',
    ],
)
