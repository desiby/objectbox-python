import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="objectbox",
    version="0.1.0",
    author="ObjectBox",
    description="ObjectBox is a superfast database for objects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/objectbox/objectbox-python",
    packages=setuptools.find_packages(),
    python_requires='>=3.4, <4',
    license='Apache 2.0',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: C",
        "Programming Language :: C++",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Database :: Front-Ends",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],

)
