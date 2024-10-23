# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='crystalia-simple-collector',  # Required
    version='0.0.1',  # Required
    description='Simple Dataset metrics collector',
    author='Vlad Korolev',

    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Data Scientists',
        'Topic :: Data Science :: Provenance',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],

    packages=find_packages(where='.'),

    python_requires='>=3.6, <4',

    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['click'],  # Optional

    extras_require={  # Optional
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },

    entry_points={  # Optional
        'console_scripts': [
            'collect_ds_metrics=cmd_tool:collect_metrics',
            'convert_to_n3=cmd_tool:convert_to_n3',
        ],
    },
)
