# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name = 'prog_models',
    version = '1.1.0', #pkg_resources.require("prog_models")[0].version,
    description = 'The NASA Prognostic Model Package is a python modeling framework focused on defining and building models for prognostics (computation of remaining useful life) of engineering systems, and provides a set of prognostics models for select components developed within this framework, suitable for use in prognostics applications for these components.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url = 'https://github.com/nasa/prog_models',
    author = 'Christopher Teubert',
    author_email = 'christopher.a.teubert@nasa.gov',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Intended Audience :: Manufacturing', 
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: Other/Proprietary License ',   
        'Programming Language :: Python :: 3',     
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only'
    ],
    keywords = ['prognostics', 'diagnostics', 'fault detection', 'fdir', 'physics modeling', 'prognostics and health management', 'PHM', 'health management'],
    package_dir = {"":"src"},
    packages = find_packages(where = 'src'),
    python_requires='>=3.6, <3.10',
    install_requires = [
        'numpy',
        'scipy',
        'matplotlib'
    ],
    license = 'NOSA',
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/nasa/prog_models/issues',
        'Organization': 'https://prognostics.nasa.gov/',
        'Source': 'https://github.com/nasa/prog_models',
    },
)
