import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="apodo",
    version="0.1.0.dev",
    author="Elliott Maguire",
    author_email="me@elliott-m.com",
    description="A small example package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elliot-maguire/apodo",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
