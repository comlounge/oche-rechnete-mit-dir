from setuptools import setup, find_packages
import sys, os

version = '0.9'

setup(name='aachen-haushalt',
      version=version,
      description="Aufbereitung Aachener Haushaltsbefragung",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='COM.lounge',
      author_email='info@comlounge.net',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        "starflyer",
        "mechanize",
        "pymongo",
        "BeautifulSoup"
      ],
      entry_points="""
        [starflyer.config]
        default = haushalt.web.setup:setup
        [paste.app_factory]
        main = starflyer:run
      """,
      )
