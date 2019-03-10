#  openei-rates

<!-- .. image:: https://img.shields.io/pypi/v/openei_rates.svg
        :target: https://pypi.python.org/pypi/openei_rates

.. image:: https://img.shields.io/travis/accurrently/openei_rates.svg
        :target: https://travis-ci.org/accurrently/openei_rates

.. image:: https://readthedocs.org/projects/openei-rates/badge/?version=latest
        :target: https://openei-rates.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status
-->

A Python package that retrieves energy rates from [OpenEI.org](https://openei.org) for use in energy data applications.

## Overview

This package has one main purpose: to fetch electrical utility rates from OpenEI's database and provide facilities to query those rate structures to determine the cost of operating equipment. This is accomplished through Pandas, and Numpy. Numba is employed in order to speed lookups of rate information in Numba arrays.


## Features

This package is supposed to do x things:

1. Retrieve of rates from [OpenEI.org](https://openei.org)
2. Load appropriate rate data into Numpy arrays for querying
3. Provide efficient lookups of energy and power prices given a timestamp and quantity of power (or energy) used.
4. Allow pricing analysis on power demand (in kW) stored in a `pandas.Series` that has a `pandas.DatetimeIndex` index.

## Credits


This project was produced with funding from the [UC Davis Energy Graduate Group](https://energy.ucadavis.edu), the [UC Davis Plug-in Hybrid and Electric Vehicle Research Center](https://phev.ucdavis.edu), and [Office of Naval Research NEPTUNE](https://www.onr.navy.mil/en/Science-Technology/Departments/Code-33/All-Programs/333-sea-platforms-weapons/Neptune)

<!-- This is nice, but it doesn't need to be seen ;)
This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.
-->

## License

Free software: Apache Software License 2.0. See LICENSE for more information.

<!-- * Documentation: https://openei-rates.readthedocs.io. -->

<!-- _Cookiecutter: https://github.com/audreyr/cookiecutter -->
<!-- _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage -->
