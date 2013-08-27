import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

version = '0.1'

setup(name='nva.mq',
      version=version,
      description='transaction-aware sending of amqp messages',
      long_description=README + "\n\n" + CHANGES,
      classifiers=[
        ],
      keywords='transaction amqp kombu',
      author="Christian Klinger",
      author_email="info@novareto.de",
      url="http://www.novareto.de",
      license="ZPL",
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      namespace_packages=['nva'],
      zip_safe=False,
      install_requires=[
          'transaction',
          'kombu',
          'grokcore.component',
          'setuptools',
          ],
      test_suite = "nva.mq",
      )
