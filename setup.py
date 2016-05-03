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


setup(
    name='sc-console',
    version='0.0.1',
    url='https://github.com/chukysoria/spotify-connect-web',
    license='Apache License, Version 2.0',
    author='chukysoria',
    author_email='nomail@nomail.com',
    description='Implementation of libspotify-connect',
    long_description=read_file('README.md'),
    keywords='spotify connect library',
    packages=find_packages(exclude=['tests', 'tests.*']),
    test_suite="tests",
    zip_safe=False,
    include_package_data=True,
    setup_requires=[
        'pytest-runner'],
    tests_require=['pytest'],
    install_requires=[
        'Flask >= 0.10.1',
        'Flask-Bootstrap >= 3.3.2.1',
        'Flask-Cors >= 2.1.2',
        'pyalsaaudio >= 0.8',
        'pyspotify-connect >= 0.1.0',
        'six >= 1.10.0'],
    entry_points={
        'console_scripts': [
            'spotifyconnect = sc_console.__main__:main',
            'spotifyconnect-web = sc_console.__main__:main_web'
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
    ],
)
