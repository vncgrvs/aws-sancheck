from setuptools import find_packages, setup


def read_requirements():
    with open("requirements.txt", "r") as req:
        content = req.read()
        requirements = content.split("\n")

    return requirements


setup(
    name="haws",
    version="0.1",
    url="https://github.com/vg-leanix/aws_sancheck",
    author="Vincent Groves",
    author_email="vincent.groves@leanix.net",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    entry_points="""
        [console_scripts]
        haws=haws.main:cli
    """,
)