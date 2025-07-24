from setuptools import find_packages, setup

setup(
    name="sona",
    version="0.8.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["lark-parser"],
    entry_points={
        "console_scripts": [
            "sona = sona.sona_cli:main",
        ],
    },
    package_data={"sona": ["grammar.lark", "License.mdc", "stdlib/*.py"]},
)
