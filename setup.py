from setuptools import setup

setup(name='cevent',
      version='0.0.1',
      description='Module for having functions get called at timed intervals, via threads',
      url='http://github.com/csm10495/cevent',
      author='csm10495',
      author_email='csm10495@gmail.com',
      license='MIT',
      packages=['cevent'],
      install_requires=[],
      python_requires='>=2.7, !=3.0.*, !=3.1.*',
      zip_safe=True,
    long_description="""\
Module for having functions get called at timed intervals via threads.
Check out http://github.com/csm10495/cevent for documentation.
""",
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],)