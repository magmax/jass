# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from setuptools import setup, find_packages, Command
from setuptools.command.test import test as TestCommand
from jass import __version__


def read_description():
    with open('README.rst') as fd:
        return fd.read()


class PyTest(TestCommand):
    user_options = [
        ('pytest-args=', 'a', "Arguments to pass to py.test"),
    ]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ['--cov-report=term-missing']

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args or ['--cov-report=term-missing'])
        sys.exit(errno)


setup(name='jass',
      version=__version__,
      description="",
      long_description=read_description(),
      cmdclass = {'test': PyTest},
      classifiers=[
          'Development Status :: 1 - Planning',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Topic :: Software Development :: Code Generators',
      ],
      keywords='static site',
      author='Miguel Ángel García',
      author_email='miguelangel.garcia@gmail.com',
      url='https://github.com/magmax/jass',
      license='MIT',
      packages=find_packages(exclude=['tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'peewee',
          'yapsy',
          'jinja2',
          'colorlog',
      ],
      tests_require=[
          'pytest',
          'pytest-cov',
      ],
      setup_requires=[
          'flake8',
      ],
      extras_require = {
        'markdown':  ["markdown"],
      }
)
