import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "gerber-tools",
    version = "0.1",
    author = "Paulo Henrique Silva",
    author_email = "ph.silva@gmail.com",
    description = ("Utilities to handle Gerber (RS-274X) files."),
    license = "Apache",
    keywords = "gerber tools",
    url = "http://github.com/curtacircuitos/gerber-tools",
    packages=['gerber'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apple Public Source License",
    ],
)
