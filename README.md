![Oxford Nanopore Technologies logo](images/ONT_logo_590x106.png)

Pomoxis - bioinformatics tools for nanopore research 
====================================================

[![Build Status](https://travis-ci.org/nanoporetech/pomoxis.svg?branch=master)](https://travis-ci.org/nanoporetech/pomoxis)

Pomoxis comprises a set of basic bioinformatic tools tailored to nanopore
sequencing. Notably tools are included for generating and analysing draft
assemblies. Many of these tools are used by the research data analysis
group at Oxford Nanopore Technologies.

Documentation can be found at https://nanoporetech.github.io/pomoxis/.

Features
--------

 * Wraps third party tools with known good default parameters
   and methods of use.
 * Creates an isolated environment with all third-party tools.
 * Streamlines common short analysis chains.
 * Includes a nanopore read simulator.
 * Server/client components for minimap2 and bwa.
 * Integrates into [katuali](https://github.com/nanoporetech/katuali)
   for performing more complex analysis pipelines.
 * Open source (Mozilla Public License 2.0).


Compatibility
-------------

Pomoxis is developed on Ubuntu 16.04, other recent linuxes should be
equally compatible (see build notes below). Pomoxis is known to work on
at least some MacOS High Sierra configurations, though some components,
notably scrappy, are known to not work on some MacOS configurations
(combinations of OS and xcode versions).


Installation
------------

Pomoxis will install itself into a an isolated virtual environment. The
installation will fetch, compile, and install all direct dependencies into the
environment.

> Before installing pomoxis is may be required to install some prerequisite
> packages, best installed by a package manager. On Ubuntu these are:
> * gcc-4.9
> * g++-4.9
> * zlib1g-dev
> * libncurses5-dev
> * python3-all-dev
> * libhdf5-dev
> * libatlas-base-dev
> * libopenblas-base
> * libopenblas-dev
> * libbz2-dev
> * liblzma-dev
> * libffi-dev
> * make
> * python-virtualenv
> * cmake (for racon)
> * wget (for fetching modules from github)
> * bzip2 (for extracting those modules)

To setup the environment run:

    git clone --recursive https://github.com/nanoporetech/pomoxis
    cd pomoxis
    make install
    . ./venv/bin/activate
    

The installation of porechop (https://github.com/rrwick/Porechop)
requires a newer compiler than is a available on some systems. It may therefore
be necessary to install a newer compiler and set environment variables before
the `make install` step:

    # For porechop to be compiled on older systems set these, e.g.:
    export CXX="g++-4.9" CC="gcc-4.9"

Note also that racon requires at least `gcc>=4.8.5` to
[compile smoothly](https://github.com/isovic/racon/issues/57).


**Alternative Installation Methods**

Running the above within a pre-exisiting virtual environnment may well fail;
advanced may wish to simply run the `setup.py` file in the standard manner
after compiling the third party programs as in the `Makefile`.
[thomcuddihy](https://github.com/thomcuddihy) has
[sketched](https://github.com/nanoporetech/pomoxis/issues/19#issuecomment-433255390)
how to use pomoxis within a conda enviroment.


Extras
------

The distribution bundles some common bioinformatics tools:

* miniasm
* minimap2
* racon
* bwa
* samtools
* porechop

These will be compiled and installed into the virtual environment created as above.
