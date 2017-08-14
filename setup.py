import os
from setuptools import find_packages, setup
from yamdl import __version__


# We use the README as the long_description
readme_path = os.path.join(os.path.dirname(__file__), "README.rst")


setup(
    name='yamdl',
    version=__version__,
    url='http://github.com/andrewgodwin/yamdl/',
    author='Andrew Godwin',
    author_email='andrew@aeracode.org',
    description='Flat-file model instances for Django',
    long_description=open(readme_path).read(),
    license='BSD',
    zip_safe=False,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=[
        'Django>=1.11',
    ],
)
