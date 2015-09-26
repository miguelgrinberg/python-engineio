"""
python-engineio
---------------

Engine.IO server.
"""
from setuptools import setup


with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='python-engineio',
    version='0.6.7',
    url='http://github.com/miguelgrinberg/python-engineio/',
    license='MIT',
    author='Miguel Grinberg',
    author_email='miguelgrinberg50@gmail.com',
    description='Engine.IO server',
    long_description=long_description,
    packages=['engineio'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'six>=1.9.0',
    ],
    tests_require=[
        'mock',
        'eventlet',
        'pbr<1.7.0',   # temporary, to workaround bug in 1.7.0
    ],
    test_suite='tests',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
