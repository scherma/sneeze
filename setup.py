#!/usr/bin/env python
import os
import setuptools

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setuptools.setup(
    name = "sneeze",
    version = "0.1",
    author = "scherma",
    author_email = "fear.nothing@gmail.com",
    description = ("Watches a directory for unified2 files being updated,"
            " and pushes new events to a designated receiver."),
    license = "MIT",
    url = "https://github.com/scherma/sneeze",
    packages = ['sneeze'],
    package_dir = {'sneeze': 'src/sneeze'},
    entry_points={
        'console_scripts': ['sneeze = sneeze.__main__:main']
    },
    install_requires = [
        "requests",
        "watchdog",
        "unified2"
    ],
    long_description = read('README.rst'),
    classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: System Administrators',
    'Topic :: System :: Networking :: Monitoring',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Programming Language :: Python :: 2.7'
    ]
) 
