#!/usr/bin/env python3
from distutils.core import setup

setup(
    name='SiebenApp',
    version='0.13',
    description='An experimental dependency-aware goal manager',
    author='Andrey Hitrin',
    author_email='andrey.hitrin@gmail.com',
    url='https://github.com/ahitrin/SiebenApp',
    packages=['siebenapp', 'siebenapp.ui'],
    scripts=['clieben', 'sieben', 'sieben-manage'],
    install_requires=['PySide6'],
    include_package_data=True,
)
