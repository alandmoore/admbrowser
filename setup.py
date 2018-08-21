from setuptools import setup, find_packages

with open('README.rst', 'r') as fh:
    long_description = fh.read()

setup(
    name="ADM Browser",
    version="0.1",
    author="Alan D Moore",
    author_email='me@alandmoore.com',
    description=(
        'A browser designed for locked-down kiosk use,'
        ' based on QtWebEngine.'
    ),
    url="http://github.com/alandmoore/admbrowser",
    license='GPL v3',
    long_description=long_description,
    packages=find_packages(),
    install_requires=['PyQt5', 'python-yaml'],
    python_requires='>=3.5',
    entry_points={
        'console_scripts': [
            'admbrowser = admbrowser:main'
        ]}
)
