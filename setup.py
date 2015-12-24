#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import re

try:
    import setuptools
    setup = setuptools.setup
except ImportError:
    setuptools = None
    from distutils.core import setup


packages = [
    'qiniu4tornado',
    'qiniu4tornado.services',
    'qiniu4tornado.services.storage',
    'qiniu4tornado.services.processing',
]


def read(*names, **kwargs):
    return io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ).read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='qiniu4tornado',
    version=find_version("qiniu4tornado/__init__.py"),
    description='Qiniu Resource Storage SDK',
    long_description='see:\nhttps://github.com/qiniu4tornado/python-sdk\n',
    author='Shanghai Qiniu Information Technologies Co., Ltd.',
    author_email='sdk@qiniu4tornado.com',
    maintainer_email='support@qiniu4tornado.com',
    license='MIT',
    url='https://github.com/qiniu4tornado/python-sdk',
    platforms='any',
    packages=packages,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    install_requires=['requests'],

    entry_points={
        'console_scripts': [
            'qiniupy = qiniu4tornado.main:main',
        ],
    }
)
