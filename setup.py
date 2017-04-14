#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

name_ = 'aboutdb'
version_ = '0.1.0'
packages_ = [
    'aboutdb',
]

classifiers = [
    "Development Status :: 1 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
]

setup(
    name=name_,
    version=version_,
    author='Johan Egneblad',
    author_email='johan@DELETEMEegneblad.se',
    description='',
    license="MIT",
    url='https://github.com/eblade/'+name_,
    download_url=('https://github.com/eblade/%s/archive/v%s.tar.gz'
                  % (name_, version_)),
    packages=packages_,
    install_requires=[
    ],
    classifiers=classifiers,
)
