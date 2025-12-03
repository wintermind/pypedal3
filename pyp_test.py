#!/usr/bin/python

###############################################################################
# NAME: pyp_test.py
# VERSION: 3.0.0 (2DECEMBER2025)
# AUTHOR: John B. Cole (john.b.cole@gmail.com)
# LICENSE: LGPL v2.1 (see LICENSE file)
###############################################################################
# FUNCTIONS:
#   test_pyp_newclasses_load_pedigree()
#   test_pyp_nrm_a_matrix()
#   test_pyp_nrm_fast_a_matrix()
#   test_pyp_nrm_fast_a_matrix_r()
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
    test_pyp_newclasses_load_pedigree() attempts to load the specified pedigree file and
    create a PyPedal pedigree object from it.
    """
    pedobj = None
    pedobj = pyp_newclasses.load_pedigree(pedigree_options)
    return pedobj


##
# test_pyp_nrm_a_matrix() attempts to calculate the relationship matrix from the provided pedigree using
# pyp_nrn/a_matrix().
# @param pedigree A PyPedal pedigree object.
# @retval A PyPedal pedigree object on success, None on failure.
def test_pyp_nrm_a_matrix(pedigree):
    """
    test_pyp_nrm_a_matrix() attempts to calculate the relationship matrix from the provided pedigree using
    pyp_nrn/a_matrix().
    """
    inbr = None
    inbr = pyp_nrm.a_matrix(pedigree)
    return inbr


##
# test_pyp_nrm_fast_a_matrix() attempts to calculate the relatonship matrix from the provided pedigree using
# pyp_nrn/fast_a_matrix().
# @param pedigree A PyPedal pedigree object.
# @param options A dictionary of pedigree options
# @retval A PyPedal pedigree object on success, None on failure.
def test_pyp_nrm_fast_a_matrix(pedigree, options):
    """
    test_pyp_nrm_fast_a_matrix() attempts to calculate the relationship matrix from the provided pedigree using
    pyp_nrn/fast_a_matrix().
    """
    inbr = None
    inbr = pyp_nrm.fast_a_matrix(pedigree, options)
    return inbr


##
# test_pyp_nrm_fast_a_matrix_r() attempts to calculate the relationship matrix adjusted for numerator relationships
# from the provided pedigree using pyp_nrn/fast_a_matrix_r().
# @param pedigree A PyPedal pedigree object.
# @param options A dictionary of pedigree options
# @retval A PyPedal pedigree object on success, None on failure.
def test_pyp_nrm_fast_a_matrix_r(pedigree, options):
    """
    test_pyp_nrm_fast_a_matrix_r() attempts to calculate the relationship matrix adjusted for numerator relationships
    from the provided pedigree using pyp_nrn/fast_a_matrix_r().
    """
    inbr = None
    inbr = pyp_nrm.fast_a_matrix_r(pedigree, options)
    return inbr


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

    inbr = np.array([
                  [1.0000, 0.0000, 0.5000, 0.5000, 0.5000, 0.2500],
                  [0.0000, 1.0000, 0.5000, 0.0000, 0.2500, 0.6250],
                  [0.5000, 0.5000, 1.0000, 0.2500, 0.6250, 0.5625],
                  [0.5000, 0.0000, 0.2500, 1.0000, 0.6250, 0.3125],
                  [0.5000, 0.2500, 0.6250, 0.6250, 1.1250, 0.6875],
                  [0.2500, 0.6250, 0.5625, 0.3125, 0.6875, 1.1250]
    ])

    result2 = test_pyp_nrm_a_matrix(result)
    assert (result2 == inbr).all(), ('Could not compute the relationship matrix for test_files/mrode.ped using '
                                     'yp_nrm/a_martix()!')
    print('\t[SUCCESS]: Computed the relationship matrix for test_files_mrode.ped using pyp_nrm/a_matrix().')

    result3 = test_pyp_nrm_fast_a_matrix(result.pedigree, result.kw)
    assert (result3 == inbr).all(), ('Could not compute the relationship matrix for test_files/mrode.ped '
                                     'using pyp_nrm/fast_a_martix()!')
    print('\t[SUCCESS]: Computed the relationship matrix for test_files_mrode.ped using pyp_nrm/fast_a_matrix().')

    inbr_r = np.array([
        [1.,         0.,         0.5,        0.5,        0.5,        0.23570226],
        [0.,         1.,         0.5,        0.,         0.25,       0.58925565],
        [0.5,        0.5,        1.,         0.25,       0.625,      0.53033009],
        [0.5,        0.,         0.25,       1.,         0.625,      0.29462783],
        [0.5,        0.25,       0.625,      0.625,      1.125,      0.64818122],
        [0.23570226, 0.58925565, 0.53033009, 0.29462783, 0.64818122, 1.125]
    ])

    result4 = test_pyp_nrm_fast_a_matrix_r(result.pedigree, result.kw)
    assert (result4 == inbr).all(), ('Could not compute the relationship matrix adjusted for numerator relationships'
                                     'for test_files/mrode.ped using pyp_nrm/fast_a_martix_r()!')
    print('\t[SUCCESS]: Computed the relationship matrix adjusted for numerator relationships for test_files_mrode.ped '
          'using pyp_nrm/fast_a_matrix_r().')


