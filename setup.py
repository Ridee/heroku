# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from setuptools import setup

with open('requirements.txt') as f:
    reqs = f.readlines()

setup(
    name='heroku',
    description='Heroku API wrapper',
    author='Javier Domingo Cansino',
    author_email='javier@jinnapp.com',
    py_modules=['heroku'],
    install_requires=reqs,
    include_package_data=True,
    zip_safe=False
)
