from setuptools import setup

setup(
    name="wgha",
    version="1.0",
    py_modules=["main"],
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "wgha=main:main"
        ]
    },
)
