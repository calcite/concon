#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages
import os

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'PyYAML>=3.11'
]

if os.name == "nt":
    requirements.append('pywinusb>=0.3.2')
else:
    requirements.append('pyusb==1.0.0')

setup_requirements = [
    # TODO(JNev): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='concon',
    version='0.9.0',
    description="Universal configuration tool for USB devices implementing the Uniprot (HID) communication layer.",
    long_description=readme + '\n\n' + history,
    author="Martin Stejskal",
    author_email='mstejskal@alps.cz',
    url='https://github.com/JNev/concon',
    packages=find_packages(include=['concon']),
    entry_points={
        'console_scripts': [
            'concon=concon.cli:main'
        ]
    },
    include_package_data=True,
    package_data={'concon': ['config/*.*']},
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='concon',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
