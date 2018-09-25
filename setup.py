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

"""A PEG-based query parser for INSPIRE."""

import os

from setuptools import find_packages, setup


URL = 'https://github.com/inspirehep/inspire-query-parser'

readme = open('README.rst').read()

setup_requires = [
    'autosemver',
]

install_requires = [
    'inspire-schemas~=58.0,>=58.0.0',
    'pypeg2~=2.0,>=2.15.2',
    'python-dateutil~=2.0,>=2.6.1',
    'six~=1.0,>=1.11.0',
],

docs_require = []

tests_require = [
    'flake8~=3.0,>=3.5.0',
    'mock~=2.0,>=2.0.0',
    'pytest-cov~=2.0,>=2.5.1',
    'pytest~=3.0,>=3.2.2',
]

extras_require = {
    'docs': docs_require,
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    extras_require['all'].extend(reqs)

packages = find_packages(exclude=['docs'])

setup(
    name='inspire-query-parser',
    autosemver={
        'bugtracker_url': URL + '/issues',
    },
    url=URL,
    license='GPLv3',
    author='CERN',
    author_email='admin@inspirehep.net',
    packages=packages,
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    description=__doc__,
    long_description=readme,
    setup_requires=setup_requires,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
