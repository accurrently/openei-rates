# -*- coding: utf-8 -*-

"""Top-level package for openei-rates."""

__author__ = """Alex Campbell"""
__email__ = 'amcampbell@ucdavis.edu'
__version__ = '0.1.0'


from .rateschedule import *
from .api import *
from .openei_rates import *

import logging
import os
 
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

logger = logging.getLogger(__name__)




