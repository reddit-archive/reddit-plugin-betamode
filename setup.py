#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name='reddit_betamode',
    description='beta testing mode for apps',
    version='0.1',
    author='Max Goodman',
    author_email='max@reddit.com',
    license='BSD',
    packages=find_packages(),
    install_requires=[
        'r2',
    ],
    entry_points={
        'r2.plugin':
            ['betamode = reddit_betamode:BetaMode'],
    },
    include_package_data=True,
    zip_safe=False,
)
