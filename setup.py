import os
import re

from setuptools import setup

PWD = os.path.dirname(__file__)

with open(os.path.join(PWD, 'sshtunnel_requests', '__init__.py')) as f:
    VERSION = (re.compile(r""".*__version__ = ["'](.*?)['"]""",
                          re.S).match(f.read()).group(1))


def parse_requirements_file(filename):
    with open(filename) as fid:
        requires = [l.strip() for l in fid.readlines() if not l.startswith("#")]

    return requires


# base requirements
install_requires = parse_requirements_file('requirements.txt')
test_requires = parse_requirements_file('requirements_test.txt')
docs_requires = parse_requirements_file('requirements_doc.txt')

extras = {
    "test": test_requires,
    "docs": docs_requires,
}

extras["all"] = sum(extras.values(), [])


setup(
    name='sshtunnel_requests',
    version=VERSION,
    url='https://github.com/featureoverload/sshtunnel-requests',
    project_urls={
        "Documentation": "https://sshtunnel-requests.readthedocs.io/en/latest/",
        "Source": "https://github.com/featureoverload/sshtunnel-requests",
        "Tracker": "https://github.com/featureoverload/sshtunnel-requests/issues",
    },
    author='Feature Overload',
    author_email='featureoverload@gmail.com',
    maintainer='Feature Overload',
    maintainer_email='featureoverload@gmail.com',
    packages=['sshtunnel_requests'],
    package_data={'': ['LICENSE', ]},
    package_dir={'sshtunnel_requests': 'sshtunnel_requests'},
    description='a simple HTTP library to port forward requests on SSH tunnels to remove server',
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=install_requires,
    extras_require=extras,
)
