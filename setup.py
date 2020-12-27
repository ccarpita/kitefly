
# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

readme = ''

setup(
    long_description=readme,
    name='kitefly',
    version='0.1.0',
    description='Dynamically generate Buildkite pipeline files with highly composable python models',
    python_requires='!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,<4.0,>=2.7',
    author='Chris Carpita',
    author_email='ccarpita@gmail.com',
    license='MIT',
    packages=['kitefly'],
    package_dir={"": "."},
    package_data={},
    install_requires=['pyyaml==5.*,>=5.3.1'],
    extras_require={"dev": ["pytest==4.*,>=4.6.0"]},
)
