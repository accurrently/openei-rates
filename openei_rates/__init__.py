# -*- coding: utf-8 -*-

"""Top-level package for openei-rates."""

__author__ = """Alex Campbell"""
__email__ = 'amcampbell@ucdavis.edu'
__version__ = '0.1.0'


__all__ = [
    "rateschedule",
    "rate",
    "api",
    "openei_rates",
]

import logging
import os
 
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

logger = logging.getLogger(__name__)




