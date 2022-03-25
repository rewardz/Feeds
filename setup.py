# -*- encoding: utf-8 -*-
"""
Feeds
"""
import os
from setuptools import setup, find_packages
import feeds as app


dev_requires = [
    'flake8',
    'pip-tools',
    'pylint',
    'pylint-django',
    'freezegun',
    'requests-mock',
    'pep8',
]

install_requires = [
    "django",
    "djangorestframework",
    "Pillow",
    "django-filter",
    #"psycopg2>=2.9.1,<=2.9.3",
    "django-annoying",
    "django-tinymce",
    "django-taggit",
    "django-floppyforms",
    "django-image-cropping>=1.5.0,<=1.7",
    "easy-thumbnails",
    "django-photologue>=3.12,<=3.15.1",
    "memoized-property",
    "django-model-helpers>=1.2.1",
    "html2text>=2020.1.16",
    "pyOpenSSL",
    "ndg-httpsclient",
    'pyasn1',
    "cropimg-django @ git+https://github.com/rewardz/cropimg-django.git@0.5",
]


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''


setup(
    name="feeds",
    version=app.__version__,
    description=read('DESCRIPTION'),
    long_description=read('README.rst'),
    license='Private',
    platforms=['OS Independent'],
    keywords='django, app, reusable, rewardz, user, feeds',
    author='Piklu',
    author_email='piklu@rewardz.sg',
    url="https://",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'dev': dev_requires,
    },
)
