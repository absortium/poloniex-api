import os

from setuptools import setup, find_packages
from pip.req import parse_requirements

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

# read requirements from requirements.txt
install_reqs = [str(ir.req) for ir in parse_requirements('requirements.txt', session=False)]

PACKAGES = find_packages(exclude=['tests'])

setup(
    name='poloniex',
    version='0.1',
    packages=PACKAGES,
    include_package_data=True,
    description='Python Poloniex API',
    long_description=README,
    url='https://github.com/AndrewSamokhvalov/poloniex.git',
    author='Andrey Samokhvalov',
    author_email='andrew.shvv@gmail.com',
    install_requires=install_reqs,
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
    ],
)
