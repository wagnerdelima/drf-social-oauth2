import sys

from setuptools import find_packages, setup

if sys.version_info < (3, 10):
    raise SystemError('This package requires Python 3.10 or above.')

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
    python_requires='>=3.10',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
        'Framework :: Django :: 5.1',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Natural Language :: English',
    ],
    install_requires=[
        'djangorestframework>=3.14.0',
        'django-oauth-toolkit>=2.0.0',
        'social-auth-app-django>=5.0.0',
        'PyJWT>=2.8.0'
    ],
    include_package_data=True,
    zip_safe=False,
)
