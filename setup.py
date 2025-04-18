from setuptools import setup, find_packages

setup(
    name="rob-1",
    version="1.0.0",
    description="Un robot assistant pour interagir avec des APIs.",
    author="Votre Nom",
    author_email="votre.email@example.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "charset_normalizer",
        "PyYAML",
        "tkinter"
    ],
    entry_points={
        "console_scripts": [
            "rob-1=main:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)