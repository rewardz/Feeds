# -*- encoding: utf-8 -*-
"""
Python setup file for the rewardz_user_importer app.

In order to register your app at pypi.python.org, create an account at
pypi.python.org and login, then register your new app like so:

    python setup.py register

If your name is still free, you can now make your first release but first you
should check if you are uploading the correct files:

    python setup.py sdist

Inspect the output thoroughly. There shouldn't be any temp files and if your
app includes staticfiles or templates, make sure that they appear in the list.
If something is wrong, you need to edit MANIFEST.in and run the command again.

If all looks good, you can make your first release:

    python setup.py sdist upload

For new releases, you need to bump the version number in
rewardz_user_importer/__init__.py and re-run the above command.

For more information on creating source distributions, see
http://docs.python.org/2/distutils/sourcedist.html

"""
import os
from setuptools import setup, find_packages
import rewardz_user_importer as app


dev_requires = [
    'flake8',
]

install_requires = open('requirements.txt').read().splitlines()


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
    dependency_links=[
        "git+https://github.com/rewardz/cropimg-django.git@0f705fa0259dd2ab4e0c3c070ab92e50c8e9ba06#egg=cropimg-django"
    ],
)
