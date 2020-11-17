import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="smartphone_connector",
    version="0.0.90",
    author="Balthasar Hofer",
    author_email="lebalz@outlook.com",
    description="Talk to a socketio server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lebalz/smartphone-connector",
    packages=setuptools.find_packages(),
    install_requires=[
        'python-socketio[client]',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
