from setuptools import find_packages, setup


def read_requirements():
    with open("requirements.txt", "r") as req:
        content = req.read()
        requirements = content.split("\n")

    return requirements


setup(
    name="haws",
    description="A Python CLI to sanity check the AWS setup for LeanIX Cloud Intelligence Scans",
    version="1.0.9",
    url="https://github.com/vg-leanix/aws_sancheck",
    author="Vincent Groves",
    author_email="vincent.groves@leanix.net",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Customer Service",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License"


    ],
    python_requires='>=3.5',
    include_package_data=True,
    install_requires=read_requirements(),
    entry_points="""
        [console_scripts]
        haws=haws.main:cli
    """,
    license='Apache 2.0'
)
