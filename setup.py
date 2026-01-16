import re
import sys

from setuptools import find_packages, setup

if sys.version_info < (3, 10):
    raise SystemError('This package requires Python 3.10 or above.')


def get_version():
    """Read version from drf_social_oauth2/__init__.py without importing."""
    with open('drf_social_oauth2/__init__.py') as f:
        content = f.read()
    match = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", content, re.MULTILINE)
    if match:
        return match.group(1)
    raise RuntimeError('Unable to find version string.')


setup(
    name='drf-social-oauth2',
    version=get_version(),
    description='OAuth2 social authentication for Django REST Framework',
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
    package_data={
        'drf_social_oauth2': ['py.typed'],
    },
    include_package_data=True,
    zip_safe=False,
)
