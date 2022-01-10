import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 7):
    sys.exit('ERROR: sb requires Python 3.7+')

setup(
    name='serverless-benchmarker',
    version='0.3.0',
    author='Anonymous',
    author_email='anonymous@gmail.com',
    url='https://github.com/anonymous/serverless-benchmarker',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # Generates sb CLI and SDK interfaces
        'fire>=0.4.0,<1',
        # YAML parser for sb config
        'PyYAML>=6.0,<7',
        # Deep merge for benchmark config
        'mergedeep>=1.3.4,<2',
        # Graph-based trace analysis
        'networkx>=2.6.3,<3',
        # peekable iterator for trace breakdown extraction
        'more-itertools>=8.12.0,<9',
        # Workload generation
        'stochastic==0.6.0',
        'pandas==1.3.5',
        # AWS
        'boto3>=1.20.26,<2',
        # Additional dependencies for certain benchmarks
        'requests>=2.26.0,<3',
        'scikit-image==0.19.1'
    ],
    # Install via pip install --editable .[dev]
    extras_require={
        'dev': [
            'pytest>=6.2.5,<7',
            'flake8>=4.0.1,<5'
        ]
    },
    entry_points='''
        [console_scripts]
        sb=sb.sb:main
    ''',
    python_requires='>=3.7',
)
