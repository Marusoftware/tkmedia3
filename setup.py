# -*- coding: utf-8 -*-
from os import path
import setuptools

root_dir = path.abspath(path.dirname(__file__))

def _requirements():
    return [name.rstrip() for name in open(path.join(root_dir, 'requirements.txt')).readlines()]

with open(path.join(root_dir, 'README.md'), "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tkmedia",
    version="0.1.1",
    author="Marusoftware",
    author_email="marusoftware@outlook.jp",
    description="Tkinter Media Support.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Marusoftware/tkmedia3",
    project_urls={
        "Bug Tracker": "https://github.com/Marusoftware/tkmedia3/issues",
        "Documents": "https://marusoftware.github.io/tkmedia3/"
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    packages=["media"],
    license="MIT",
    python_requires=">=3.8",
    install_requires=_requirements(),
    keywords='tkmedia',
)
