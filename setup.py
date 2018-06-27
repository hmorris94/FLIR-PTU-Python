import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="flirptu",
    version="0.0.1a2",
    author="Hunter Morris",
    author_email="hunterbmorris@gmail.com",
    description="Controller for FLIR E-series pan-tilt units",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="flir ptu pan-tilt",
    url="https://github.com/hmorris94/FLIR-PTU-Python",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        'Natural Language :: English',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: System :: Hardware",
    ),
    install_requires=["pyserial"],
    python_requires=">=3",
)
