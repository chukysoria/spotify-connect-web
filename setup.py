from __future__ import unicode_literals

import re


from setuptools import find_packages, setup


def read_file(filename):
    with open(filename) as fh:
        return fh.read()


def get_version(filename):
    init_py = read_file(filename)
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", init_py))
    return metadata['version']


def md_to_rst(filename):
    try:
        import pypandoc
        long_description = pypandoc.convert(filename, 'rst')
    except(IOError, ImportError):
        long_description = read_file(filename)
    return long_description

setup(
    name='spotifyconnect-web',
    version=get_version('scweb/__init__.py'),
    url='https://github.com/chukysoria/spotify-connect-web',
    license='Apache License, Version 2.0',
    author='chukysoria',
    author_email='nomail@nomail.com',
    description='Console and web client for Spotify Connect',
    long_description=md_to_rst('README.md'),
    keywords='spotify connect player client',
    packages=find_packages(exclude=['tests', 'tests.*']),
    test_suite="tests",
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'Flask >= 0.10.1',
        'Flask-Bootstrap >= 3.3.2.1',
        'Flask-Cors >= 2.1.2',
        'pyalsaaudio >= 0.8',
        'pyspotify-connect >= 0.1.11',
        'six >= 1.10.0'],
    entry_points={
        'console_scripts': [
            'spotifyconnect = scweb.__main__:main',
            'spotifyconnect-web = scweb.__main__:main_web'
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Environment :: Console',
        'Framework :: Flask',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
