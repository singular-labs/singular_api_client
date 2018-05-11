from setuptools import setup
from singular_api_client import __version__

setup(
    name='singular_api_client',
    version=__version__,
    py_modules=['singular_api_client'],
    packages=['singular_api_client'],
    description='Helper Library to use Singular Reporting API',
    author='Ruby Feinstein',
    url='https://github.com/singular-labs/singular_api_client/',
    download_url='https://github.com/singular-labs/singular_api_client/tarball/%s' % __version__,
    keywords=[
        'singular'],
    install_requires=[
        'requests',
    ])