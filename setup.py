import os
from setuptools import setup

# run python setup.py sdist
# check out MANIFEST.in for files to include

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-plupload',
    version='1.0.1',
    packages=['plupload'],
    include_package_data=True,
    license='BSD License',
    description='An integration of Plupload with Django, for use with file-based model and form fields.',
    long_description=README,
    url='https://bitbucket.org/amoretti/django-plupload',
    author='Alessio Moretti',
    author_email='',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)

