#!/usr/bin/env python
try:
    from setuptools import setup

    args = {}
except ImportError:
    from distutils.core import setup

    print(
        """\
*** WARNING: setuptools is not found.  Using distutils...
"""
    )

from setuptools import setup

try:
    from pypandoc import convert

    read_md = lambda f: convert(f, "rst")
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, "r").read()

from os import path

setup(
    name="aflow",
    version="0.0.11-patched",
    description="Python API for searching AFLOW database. Forked from rosenbrockc/aflow",
    long_description="" if not path.isfile("README.md") else read_md("README.md"),
    author="Conrad W Rosenbrock",
    author_email="rosenbrockc@gmail.com",
    maintainer="T.Tian",
    maintainer_email="alchem0x2a@gmail.com",
    url="https://github.com/ulissigroup/aflow",
    license="MIT",
    setup_requires=[
        "pytest-runner",
    ],
    tests_require=["pytest", "python-coveralls"],
    install_requires=[
        "termcolor",
        "numpy",
        "six",
        # "jinja2",
        # "beautifulsoup4",
        "ase",
        "sympy",
    ],
    packages=["aflow"],
    scripts=[],
    package_data={"aflow": ["templates/*", "api/*.json"]},
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
