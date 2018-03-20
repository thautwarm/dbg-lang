from setuptools import setup, find_packages

with open('./README.rst', encoding='utf-8') as f:
    readme = f.read()

setup(name='dbglang',
      version='0.1',
      keywords='orm, dsl',
      description='a declarative dsl for db-orm',
      long_description=readme,
      license='MIT',
      url='https://github.com/thautwarm/dbg-lang',
      author='thautwarm',
      author_email='twshere@outlook.com',
      include_package_data=True,
      packages=['dbglang'],
      entry_points={
          'console_scripts': {
              'dbgc=dbglang.__main__:main'}
      },
      install_requires=[
          'EBNFParser==1.1'
      ],
      platforms='any',
      classifiers=[
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: Implementation :: CPython'],
      zip_safe=False)
