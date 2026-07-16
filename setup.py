from setuptools import setup, find_packages
from singular_api_client.version import __version__

setup(
    name='singular_api_client',
    version=__version__,
    py_modules=[],
    packages=find_packages(),
    description='Helper Library to use Singular Reporting API',
    long_description="""This is the official Singular Reporting API Python Library. This library allows easy BI integration of Singular.
For more information please visit our github repo: https://github.com/singular-labs/singular_api_client/""",
    url='https://github.com/singular-labs/singular_api_client/',
    download_url='https://github.com/singular-labs/singular_api_client/tarball/%s' % __version__,
    author="Singular Labs, Inc",
    license='Apache',
    author_email="devs@singular.net",
    keywords=[
        'singular'],
    project_urls={
        'Documentation': 'https://github.com/singular-labs/singular_api_client',
        'Source': 'https://github.com/singular-labs/singular_api_client',
        'Tracker': 'https://github.com/singular-labs/singular_api_client/issues',
    },
    install_requires=[
        'requests>=2.26.0',
        'urllib3>=1.26.0',
        'pytz',
        'retrying',
    ],
    python_requires='>=3.8',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ]
)