import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="confr",
    version="0.1.0",
    author="Mattias Arro",
    author_email="mattias.arro@gmail.com",
    description="Configuration system geared towards Python / machine learning projects.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mattiasarro/confr",
    project_urls={
        "Bug Tracker": "https://github.com/mattiasarro/confr/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        "aiocontextvars>=0.2.2",
    ]
)
