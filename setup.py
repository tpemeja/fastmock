from setuptools import setup, find_packages

setup(
    name="fastmock",
    version="0.1.0",
    author="Tanguy PEMEJA",
    author_email="tanguy.pemeja@gmail.com",
    description="FastAPI middleware for mocking responses based on Pydantic models response",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tpemeja/fastmock",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10'
)


