from setuptools import setup, find_packages
import sys

if sys.version_info < (3, 5):
    raise SystemError('This package is for Python 3.5 and above.')

setup(
    name='drf-social-oauth2',
    version=__import__('drf_social_oauth2').__version__,
    description=__import__('drf_social_oauth2').__doc__,
    long_description=open('README.rst').read(),
    author='Wagner de Lima',
    author_email='waglds@gmail.com',
    url='https://github.com/wagnerdelima/drf-social-oauth2',
    license='MIT',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'djangorestframework>=3.10.3',
        'django-oauth-toolkit>=0.12.0',
        'social-auth-app-django>=3.1.0',
        'python-jose[cryptography]>=3.2.0',
    ],
    include_package_data=True,
    zip_safe=False,
)
