#!/usr/bin/python

###############################################################################
# NAME: pyp_test.py
# VERSION: 3.0.0 (2DECEMBER2025)
# AUTHOR: John B. Cole (john.b.cole@gmail.com)
# LICENSE: LGPL v2.1 (see LICENSE file)
###############################################################################
# FUNCTIONS:
#   test_pyp_newclasses_load_pedigree()
###############################################################################

# @package pyp_test
# pyp_test contains procedures for testing various PyPedal functions.


import logging
import numpy as np
import pandas as pd
from PyPedal import pyp_io
from PyPedal import pyp_network
from PyPedal import pyp_newclasses
from PyPedal import pyp_nrm
from PyPedal import pyp_utils


##
# test_pyp_newclasses_load_pedigree() attempts to load the specified pedigree file and
# create a PyPedal pedigree object from it.
# @param options A dictionary of pedigree options, which includes a filename.
# @retval A PyPedal pedigree object on success, None on failure.
def test_pyp_newclasses_load_pedigree(pedigree_options):
    """
    read_agil_chromosome_data() loads SNP marker information from the chromosome.data file
    used by AGIL and CDCB. Note that this ONLY reads the first 5 columns (SNP name, chromosome
    number, within-chromosome marker number, overall marker number, and location in base pairs).
    """
    pedobj = None
    pedobj = pyp_newclasses.load_pedigree(pedigree_options)
    return pedobj


if __name__ == '__main__':

    print('Loading test_files/mrode.ped...')
    logging.info('Loading test_files/mrode.ped...')
    options = {
        'renumber': 0,
        'pedfile': 'test_files/mrode.ped',
        'pedformat': 'asd',
        'pedname': 'Mrode Pedigree Table 2.1',
        'pedigree_is_renumbered': 1,
        'messages': 'quiet',
    }
    result = test_pyp_newclasses_load_pedigree(options)
    assert result is not None, 'Unable to load mrode.ped!'
    print('\t[SUCCESS]: Loaded pedigree from test_files_mrode.ped.')
    assert result.metadata.num_records == 6, ('The pedigree contains %s instead of 6 animals!' %
                                                 result.metadata.num_records)
    print('\t[SUCCESS]: test_files/mrode.ped contains 6 unique animals, as expected.')
