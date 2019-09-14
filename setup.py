from setuptools import setup, find_packages

setup(
    name='dark-shell',
    version='0.7',
    packages=find_packages(),
    url='https://github.com/Nahnahchi/dark-shell',
    license='GNU GENERAL PUBLIC LICENSE',
    author='Nahnahchi',
    author_email='sawalozb@gmail.com',
    description='A command line tool for testing and debugging DARK SOULS - Prepare to Die Edition',
    python_requires=">=3.7",
    install_requires=[
        "prompt-toolkit>=3.0.0", "psutil", "pywin32"
    ],
    dependency_links=[
        "https://github.com/prompt-toolkit/python-prompt-toolkit/tarball/master#egg=prompt-toolkit-3.0.0"
    ]
)
