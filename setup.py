import os
import re
from setuptools import setup

requirements = [
    "requests>=2.26.0",
    "sshtunnel>=0.4.0",
    "furl>=2.1.3",
]

test_requirements = [
    "pytest>=6.2.5"
]

about = {}


pwd = os.path.dirname(__file__)

with open(os.path.join(pwd, 'sshtunnel_requests', '__init__.py')) as f:
  VERSION = (
      re.compile(r""".*__version__ = ["'](.*?)['"]""", re.S)
      .match(f.read())
      .group(1)
  )

setup(name='sshtunnel_requests',
      version=VERSION,
      url='https://github.com/featureoverload/sshtunnel-requests',
      project_urls={},
      author='Feature Overload',
      maintainer='Feature Overload',
      packages=['sshtunnel_requests'],
      package_data={'': ['LICENSE', ]},
      package_dir={'sshtunnel_requests': 'sshtunnel_requests'},
      # description='',
      include_package_data=True,
      zip_safe=False,
      python_requires='>=3.8',
      install_requires=requirements)
