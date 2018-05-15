from setuptools import setup, find_packages
from singular_api_client.version import __version__

setup(
    name='singular_api_client',
    version=__version__,
    py_modules=[],
    packages=find_packages(),
    description='Helper Library to use Singular Reporting API',
    author='Ruby Feinstein',
    url='https://github.com/singular-labs/singular_api_client/',
    download_url='https://github.com/singular-labs/singular_api_client/tarball/%s' % __version__,
    keywords=[
        'singular'],
    project_urls={
        'Documentation': 'https://github.com/singular-labs/singular_api_client',
        'Source': 'https://github.com/singular-labs/singular_api_client',
        'Tracker': 'https://github.com/singular-labs/singular_api_client/issues',
    },
    install_requires=[
        'requests',
        'pytz',
        'retrying',
        'futures'
    ])