#!/usr/bin/python

###############################################################################
# NAME: pyp_newclasses.py
# VERSION: 3.0.0 (16MARCH2024)
# AUTHOR: John B. Cole (john.b.cole@gmail.com)
# LICENSE: LGPL v2.1 (see LICENSE file)
###############################################################################

## @package pyp_newclasses
# pyp_newclasses contains the new class structure that will be a part of PyPedal 2.0.0Final.
# It includes a master class to which most of the computational routines will be bound as
# methods, a NewAnimal() class, and a PedigreeMetadata() class.
##

import logging
import numpy
# import string
import sys
import time
# Handle the configuration file
from configobj import ConfigObj
# Import the other pieces of PyPedal.  This will probably go away as most of these are rolled into
# NewPedigree as methods.
from . import pyp_db
from . import pyp_io
from . import pyp_metrics
from . import pyp_nrm
from . import pyp_utils


##
# The NewPedigree class is the main data structure for PyP 2.0.0Final.
class NewPedigree:
    ##
    # __init__() initializes a NewPedigree object.
    # @param self Reference to the current NewPedigree() object
    # @param kw A dictionary of options.
    # @param kwfile An optionsl configuration file name
    # @retval An instance of a NewPedigree() object
    def __init__(self, kw={}, kwfile='pypedal.ini'):
        """
        __init__() initializes a NewPedigree object.
        """

        # This hacks-in support for configuration files.  This is not
        # a perfect solution because it can let a naked exception
        # propagate back to the user, but __init__() methods can only
        # return None, so there is no nice way to pass back a message
        # if an exception is thrown.  If dict4ini.DictIni(kwfile) fails,
        # then kw will be an empty dictionary.  The user will only see
        # this when the load() method is called on the NewPedigree
        # instance.
        if len(kw) == 0:
            # from . import dict4ini
            # kw = dict4ini.DictIni(kwfile)
            kw = ConfigObj(kwfile)
            if kw == {}:
                print('[ERROR]: pyp_newclasses.NewPedigree.__init__() was unable to load a configuration file named '
                      '%s!' % kwfile)
                import sys
                sys.exit(0)
            # The dict method converts the Dict4Ini object to an actual
            # Python dictionary.
            kw = kw.dict()

        # Handle the Main Keywords.

        # Here are the keywords used for simulating pedigrees.  We need to
        # set simulate_pedigree before we do anything else; if the user
        # wants to simulate a pedigree they do not need to provide a
        # pedfile.
        if 'simulate_pedigree' not in list(kw.keys()):
            kw['simulate_pedigree'] = 0
        if kw['simulate_pedigree']:
            # These defaults will produce a three-generation pedigree
            # in which each sire and dam has a single progeny.
            if 'simulate_n' not in list(kw.keys()):
                kw['simulate_n'] = 15
            if 'simulate_g' not in list(kw.keys()):
                kw['simulate_g'] = 3
            if 'simulate_ns' not in list(kw.keys()):
                kw['simulate_ns'] = 4
            if 'simulate_nd' not in list(kw.keys()):
                kw['simulate_nd'] = 4
            if 'simulate_mp' not in list(kw.keys()):
                kw['simulate_mp'] = 0
            if 'simulate_po' not in list(kw.keys()):
                kw['simulate_po'] = 0
            if 'simulate_fs' not in list(kw.keys()):
                kw['simulate_fs'] = 0
            if 'simulate_sr' not in list(kw.keys()):
                kw['simulate_sr'] = 0.5
            if 'simulate_ir' not in list(kw.keys()):
                kw['simulate_ir'] = 0.0
            if 'simulate_pmd' not in list(kw.keys()):
                kw['simulate_pmd'] = 100
            if 'simulate_save' not in list(kw.keys()):
                kw['simulate_save'] = 0
            # This seed isn't anything mysterious, it's my office telephone number from when I worked at USDA.
            if 'simulate_seed' not in list(kw.keys()):
                kw['simulate_seed'] = 5048665
        else:
            if 'pedfile' not in list(kw.keys()):
                raise PyPedalPedigreeInputFileNameError
        if 'pedigree_save' not in list(kw.keys()):
            kw['pedigree_save'] = 0
        if 'pedformat' not in list(kw.keys()):
            kw['pedformat'] = 'asd'
        if 'has_header' not in list(kw.keys()):
            kw['has_header'] = 0
        if 'pedname' not in list(kw.keys()):
            kw['pedname'] = 'Untitled'
        if 'messages' not in list(kw.keys()):
            kw['messages'] = 'verbose'
        if 'renumber' not in list(kw.keys()):
            kw['renumber'] = 1
        if 'reorder' not in list(kw.keys()):
            kw['reorder'] = 0
        # When True, auto_renumber tells PyPedal to automatically renumber a pedigree when a function requires a
        # renumbered pedigree but the pedigree provided is not renumbered.
        if 'auto_renumber' not in list(kw.keys()):
            kw['auto_renumber'] = False
        if 'reorder_max_rounds' not in list(kw.keys()):
            kw['reorder_max_rounds'] = 100
        if 'pedigree_is_renumbered' not in list(kw.keys()):
            kw['pedigree_is_renumbered'] = 0
        if 'set_generations' not in list(kw.keys()):
            kw['set_generations'] = 0
        if 'gen_coeff' not in list(kw.keys()):
            kw['gen_coeff'] = 0
        if 'set_ancestors' not in list(kw.keys()):
            kw['set_ancestors'] = 0
        if 'set_alleles' not in list(kw.keys()):
            kw['set_alleles'] = 0
        if 'set_offspring' not in list(kw.keys()):
            kw['set_offspring'] = 0
        if 'set_sexes' not in list(kw.keys()):
            kw['set_sexes'] = 0
        if 'pedcomp' not in list(kw.keys()):
            kw['pedcomp'] = 0
        if 'pedcomp_gens' not in list(kw.keys()):
            kw['pedcomp_gens'] = 3
        if 'sepchar' not in list(kw.keys()):
            kw['sepchar'] = ' '
        if 'alleles_sepchar' not in list(kw.keys()):
            kw['alleles_sepchar'] = '/'
        if 'counter' not in list(kw.keys()):
            kw['counter'] = 1000
        if 'slow_reorder' not in list(kw.keys()):
            kw['slow_reorder'] = 1
        if 'update_sexes' not in list(kw.keys()):
            kw['update_sexes'] = 0
        # Default missing values for NewAnimal objects.
        if 'missing_bdate' not in list(kw.keys()):
            kw['missing_bdate'] = '01011900'
        if 'missing_byear' not in list(kw.keys()):
            kw['missing_byear'] = 1900
        if 'missing_parent' not in list(kw.keys()):
            kw['missing_parent'] = 0
        if 'missing_name' not in list(kw.keys()):
            kw['missing_name'] = 'Unknown_Name'
        if 'missing_breed' not in list(kw.keys()):
            kw['missing_breed'] = 'Unknown_Breed'
        if 'missing_herd' not in list(kw.keys()):
            kw['missing_herd'] = 'Unknown_Herd'
        if 'missing_sex' not in list(kw.keys()):
            kw['missing_sex'] = 'u'
        if 'missing_inbreeding' not in list(kw.keys()):
            kw['missing_inbreeding'] = 0.
        if 'missing_alive' not in list(kw.keys()):
            kw['missing_alive'] = 0
        if 'missing_age' not in list(kw.keys()):
            kw['missing_age'] = -999
        if 'missing_gen' not in list(kw.keys()):
            kw['missing_gen'] = -999.
        if 'missing_gencoeff' not in list(kw.keys()):
            kw['missing_gencoeff'] = -999.
        if 'missing_igen' not in list(kw.keys()):
            kw['missing_igen'] = -999.
        if 'missing_pedcomp' not in list(kw.keys()):
            kw['missing_pedcomp'] = -999.
        if 'missing_alleles' not in list(kw.keys()):
            kw['missing_alleles'] = ['', '']
        if 'missing_userfield' not in list(kw.keys()):
            kw['missing_userfield'] = ''
        if 'missing_value' not in list(kw.keys()):
            kw['missing_value'] = -999.
        # End of default missing values for NewAnimal objects.
        if 'file_io' not in list(kw.keys()):
            kw['file_io'] = '1'
        if 'debug_messages' not in list(kw.keys()):
            kw['debug_messages'] = 0
        if 'form_nrm' not in list(kw.keys()):
            kw['form_nrm'] = 0
        if 'nrm_method' not in list(kw.keys()):
            kw['nrm_method'] = 'nrm'
        if 'nrm_format' not in list(kw.keys()):
            kw['nrm_format'] = 'text'
        if 'f_computed' not in list(kw.keys()):
            kw['f_computed'] = 0
        if 'long_ped_lines' not in list(kw.keys()):
            kw['log_ped_lines'] = 0
        if 'log_long_filename' not in list(kw.keys()):
            kw['log_long_filenames'] = 0
        if 'pedigree_summary' not in list(kw.keys()):
            kw['pedigree_summary'] = 1
        if kw['pedigree_summary'] not in [0, 1, 2]:
            kw['pedigree_summary'] = 1
        if 'animal_type' not in list(kw.keys()):
            kw['animal_type'] = 'new'
        if kw['animal_type'] not in ['new', 'light']:
            kw['animal_type'] = 'new'
        if 'f' in kw['pedformat']:
            kw['f_computed'] = 1
        # We have to check for the pedfile key in case this is a
        # simulated pedigree, which does not have a pedfile.
        if kw['simulate_pedigree']:
            kw['pedfile'] = 'simulated_pedigree'
        # kw['filetag'] = string.split(kw['pedfile'], '.')[0]
        kw['filetag'] = kw['pedfile'].split('.')[0]
        if len(kw['filetag']) == 0:
            kw['filetag'] = 'untitled_pedigree'
        # The database name and default database table name are needed by pyp_db.
        # If the defaults are not overridden 'pypedal' and the filetag are used
        # for the defaults, respectively.
        if 'database_name' not in list(kw.keys()):
            kw['database_name'] = 'pypedal'
        if 'database_table' not in list(kw.keys()):
            kw['database_table'] = pyp_utils.string_to_table_name(kw['filetag'])
        else:
            kw['database_table'] = pyp_utils.string_to_table_name(kw['database_table'])
        if 'database_debug' not in list(kw.keys()):
            kw['database_debug'] = False
        if 'database_type' not in list(kw.keys()):
            kw['database_type'] = 'sqlite'
        if 'database_host' not in list(kw.keys()):
            kw['database_host'] = 'localhost'
        if 'database_user' not in list(kw.keys()):
            kw['database_user'] = 'anonymous'
        if 'database_passwd' not in list(kw.keys()):
            kw['database_passwd'] = 'anonymous'
        if 'database_port' not in list(kw.keys()):
            kw['database_port'] = ''
        if 'database_sql' not in list(kw.keys()):
            kw['database_sql'] = 'SELECT * FROM %s'
        # This keyword is used by pyp_nrm/fast_a_matrix() to determine if the diagonals
        # of the relationship matrix should be augmented by founder coefficients of
        # inbreeding or not. This is disabled by default.
        if 'foundercoi' not in list(kw.keys()):
            kw['foundercoi'] = 0.
        if kw['foundercoi'] < 0. or kw['foundercoi'] > 1.:
            kw['foundercoi'] = 0.
        # If the user provides a paper size make sure that it is a supported value.
        # Right now, only a4 and letter are supported.  Note that 'a4' is silently
        # changed to 'A4' because ReportLab is case-sensitive.  Also handle setting
        # the defualt unit of measurement.
        if 'paper_size' not in list(kw.keys()):
            kw['paper_size'] = 'letter'
        if kw['paper_size'] == 'a4':
            kw['paper_size'] = 'A4'
        if kw['paper_size'] not in ['A4', 'letter']:
            kw['paper_size'] = 'letter'
        if 'default_unit' not in list(kw.keys()):
            kw['default_unit'] = 'inch'
        if kw['default_unit'] not in ['cm', 'inch']:
            kw['default_unit'] = 'inch'
        # Defining the default font size to be used in graphs as a keyword
        # saves some cruft in pyp_graphics and makes it easier for the user
        # to understand what is going on.
        if 'default_fontsize' not in list(kw.keys()):
            kw['default_fontsize'] = 10
        try:
            kw['default_fontsize'] = int(kw['default_fontsize'])
        except TypeError:
            kw['default_fontsize'] = 10
        if kw['default_fontsize'] < 1:
            kw['default_fontsize'] = 10
        # default_report is used by pyp_reports as a root name when writing
        # reports to files.
        if 'database_report' not in list(kw.keys()):
            kw['default_report'] = kw['filetag']
        # This is a hack to fix it so that the inbreeding routines in
        # pyp_nrm can be told to use sparse matrices when necessary.
        if 'matrix_type' not in list(kw.keys()):
            kw['matrix_type'] = 'dense'
        if kw['matrix_type'] not in ['dense', 'sparse']:
            kw['matrix_type'] = 'dense'

        # !!! This is for internal use only! I left it out of the documentation
        # !!! on purpose so that people won't break things with it.
        if 'newanimal_caller' not in list(kw.keys()):
            kw['newanimal_caller'] = 'loader'

        # Options related to traits
        if 'trait_names' not in list(kw.keys()):
            kw['trait_names'] = []
        if 'trait_auto_name' not in list(kw.keys()):
            kw['trait_auto_name'] = 1
        if 'trait_count' not in list(kw.keys()):
            kw['trait_count'] = 0

        # We need a match rule to use with the __add__() method.
        if 'match_rule' not in list(kw.keys()):
            kw['match_rule'] = 'asd'

        # Now that we have processed all the arguments in the options dictionary
        # we need to attach it to this object.
        #         print('Ending kw: ', kw )
        self.kw = kw

        # Initialize the Big Main Data Structures to null values
        self.pedigree = []  # We may start storing animals in a dictionary rather than in a list.  Maybe,
        self.metadata = {}  # Metadata will also be stored in a dictionary.
        self.idmap = {}  # Used to map between original and renumbered IDs.
        self.backmap = {}  # Used to map between renumbered and original IDs.
        self.namemap = {}  # This is needed to map IDs to names when IDs are read using the string formats (ASD).
        self.backmap = {}
        self.namebackmap = {}
        self.stringmap = {}  # Maps original IDs to names in ASD pedigrees
        # Maybe these will go in a configuration file later
        self.starline = '*' * 80
        # This is the list of valid pedformat codes
        self.pedformat_codes = ['a', 's', 'd', 'g', 'x', 'b', 'f', 'r', 'n', 'y', 'l', 'e', 'p', 'A', 'S', 'D', 'L',
                                'Z', 'h', 'H', 'u', 'T']
        # This dictionary maps pedformat codes to NewAnimal attributes
        self.new_animal_attr = {
            'a': 'animalID',
            's': 'sireID',
            'd': 'damID',
            'g': 'gen',
            'x': 'sex',
            'b': 'bd',
            'f': 'fa',
            'r': 'breed',
            'n': 'name',
            'y': 'by',
            'l': 'alive',
            'e': 'age',
            'p': 'gencoeff',
            'A': 'name',
            'S': 'sireName',
            'D': 'damName',
            'L': 'alleles',
            'Z': False,
            'h': 'herd',
            'H': 'originalHerd',
            'u': 'userField',
            'T': 'traits',
        }
        # Start logging!
        if 'logfile' not in list(kw.keys()):
            if kw['log_long_filenames']:
                kw['logfile'] = '%s_%s.log' % (kw['filetag'], pyp_utils.pyp_datestamp())
            else:
                kw['logfile'] = '%s.log' % (kw['filetag'])
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S', filename=kw['logfile'], filemode='w')
        logging.info('Logfile %s instantiated.', kw['logfile'])
        if kw['messages'] == 'verbose' and kw['pedigree_summary']:
            print('[INFO]: Logfile %s instantiated.' % (kw['logfile']))
        # Deal with aberrant cases of log_ped_lines here.
        try:
            kw['log_ped_lines'] = int(kw['log_ped_lines'])
        except ValueError:
            kw['log_ped_lines'] = 0
            logging.warning('An incorrect value (%s) was provided for the option log_ped_lines, which must be a number '
                            'greater than or equal 0.  It has been set to 0.', kw['log_ped_lines'])
        if kw['log_ped_lines'] < 0:
            kw['log_ped_lines'] = 0
            logging.warning('A negative value (%s) was provided for the option log_ped_lines, which must be greater '
                            'than or equal 0.  It has been set to 0.', kw['log_ped_lines'])

    ##
    # Method to add two pedigrees and return a new pedigree representing the
    # merged pedigrees.
    def __add__(self, other, filename=False, debug_load=False):
        """
        Method to add two pedigree and return a new pedigree representing the
        merged pedigrees.
        """
        if self.__class__.__name__ == 'NewPedigree' and other.__class__.__name__ == 'NewPedigree':
            logging.info('Adding pedigrees %s and %s', self.kw['pedname'],
                         other.kw['pedname'])
            if self.kw['debug_messages']:
                print('[DEBUG]: self and other both are NewPedigree objects. We can start combining them.')
                print('[DEBUG]: Using match rule: %s' % (self.kw['match_rule']))
            logging.info('Using match rule %s to merge pedigrees',
                         self.kw['match_rule'])
            # Pedigrees must be renumbered
            if self.kw['pedigree_is_renumbered'] != 1:
                self.renumber()
                logging.info('Renumbering pedigree %s', self.kw['pedname'])
            if other.kw['pedigree_is_renumbered'] != 1:
                other.renumber()
                logging.info('Renumbering pedigree %s', other.kw['pedname'])
            # We need to compare each animal in self and other to see if they
            # match based on the match_rule.
            #
            # We're going to use a dictionary to keep track of which animals
            # need to be written to the new pedigree file from which the merged
            # pedigree will be loaded. By default, I assume that all animal
            # records are unique, and only change the ped_to_write flag  when a
            # duplicate has been detected.
            #
            # NOTE: It's nagging at me that there may be a logic error in the
            # checking and flagging, so this code needs to be thoroughly tested!
            ped_to_write = {'a': {}, 'b': {}}
            for a in self.pedigree:
                ped_to_write['a'][a.animalID] = True
                for b in other.pedigree:
                    mismatches = 0  # Count places where the animals don't match
                    # print 'Comparing animal %s in a and animal %s in b' % \
                    #    ( a.animalID, b.animalID )
                    for match in self.kw['match_rule']:
                        # print 'First match criterion: %s (%s)' % \
                        #    ( match, self.new_animal_attr[match] )
                        # If we're comparing animal IDs, make sure that we
                        # compare original IDs, not renumbered IDs.
                        if match in ['a', 'A']:
                            if a.originalID != b.originalID:
                                mismatches += 1
                        # The sire and dam match rules don't work correctly
                        # when the sires or dams are unknown.
                        elif match in ['s', 'S']:
                            # Check and see if sires are unknown -- what do we do if
                            # self and other have different missing parent indicators?
                            # It doesn't matter -- an unknown parent is an unknown
                            # parent.
                            if self.pedigree[a.sireID] != self.kw['missing_parent'] and \
                                            other.pedigree[b.sireID] != other.kw['missing_parent']:
                                if self.pedigree[a.sireID - 1].originalID != \
                                        other.pedigree[b.sireID - 1].originalID:
                                    mismatches += 1
                            # If one parent is unknown and the othe ris not then we have
                            # a mismatch.
                            elif self.pedigree[a.sireID] == self.kw['missing_parent'] and \
                                    other.pedigree[b.sireID] != other.kw['missing_parent']:
                                mismatches += 1
                            elif self.pedigree[a.sireID] != self.kw['missing_parent'] and \
                                    other.pedigree[b.sireID] == other.kw['missing_parent']:
                                mismatches += 1
                            # Otherwise, carry onn.
                            else:
                                pass
                        elif match in ['d', 'D']:
                            if self.pedigree[a.damID] != self.kw['missing_parent'] and \
                                    other.pedigree[b.damID] != other.kw['missing_parent']:
                                if self.pedigree[a.damID - 1].originalID != \
                                        other.pedigree[b.damID - 1].originalID:
                                    mismatches += 1
                            elif (self.pedigree[a.sireID] == self.kw['missing_parent'] and
                                  other.pedigree[b.sireID] != other.kw['missing_parent']):
                                mismatches += 1
                            elif (self.pedigree[a.sireID] != self.kw['missing_parent'] and
                                  other.pedigree[b.sireID] == other.kw['missing_parent']):
                                mismatches += 1
                            else:
                                pass
                        elif getattr(a, self.new_animal_attr[match]) != \
                                getattr(b, self.new_animal_attr[match]):
                            # print '%s == %s' % ( \
                            #    getattr(a, self.new_animal_attr[match]), \
                            #    getattr(b, self.new_animal_attr[match]) )
                            mismatches += 1
                        else:
                            # print '%s != %s' % ( \
                            #    getattr(a, self.new_animal_attr[match]), \
                            #    getattr(b, self.new_animal_attr[match]) )
                            pass
                    # If there are no mismatches then the two animals are identical
                    # based on the match rule and only one of them needs to be written
                    # to the merged pedigree.
                    if mismatches == 0:
                        # Animals are identical
                        ped_to_write['b'][b.animalID] = False
                        if self.kw['debug_messages']:
                            print('[DEBUG]: Animals %s and %s are identical:' %
                                  (a.animalID, b.animalID))
                    else:
                        # Animals are different
                        ped_to_write['b'][b.animalID] = True
                        if self.kw['debug_messages']:
                            print('[DEBUG]: Animals %s and %s are different:' %
                                  (a.animalID, b.animalID))
                    if self.kw['debug_messages']:
                        print('[DEBUG]: \tA: %s,\tS: %s,\tD: %s' % (a.animalID,
                                                                    self.pedigree[a.sireID - 1].originalID,
                                                                    self.pedigree[a.damID - 1].originalID))
                        print('[DEBUG]: \tA: %s,\tS: %s,\tD: %s' % (b.animalID,
                                                                    other.pedigree[b.sireID - 1].originalID,
                                                                    other.pedigree[b.damID - 1].originalID))
            # Once we have matches, we are going to write a new pedigree
            # file to disc, and we will load that file to get the new
            # pedigree.
            #
            # First, save the unique animals from the union of pedigrees a and
            # b based on the match rule. Note that the pedformat from the first
            # pedigree passed to __add__() will be used for both pedigrees. This
            # makes sense because you cannot have two different pedformats in
            # the same file.
            if not filename:
                filename = '%s_%s.ped' % (self.kw['pedname'],
                                          other.kw['pedname'])
                print('[INFO]: filename = %s' % filename)
            self.save(filename=filename, write_list=ped_to_write['a'],
                      pedformat=self.kw['pedformat'], originalID=True)
            other.save(filename=filename, write_list=ped_to_write['b'],
                       pedformat=self.kw['pedformat'], originalID=True, append=True)
            # Now we need to load the new pedigree and return it. This should be
            # dead easy.
            #
            # Create the options dictionary
            merged_pedname = 'Merged Pedigree: %s + %s' % (self.kw['pedname'], other.kw['pedname'])
            new_options = {
                'messages': self.kw['messages'],
                'pedname': merged_pedname,
                'renumber': 1,
                'pedfile': filename,
                'pedformat': self.kw['pedformat'],
            }
            # Load the new pedigree and return it.
            try:
                new_pedigree = load_pedigree(new_options, debug_load=True)
                if self.kw['messages'] == 'verbose':
                    print('[INFO]: Loaded merged pedigree %s from file %s!' %
                          (merged_pedname, filename))
                logging.info('Loaded merged pedigree %s from file %s.',
                             merged_pedname, filename)
                return new_pedigree
            except:
                if self.kw['messages'] == 'verbose':
                    print('[ERROR]: Could not load merged pedigree %s from file %s!' %
                          (merged_pedname, filename))
                logging.error('Could not load merged pedigree %s from file %s!',
                              merged_pedname, filename)
                return False
        else:
            logging.error('Cannot complete __add__() operation because types do not match.')
            return NotImplemented

    ##
    # Method to subtract two pedigree and return a new pedigree representing the
    # first pedigree without any animals shared in common with the second pedigree,
    # or: A - B = A - (A \cap B).
    def __sub__(self, other, filename=False, debug_load=False):
        """
        Method to subtract two pedigree and return a new pedigree representing the
        first pedigree without any animals shared in common with the second pedigree,
        or: A - B = A - (A cap B).
        """
        if self.__class__.__name__ == 'NewPedigree' and other.__class__.__name__ == 'NewPedigree':
            logging.info('Subtracting pedigrees %s and %s', self.kw['pedname'],
                         other.kw['pedname'])
            # print 'self and other both are NewPedigree objects. We can start combining them'
            # print 'Using match rule: %s' % ( self.kw['match_rule'])
            logging.info('Using match rule %s to subtract pedigrees',
                         self.kw['match_rule'])
            # Pedigrees must be renumbered
            if self.kw['pedigree_is_renumbered'] != 1:
                self.renumber()
                logging.info('Renumbering pedigree %s', self.kw['pedname'])
            if other.kw['pedigree_is_renumbered'] != 1:
                other.renumber()
                logging.info('Renumbering pedigree %s', other.kw['pedname'])
            # We need to compare each animal in self and other to see if they
            # match based on the match_rule.
            #
            # We're going to use a dictionary to keep track of which animals
            # need to be written to the new pedigree file from which the merged
            # pedigree will be loaded. By default, I assume that all animal
            # records are unique, and only change the ped_to_write flag  when a
            # duplicate has been detected.
            #
            # NOTE: It's nagging at me that there may be a logic error in the
            # checking and flagging, so this code needs to be thoroughly tested!
            ped_to_write = {'a': {}, 'b': {}}
            mismatches = 0  # Count places where the animals don't match
            for a in self.pedigree:
                ped_to_write['a'][a.animalID] = True
                for b in other.pedigree:
                    ped_to_write['b'][b.animalID] = False
                    #mismatches = 0  # Count places where the animals don't match
                    # print 'Comparing animal %s in a and animal %s in b' % \
                    #    ( a.animalID, b.animalID )
                    for match in self.kw['match_rule']:
                        # print 'First match criterion: %s (%s)' % \
                        #    ( match, self.new_animal_attr[match] )
                        # If we're comparing animal IDs, make sure that we
                        # compare original IDs, not renumbered IDs.
                        if match in ['a', 'A']:
                            if a.originalID != b.originalID:
                                mismatches += 1
                        elif match in ['s', 'S']:
                            if self.pedigree[a.sireID - 1].originalID != \
                                    other.pedigree[b.sireID - 1].originalID:
                                mismatches += 1
                        elif match in ['d', 'D']:
                            if self.pedigree[a.damID - 1].originalID != \
                                    other.pedigree[b.damID - 1].originalID:
                                mismatches += 1
                        elif getattr(a, self.new_animal_attr[match]) != \
                                getattr(b, self.new_animal_attr[match]):
                            mismatches += 1
                        else:
                            pass
            # If there are no mismatches then the two animals are identical
            # based on the match rule and only one of them needs to be written
            # to the merged pedigree.
            if mismatches == 0:
                # Animals are identical. Do not write animals from self that are
                # identical to animals in other.
                ped_to_write['a'][a.animalID] = False
            else:
                # Animals are different
                ped_to_write['b'][b.animalID] = True
            # Once we have matches, we are going to write a new pedigree
            # file to disc, and we will load that file to get the new
            # pedigree.
            #
            # First, save the unique animals from the union of pedigrees a and
            # b based on the match rule. Note that the pedformat from the first
            # pedigree passed to __add__() will be used for both pedigrees. This
            # makes sense because you cannot have two different pedformats in
            # the same file.
            if not filename:
                filename = '%s_%s.ped' % (self.kw['pedname'],
                                          other.kw['pedname'])
                print('[INFO]: filename = %s' % filename)
            self.save(filename=filename, write_list=ped_to_write['a'],
                      pedformat=self.kw['pedformat'], originalID=True)
            other.save(filename=filename, write_list=ped_to_write['b'],
                       pedformat=self.kw['pedformat'], originalID=True, append=True)
            # Now we need to load the new pedigree and return it. This should be
            # dead easy.
            #
            # Create the options dictionary
            merged_pedname = 'Merged Pedigree: %s + %s' % \
                             (self.kw['pedname'], other.kw['pedname'])
            new_options = {
                'messages': self.kw['messages'],
                'pedname': merged_pedname,
                'renumber': 1,
                'pedfile': filename,
                'pedformat': self.kw['pedformat'],
            }
            # Load the new pedigree and return it.
            try:
                new_pedigree = load_pedigree(new_options, debug_load=True)
                if self.kw['messages'] == 'verbose':
                    print('[INFO]: Loaded merged pedigree %s from file %s!' %
                          (merged_pedname, filename))
                logging.info('Cannot complete __add__() operation becuase types do not match.')
                return new_pedigree
            except:
                if self.kw['messages'] == 'verbose':
                    print('[ERROR]: Could not load merged pedigree %s from file %s!' %
                          (merged_pedname, filename))
                logging.error('Could not load merged pedigree %s from file %s!',
                              merged_pedname, filename)
                return False
        else:
            logging.error('Cannot complete __add__() operation becuase types do not match.')
            return NotImplemented

    # __union__() is an alias to NewPedigree::__add__().
    def union(self, other, filename=False, debug_load=False):
        """
            __union__() is an alias to NewPedigree::__add__().
        """
        self.__add__(self, other, filename, debug_load)

    ##
    # __intersection__() returns a PyPedal pedigree object which contains the animals that are
    # common to both input pedigrees. If there are no animals in common between the two pedgrees,
    # a value of false is returned.
    # @param pedobj_b Another PyPedal pedigree.
    # @param filename The file to which the new pedigree should be written
    # @retval A new PyPedal pedigree containing the animals that are common to both input pedigrees.
    def intersection(self, other, filename=False):
        """
        intersection() returns a PyPedal pedigree object which contains the animals that are common to
        both input pedigrees. If there are no animals in common between the two pedgrees, a value
        of false is returned.
        """
        if self.__class__.__name__ == 'NewPedigree' and other.__class__.__name__ == 'NewPedigree':
            logging.info('Computing intersection of pedigrees %s and %s', self.kw['pedname'], other.kw['pedname'])
            logging.info('Using match rule %s to compare pedigrees', self.kw['match_rule'])
            # Pedigrees must be renumbered
            if self.kw['pedigree_is_renumbered'] != 1:
                self.renumber()
                logging.info('Renumbering pedigree %s', self.kw['pedname'])
            if other.kw['pedigree_is_renumbered'] != 1:
                other.renumber()
                logging.info('Renumbering pedigree %s', other.kw['pedname'])
            # We need to compare each animal in self and other to see if they
            # match based on the match_rule.
            #
            # We're going to use a dictionary to keep track of which animals
            # need to be written to the new pedigree file from which the merged
            # pedigree will be loaded. By default, I assume that all animal
            # records are unique, and only change the ped_to_write flag  when a
            # duplicate has been detected.
            #
            # NOTE: It's nagging at me that there may be a logic error in the
            # checking and flagging, so this code needs to be thoroughly tested!
            animals_to_write = []
            for a in self.pedigree:
                for b in other.pedigree:
                    matches = 0  # Count places where the animals match
                    # print('Comparing animal %s in a and animal %s in b' % \
                    #    ( a.animalID, b.animalID ))
                    for match in self.kw['match_rule']:
                        # print('First match criterion: %s (%s)' % \
                        #    ( match, self.new_animal_attr[match] ))
                        # If we're comparing animal IDs, make sure that we
                        # compare original IDs, not renumbered IDs.
                        if match in ['a', 'A']:
                            if a.originalID == b.originalID:
                                matches += 1
                        elif match in ['s', 'S']:
                            if self.pedigree[a.sireID - 1].originalID == \
                                    other.pedigree[b.sireID - 1].originalID:
                                matches += 1
                        elif match in ['d', 'D']:
                            if self.pedigree[a.damID - 1].originalID == \
                                    other.pedigree[b.damID - 1].originalID:
                                matches += 1
                        elif getattr(a, self.new_animal_attr[match]) == \
                                getattr(b, other.new_animal_attr[match]):
                            # print('%s == %s' % ( \
                            #    getattr(a, self.new_animal_attr[match]), \
                            #    getattr(b, self.new_animal_attr[match]) ))
                            matches += 1
                        else:
                            # print('%s != %s' % ( \
                            #    getattr(a, self.new_animal_attr[match]), \
                            #    getattr(b, self.new_animal_attr[match]) ))
                            pass
                # If there are no mismatches then the two animals are identical
                # based on the match rule and only one of them needs to be written
                # to the merged pedigree.
                if matches == len(self.kw['match_rule']):
                    # Animals are identical
                    animals_to_write.append(a)
            # Once we have matches, we are going to write a new pedigree file to disc, and we will load that file to
            # get the new pedigree.
            #
            # First, save the unique animals from the union of pedigrees a and b based on the match rule. Note that
            # the pedformat from the first pedigree passed to __add__() will be used for both pedigrees. This
            # makes sense because you cannot have two different pedformats in the same file.
            if not filename:
                filename = '%s_%s.ped' % (self.kw['pedname'], other.kw['pedname'])
                if self.kw['debug_messages']:
                    print('[INFO]: filename = %s' % filename)
                pyp_io.save_newanimals_to_file(animals_to_write, filename, self.pedigree, self.pedformat, self.kw)
            # Now we need to load the new pedigree and return it. This should be
            # dead easy.
            #
            # Create the options dictionary
            intersect_pedname = 'Intersected Pedigree: %s + %s' % (self.kw['pedname'], other.kw['pedname'])
            new_options = {
                'messages': self.kw['messages'],
                'pedname': intersect_pedname,
                'renumber': 1,
                'pedfile': filename,
                'pedformat': self.kw['pedformat'],
            }
            # Load the new pedigree and return it.
            try:
                new_pedigree = load_pedigree(new_options, debug_load=True)
                if self.kw['messages'] == 'verbose':
                    print('[INFO]: Loaded intersected pedigree %s from file %s!' %
                          (intersect_pedname, filename))
                    logging.info('Cannot complete intersection operation because types do not match.')
                    return new_pedigree
            except:
                if self.kw['messages'] == 'verbose':
                    print('[ERROR]: Could not load intersected pedigree %s from file %s!' %
                          (intersect_pedname, filename))
                logging.error('Could not load intersected pedigree %s from file %s!',
                              intersect_pedname, filename)
                return False
        else:
            logging.error('Cannot complete intersection operation because types do not match.')
            return NotImplemented

    ##
    # load() wraps several processes useful for loading and preparing a pedigree for
    # use in an analysis, including reading the animals into a list of animal objects,
    # forming lists of sires and dams, checking for common errors, setting ancestor
    # flags, and renumbering the pedigree.
    # @param self Reference to current object.
    # @param pedsource Source of the pedigree ('file'|'graph'|'graphfile'|'db').
    # @param pedgraph DiGraph from which to load the pedigree.
    # @param pedstream Stream of text from which to load the pedigree.
    # @param animallist Liost of NewAnimal objects from which to create a pedigree.
    # @retval None
    def load(self, pedsource='file', pedgraph=0, pedstream='', animallist=False):
        """
        load() wraps several processes useful for loading and preparing a pedigree for
        use in an analysis, including reading the animals into a list of animal objects,
        forming lists of sires and dams, checking for common errors, setting ancestor
        flags, and renumbering the pedigree.
        """
        # Check for valid values of pedsource
        if pedsource not in ['file', 'db', 'graph', 'graphfile', 'null', 'animallist', 'gedcomfile', 'genesfile',
                             'textstream']:
            logging.error('Unable to load pedigree because an invalid value of %s was provided for pedsource!',
                          pedsource)
            sys.exit(0)
        # If the user has included traits in the pedigree file, we need to make sure that the
        # names are properly handled.
        if len(self.kw['trait_names']) > 0 and self.kw['trait_auto_name'] != 0:
            # Use the name list
            # logging.warning('Loading from database %s.%s at %s.',self.kw['database_name'], \
            #     self.kw['database_table'], pyp_utils.pyp_nice_time())
            # if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            #     print '[INFO]: Loading from database %s.%s' % ( self.kw['database_name'], \
            #     self.kw['database_table'] )        # Create the table
            pass
        # If the user wants to simulate a pedigree we don't need to
        # call self.preprocess(), which loads pedigrees from files.
        if self.kw['simulate_pedigree']:
            self.simulate()
        # Load an ASDx pedigree from an SQLite databases.
        elif pedsource == 'db':
            self.kw['pedformat'] = 'ASDx'
            self.kw['sepchar'] = ','
            logging.info('Loading from database %s.%s at %s.', self.kw['database_name'],
                         self.kw['database_table'], pyp_utils.pyp_nice_time())
            if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                print('[INFO]: Loading from database %s.%s' % (self.kw['database_name'],
                                                               self.kw['database_table']))  # Create the table
            try:
                # Connect to the database
                if pyp_db.doesTableExist(self):
                    conn = pyp_db.connectToDatabase(self)
                    if conn:
                        # Contributed by Matt Kelly -- see also the 'database_sql' option
                        sql = self.kw['database_sql'] % (self.kw['database_table'])
                        # sql = 'SELECT * FROM %s' % ( self.kw['database_table'] )
                        # sql = 'SELECT animaltattoo,if(siretattoo is NULL ,"",siretattoo),if(damtattoo is NULL ,
                        # "",damtattoo),if(concat(year(bdate)) is NULL ,"",concat(year(bdate))) FROM %s' %
                        # ( self.kw['database_table'] )
                        # This could fail for VERY large pedigrees or on low-RAM machines.
                        dbstream = conn.GetAll(sql)
                        conn.Close()
                        # Process the ASDx pedigree file as usual.
                        self.preprocess(dbstream=dbstream)
                    else:
                        logging.error('Unable to connect to the database %s at %s.',
                                      self.kw['database_name'], pyp_utils.pyp_nice_time())
                        if self.kw['messages'] == 'verbose':
                            print('[ERROR]: Unable to connect to the database %s at %s.' %
                                  (self.kw['database_name'], pyp_utils.pyp_nice_time()))
                        sys.exit(0)
            except:
                logging.error('Unable to load pedigree from database %s.%s at %s.',
                              self.kw['database_name'], self.kw['database_table'], pyp_utils.pyp_nice_time())
                if self.kw['messages'] == 'verbose':
                    print('[ERROR]: Unable to load pedigree from database %s.%s' % (
                        self.kw['database_name'],
                        self.kw['database_table']))
                sys.exit(0)
        # Load the pedigree from an DiGraph object that already exists.
        elif pedsource == 'graph':
            if pedgraph:
                self.fromgraph(pedgraph)
            else:
                logging.error('Unable to load pedigree from a directed graph: no pedgraph provided!')
                sys.exit(0)
        # The graphfile pedsource uses the read_adjlist() function
        # from the NetworkX module to load a graph stored in a file
        # as an adjacency list, and then converts it to a PyPedal
        # pedigree using the NewPedigree::fromgraph() method.
        elif pedsource == 'graphfile':
            try:
                import networkx as nx
            except ImportError:
                logging.error(
                    'Unable to load pedigree from a directed graph stored in adjacency list format because the ' +
                    'NetworkX module could not be imported!')
                sys.exit(0)
            if self.kw['pedfile']:
                try:
                    pedgraph = nx.read_adjlist(self.kw['pedfile'])
                    self.fromgraph(pedgraph)
                except:
                    logging.error('Unable to load pedigree from a directed graph stored in adjacency list format!')
                    sys.exit(0)
            else:
                logging.error(
                    'Unable to load pedigree from a directed graph stored in adjacency list format because no ' +
                    'filename was provided!'
                )
                sys.exit(0)
        # I want a way to create null (empty) pedigrees. Let's see what we can do...
        elif pedsource == 'null':
            try:
                self.fromnull()
            except:
                logging.error('Unable to create a null (empty) pedigree!')
                sys.exit(0)
        # I also want a way to create a pedigree based on a list of NewAnimal instances.
        elif pedsource == 'animallist':
            if animallist and len(animallist) > 0:
                try:
                    self.fromanimallist(animallist)
                except:
                    logging.error('Unable to create a pedigree from an animallist!')
                    sys.exit(0)
            else:
                if not animallist:
                    logging.error('Unable to create a pedigree from an animal list because no list was provided!')
                else:
                    logging.error('Unable to create a pedigree from an animal list because an empty list was provided!')
                sys.exit(0)
        # The gedcomfile pedsource reads files that conform to the
        # GEDCOM 5.5 standard.
        elif pedsource == 'gedcomfile':
            if self.kw['pedfile']:
                # try:
                # Load a GEDCOM file
                if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                    print('[INFO]: Loading GEDCOM file %s.' % self.kw['pedfile'])
                pedformat = pyp_io.load_from_gedcom(infilename=self.kw['pedfile'],
                                                    standalone=0,
                                                    messages=self.kw['messages'],
                                                    missing_sex=self.kw['missing_sex'],
                                                    missing_parent=self.kw['missing_parent'],
                                                    missing_name=self.kw['missing_name'],
                                                    missing_byear=self.kw['missing_byear'])
                if pedformat != 'xxxx':
                    if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                        print('[INFO]: Changing pedformat from %s to %s as part of GEDCOM file processing.' % (
                            self.kw['pedformat'], pedformat))
                    logging.info('Changing pedformat from %s to %s.tmp as part of GEDCOM file processing.',
                                 self.kw['pedformat'], pedformat)
                    self.kw['pedformat'] = pedformat

                    logging.info('Changing sepchar from \'%s\' to \',\' as part of GEDCOM file processing.',
                                 self.kw['sepchar'])
                    self.kw['sepchar'] = ','

                    if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                        print('[INFO]: Changing pedfile from %s to %s.tmp as part of GEDCOM file processing.' % (
                            self.kw['pedfile'], self.kw['pedfile']))
                    logging.info('Changing pedfile from %s to %s.tmp as part of GEDCOM file processing.',
                                 self.kw['pedfile'], self.kw['pedfile'])
                    self.kw['pedfile'] = '%s.tmp' % self.kw['pedfile']
                    # Process the ASD pedigree file as usual.
                    self.preprocess()
                else:
                    if self.kw['messages'] == 'verbose':
                        print('[load] Unable to load pedigree from a GEDCOM file because an invalid pedigree format '
                              'code, %s, was returned!' % pedformat)
                    logging.error(
                        'Unable to load pedigree from a GEDCOM file because an invalid pedigree format code, %s, ' +
                        'was returned!', pedformat
                    )
                    # except:
                    # if self.kw['messages'] == 'verbose':
                    # print '[load] Unable to load pedigree from a GEDCOM file because an exception was raised!'
                    # logging.error('Unable to load pedigree from a GEDCOM file because an exception was raised!')
                    # sys.exit(0)
            else:
                if self.kw['messages'] == 'verbose':
                    print('[load] Unable to load pedigree from a GEDCOM file because no filename was provided!')
                logging.error('Unable to load pedigree from a GEDCOM file because no filename was provided!')
                sys.exit(0)
        # The genesfile pedsource reads files that conform to the dBase III format used by GENES v1.2.
        elif pedsource == 'genesfile':
            if self.kw['pedfile']:
                if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                    print('[INFO]: Loading GENES v1.20 file %s.' % (self.kw['pedfile']))
                pedformat = pyp_io.load_from_genes(infilename=self.kw['pedfile'],
                                                   standalone=0,
                                                   messages=self.kw['messages'],
                                                   missing_sex=self.kw['missing_sex'],
                                                   missing_parent=self.kw['missing_parent'],
                                                   missing_name=self.kw['missing_name'],
                                                   missing_bdate=self.kw['missing_bdate'])
                if pedformat != 'xxxx':
                    if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                        print('[INFO]: Changing pedformat from %s to %s as part of GENES v1.20 file processing.' % (
                            self.kw['pedformat'], pedformat))
                    logging.info('Changing pedformat from %s to %s as part of GENES v1.20 file processing.',
                                 self.kw['pedformat'], pedformat)
                    self.kw['pedformat'] = pedformat

                    logging.info('Changing sepchar from \'%s\' to \',\' as part of GENES v1.20 file processing.',
                                 self.kw['sepchar'])
                    self.kw['sepchar'] = ','

                    if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                        print('[INFO]: Changing pedfile from %s to %s.tmp as part of GENES v1.20 file processing.' % (
                            self.kw['pedfile'], self.kw['pedfile']))
                    logging.info('Changing pedfile from %s to %s.tmp as part of GENES v1.20 file processing.',
                                 self.kw['pedfile'], self.kw['pedfile'])
                    self.kw['pedfile'] = '%s.tmp' % (self.kw['pedfile'])
                    # Process the ASD pedigree file as usual.
                    self.preprocess()
                else:
                    if self.kw['messages'] == 'verbose':
                        print('[load] Unable to load pedigree from a GENES v1.20 file because an invalid pedigree '
                              'format code, %s, was returned!' % pedformat)
                    logging.error(
                        'Unable to load pedigree from a GENES v1.20 file because an invalid pedigree format code, ' +
                        '%s, was returned!', pedformat
                    )
            else:
                if self.kw['messages'] == 'verbose':
                    print('[load] Unable to load pedigree from a GENES v1.2 file because no filename was provided!')
                logging.error('Unable to load pedigree from a GENES v1.2 file because no filename was provided!')
                sys.exit(0)
        # A user requested this feature so that he can run PyPedal as a web service
        # without worrying about Apache and file creation and etc. I'll see what I
        # can do...
        elif pedsource == 'textstream':
            # Unpack those tuples...
            self.kw['pedformat'] = 'ASD'
            self.kw['sepchar'] = ','
            logging.info('Preprocessing a textstream')
            if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                print('[INFO]: Preprocessing a textstream')
            self.preprocess(textstream=pedstream)
        else:
            logging.info('Preprocessing %s', self.kw['pedfile'])
            if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                print('[INFO]: Preprocessing %s' % (self.kw['pedfile']))
            self.preprocess()
        # Now that we've got the animals loaded, take care of the
        # renumbering etc.
        if self.kw['reorder'] == 1 and not self.kw['renumber']:
            if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                print('\t[INFO]: Reordering pedigree at %s' % (pyp_utils.pyp_nice_time()))
            logging.info('Reordering pedigree')
            if not self.kw['slow_reorder']:
                self.pedigree = pyp_utils.fast_reorder(self.pedigree)
            else:
                self.pedigree = pyp_utils.reorder(self.pedigree, missingparent=self.kw['missing_parent'],
                                                  max_rounds=self.kw['reorder_max_rounds'])
                # self.pedigree = pyp_utils.reorder(self.pedigree,missingparent=self.kw['missing_parent'],
                # max_rounds=self.kw['reorder_max_rounds'])
        if self.kw['renumber'] == 1:
            self.renumber()
        if self.kw['set_generations']:
            logging.info('Assigning generations')
            if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                print('\t[INFO]: Assigning generations at %s' % (pyp_utils.pyp_nice_time()))
            pyp_utils.set_generation(self)
        if self.kw['set_ancestors']:
            logging.info('Setting ancestor flags')
            if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                print('\t[INFO]: Setting ancestor flags at %s' % (pyp_utils.pyp_nice_time()))
            pyp_utils.set_ancestor_flag(self)
        if self.kw['set_sexes']:
            logging.info('Assigning sexes')
            if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                print('\t[INFO]: Assigning sexes at %s' % (pyp_utils.pyp_nice_time()))
            pyp_utils.assign_sexes(self)
        if self.kw['set_alleles']:
            logging.info('Gene dropping to compute founder genome equivalents')
            if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                print('\t[INFO]: Gene dropping at %s' % (pyp_utils.pyp_nice_time()))
            pyp_metrics.effective_founder_genomes(self)
        if self.kw['form_nrm']:
            logging.info('Forming numerator relationship matrix')
            if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                print('\t[INFO]: Forming numerator relationship matrix at %s' % (pyp_utils.pyp_nice_time()))
            self.nrm = NewAMatrix(self.kw)
            self.nrm.form_a_matrix(self.pedigree)
        if self.kw['set_offspring'] and not self.kw['renumber']:
            logging.info('Assigning offspring')
            if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                print('\t[INFO]: Assigning offspring at %s' % (pyp_utils.pyp_nice_time()))
            pyp_utils.assign_offspring(self)
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('[INFO]: Creating pedigree metadata object')
        self.metadata = PedigreeMetadata(self.pedigree, self.kw)
        if self.kw['messages'] != 'quiet' and self.kw['pedigree_summary']:
            self.metadata.printme()
        # Calculate pedigree completeness.
        if self.kw['pedcomp']:
            logging.info('Calculating %s generation pedigree completeness', self.kw['pedcomp_gens'])
            if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                print('[INFO]: Calculating %s generation pedigree completeness' % (self.kw['pedcomp_gens']))
            _foo = pyp_metrics.pedigree_completeness(self, self.kw['pedcomp_gens'])

    ##
    # oldsave() writes a PyPedal pedigree to a user-specified file.  The saved pedigree includes
    # all fields recognized by PyPedal, not just the original fields read from the input pedigree
    # file.
    # @param self Reference to current object.
    # @param filename The file to which the pedigree should be written.
    # @param outformat The format in which the pedigree should be written: 'o' for original (as read) and 'l' for
    #                  long version (all available variables).
    # @param idformat Write 'o' (original) or 'r' (renumbered) animal, sire, and dam IDs.
    # @retval A save status indicator (0: failed, 1: success)
    def oldsave(self, filename='', outformat='o', idformat='o'):
        """
        oldsave() writes a PyPedal pedigree to a user-specified file.  The saved pedigree
        includes all fields recognized by PyPedal, not just the original fields read
        from the input pedigree file.
        """
        #
        # This is VERY important: never overwrite the user's data if it looks like an accidental
        # request!  If the user does not pass a filename to save() save the pedigree to a file
        # whose name is derived from, but not the same as, the original pedigree file.
        #
        if filename == '':
            filename = '%s_saved.ped' % (self.kw['filetag'])
            if self.kw['messages'] == 'verbose':
                print('[WARNING]: Saving pedigree to file %s to avoid overwriting %s.' % (filename, self.kw['pedfile']))
            logging.warning('Saving pedigree to file %s to avoid overwriting %s.', filename, self.kw['pedfile'])
        try:
            ofh = open(filename, 'w')
            if self.kw['messages'] == 'verbose':
                print('[INFO]: Opened file %s for pedigree save at %s.' % (filename, pyp_utils.pyp_nice_time()))
            logging.info('Opened file %s for pedigree save at %s.', filename, pyp_utils.pyp_nice_time())

            if outformat == 'l':
                # We have to form the new pedformat.
                _newpedformat = 'asdgx'
                if 'y' in self.kw['pedformat']:
                    _newpedformat = '%sy' % _newpedformat
                else:
                    _newpedformat = '%sb' % _newpedformat
                _newpedformat = '%sfrnleh' % _newpedformat
            else:
                if self.kw['f_computed']:
                    _newpedformat = '%sf' % self.kw['pedformat']
                else:
                    _newpedformat = self.kw['pedformat']

            # Write file header.
            ofh.write('# %s created by PyPedal at %s\n' % (filename, pyp_utils.pyp_nice_time()))
            ofh.write('# Current pedigree metadata:\n')
            ofh.write('#\tpedigree file: %s\n' % filename)
            ofh.write('#\tpedigree name: %s\n' % self.kw['pedname'])
            ofh.write('#\tpedigree format: \'%s\'\n' % _newpedformat)
            if idformat == 'o':
                ofh.write('#\tNOTE: Animal, sire, and dam IDs are RENUMBERED IDs, not original IDs!\n')
            ofh.write('# Original pedigree metadata:\n')
            ofh.write('#\tpedigree file: %s\n' % (self.kw['pedfile']))
            ofh.write('#\tpedigree name: %s\n' % (self.kw['pedname']))
            ofh.write('#\tpedigree format: %s\n' % (self.kw['pedformat']))
            for _a in self.pedigree:
                if idformat == 'o':
                    _outstring = '%s %s %s' % \
                                 (_a.originalID, self.pedigree[int(_a.sireID) - 1].originalID,
                                  self.pedigree[int(_a.damID) - 1].originalID)
                else:
                    _outstring = '%s %s %s' % (_a.animalID, _a.sireID, _a.damID)
                if 'g' in _newpedformat:
                    _outstring = '%s %s' % (_outstring, _a.gen)
                if 'p' in _newpedformat:
                    _outstring = '%s %s' % (_outstring, _a.gencoeff)
                if 'x' in _newpedformat:
                    _outstring = '%s %s' % (_outstring, _a.sex)
                if 'y' in _newpedformat:
                    _outstring = '%s %s' % (_outstring, _a.bd)
                else:
                    _outstring = '%s %s' % (_outstring, _a.by)
                if 'f' in _newpedformat:
                    _outstring = '%s %s' % (_outstring, _a.fa)
                if 'r' in _newpedformat:
                    _outstring = '%s %s' % (_outstring, _a.breed)
                if 'n' in _newpedformat:
                    _outstring = '%s %s' % (_outstring, _a.name)
                if 'l' in _newpedformat:
                    _outstring = '%s %s' % (_outstring, _a.alive)
                if 'e' in _newpedformat:
                    _outstring = '%s %s' % (_outstring, _a.age)
                if 'h' in _newpedformat or 'H' in _newpedformat:
                    _outstring = '%s %s' % (_outstring, _a.herd)
                    _outstring = '%s %s' % (_outstring, _a.originalHerd)
                if 'u' in _newpedformat:
                    _outstring = '%s %s' % (_outstring, _a.userField)
                ofh.write('%s\n' % _outstring)
            ofh.close()
            if self.kw['messages'] == 'verbose':
                print('[INFO]: Closed file %s after pedigree save at %s.' % (filename, pyp_utils.pyp_nice_time()))
            logging.info('Closed file %s after pedigree save at %s.', filename, pyp_utils.pyp_nice_time())
            return 1
        except:
            if self.kw['messages'] == 'verbose':
                print('[ERROR]: Unable to open file %s for pedigree save!' % filename)
            logging.error('Unable to open file %s for pedigree save.', filename)
            return 0

    ##
    # save() writes a PyPedal pedigree to a user-specified file.  The saved pedigree includes
    # all fields recognized by PyPedal, not just the original fields read from the input pedigree
    # file.
    # @param self Reference to current object.
    # @param filename The file to which the pedigree should be written.
    # @param pedformat Pedigree format string for the pedigree to be written.
    # @param sepchar Character used to separate columns in the output pedigree file.
    # @param append Append animal records to an existing file instead of creating a new one.
    # @param write_list Optional list of animal records to save. The default is to save all animals.
    # @param originalID save original IDs or renumbered IDs.
    # @retval A save status indicator (0: failed, 1: success)
    def save(self, filename='', pedformat='asd', sepchar=' ', append=False,
             write_list=False, originalID=False):
        """
        save() writes a PyPedal pedigree to a user-specified file.  The saved pedigree
        includes all fields recognized by PyPedal, not just the original fields read
        from the input pedigree file.
        """
        # Check the contents of the pedformat to make sure that each entry is valid. Save the pedformat passed in
        # by the user and add the valid entries a new version of pedformat which will be used for the remainder of
        # the processing.
        pedformat_in = str(pedformat)
        pedformat = ''
        for pf in pedformat_in:
            if pf in self.pedformat_codes:
                pedformat = '%s%s' % (pedformat, pf)
            else:
                if self.kw['messages'] == 'verbose':
                    print('[WARNING]: Invalid pedigree format code, %s, in NewPedigree::save().'
                          ' Not included in pedformat_ckd.' % pf)
                logging.warning(
                    'Invalid pedigree format code, %s, in NewPedigree::save(). Not included in pedformat_ckd.',
                    pf)
        # Warn the user if they are not outputting incomplete information (e.g., animals without sires or dams).
        if ('ASD' not in pedformat) and ('asd' not in pedformat):
            if self.kw['messages'] == 'verbose':
                print('[WARNING]: The pedigree format code, %s, does not contain the sequence \'asd\' or \'ASD\', and'
                      ' the resulting pedigree may have incomplete parentage information.' % pedformat)
            logging.warning(
                'The pedigree format code, %s, does not contain the sequence \'asd\' or \'ASD\', and the'
                ' resulting pedigree may have incomplete parentage information.', pedformat)
        # Check the sepchar to make sure that the fields aren't run all together
        if sepchar == '':
            sepchar = self.kw['sepchar']
            if self.kw['messages'] == 'verbose':
                print('[WARNING]: Invalid sepchar \'\' in NewPedigree::save(). Changed to \'%s\' to keep columns'
                      ' from running together.' % sepchar)
            logging.warning(
                'Invalid sepchar \'\' in NewPedigree::save(). Changed to \'%s\' to keep columns from running'
                ' together.', sepchar)
        # This is VERY important: never overwrite the user's data if it looks like an accidental
        # request!  If the user does not pass a filename to save() save the pedigree to a file
        # whose name is derived from, but not the same as, the original pedigree file.
        if filename == '':
            filename = '%s_saved.ped' % self.kw['filetag']
            if self.kw['messages'] == 'verbose':
                print('[WARNING]: Saving pedigree to file %s to avoid overwriting %s.' % (filename, self.kw['pedfile']))
            logging.warning('Saving pedigree to file %s to avoid overwriting %s.', filename,
                            self.kw['pedfile'])
        try:
            if not append:
                ofh = open(filename, 'w')
                if self.kw['messages'] == 'verbose':
                    print('[INFO]: Opened file %s for pedigree save at %s.' % (filename, pyp_utils.pyp_nice_time()))
                logging.info('Opened file %s for pedigree save at %s.', filename, pyp_utils.pyp_nice_time())
            else:
                ofh = open(filename, 'a')
                if self.kw['messages'] == 'verbose':
                    print('[INFO]: Opened file %s for pedigree save in append mode at %s.' % (
                        filename, pyp_utils.pyp_nice_time()))
                logging.info('Opened file %s for pedigree save in append mode at %s.', filename,
                             pyp_utils.pyp_nice_time())

            # Let the user know which pedigree format code is being used.
            if self.kw['messages'] == 'verbose':
                print('\t[INFO]: Writing pedigree file with format code %s in NewPedigree::save().' % pedformat)
            logging.info('Pedigree format code %s being used to write pedigree file %s in NewPedigree::save().',
                         pedformat, filename)

            # Write file header.
            if append:
                ofh.write('# %s created by PyPedal at %s\n' % (filename, pyp_utils.pyp_nice_time()))
                ofh.write('# Current pedigree metadata:\n')
                ofh.write('#\tpedigree file: %s\n' % filename)
                ofh.write('#\tpedigree name: %s\n' % self.kw['pedname'])
                ofh.write('#\tpedigree format: %s\n' % pedformat)
                if self.kw['pedigree_is_renumbered'] == 1:
                    if originalID:
                        ofh.write('#\tNOTE: Animal, sire, and dam IDs are original IDs!\n')
                    else:
                        ofh.write('#\tNOTE: Animal, sire, and dam IDs are renumbered IDs!\n')
                ofh.write('# Original pedigree metadata:\n')
                ofh.write('#\tpedigree file: %s\n' % self.kw['pedfile'])
                ofh.write('#\tpedigree name: %s\n' % self.kw['pedname'])
                ofh.write('#\tpedigree format: %s\n' % self.kw['pedformat'])
            for _a in self.pedigree:
                if not write_list or write_list[_a.animalID]:
                    _outstring = ''
                    for pf in pedformat:
                        if not originalID:
                            value = getattr(_a, self.new_animal_attr[pf])
                        else:
                            # if self.kw['debug_messages']:
                            #    print '[DEBUG]: Using original IDs for pedigree %s' % \
                            #    ( self.kw['pedname'] )
                            if pf in ['a', 'A']:
                                value = _a.originalID
                            # This cascade may break if the pedigree is not
                            # renumbered...
                            elif pf in ['s', 'S']:
                                if _a.sireID != self.kw['missing_parent']:
                                    value = self.pedigree[_a.sireID - 1].originalID
                                else:
                                    value = 0
                            elif pf in ['d', 'D']:
                                if _a.damID != self.kw['missing_parent']:
                                    value = self.pedigree[_a.damID - 1].originalID
                                else:
                                    value = 0
                            else:
                                value = getattr(_a, self.new_animal_attr[pf])
                        # If we don't catch the special case of the first entry
                        # in an output line a sepchar always will be the
                        # first character in the line.
                        if len(_outstring) > 0:
                            _outstring = '%s%s%s' % (_outstring, sepchar, value)
                        else:
                            _outstring = '%s' % value
                    ofh.write('%s\n' % _outstring)
            ofh.close()
            if self.kw['messages'] == 'verbose':
                print('\t[INFO]: Closed file %s after pedigree save at %s.' % (filename, pyp_utils.pyp_nice_time()))
            logging.info('Closed file %s after pedigree save at %s.', filename, pyp_utils.pyp_nice_time())
            return 1
        except:
            if self.kw['messages'] == 'verbose':
                print('[ERROR]: Unable to open file %s for pedigree save!' % filename)
            logging.error('Unable to open file %s for pedigree save.', filename)
            return 0

    ##
    # savegraph() save a pedigree to a file as an adjacency list.
    # @param self Reference to current object.
    # @param pedoutfile Name of the file to which the graph is written.
    # @param pedgraph Graph object
    # @retval None
    def savegraph(self, pedoutfile=0, pedgraph=0):
        """
        Save a pedigree to a file as an adjacency list.
        """
        if not pedoutfile:
            pedoutfile = '%s.adjlist' % (self.kw['pedfile'])
        if not pedgraph:
            try:
                from . import pyp_network
                pedgraph = pyp_network.ped_to_graph(self)
                logging.info('[savegraph]: Convert pedigree to a directed graph.')
            except:
                logging.error('[savegraph]: Unable to convert pedigree to a directed graph.')
        try:
            import networkx as nx
            nx.write_adjlist(pedgraph, pedoutfile)
        except:
            logging.error('[savegraph]: Unable to save directed graph to a file.')

    ##
    # savegedcom() save a pedigree to a file in GEDCOM 5.5 format.
    # @param self Reference to current object
    # @param pedoutfile Name of the file to which the graph is written
    # @retval None
    def savegedcom(self, pedoutfile=0):
        """
        Save a pedigree to a file in GEDCOM 5.5 format.
        """
        if not pedoutfile:
            pedoutfile = '%s.ged' % (self.kw['pedfile'])
        try:
            pyp_io.save_to_gedcom(self, pedoutfile)
            logging.info('[savegedcom]: Saved GEDCOM pedigree to the file %s.', pedoutfile)
        except:
            logging.error('[savegedcom]: Unable to save GEDCOM pedigree to the file %s.', pedoutfile)

    ##
    # savegenes() save a pedigree to a file in GENES 1.20 (dBase III) format.
    # @param self Reference to current object
    # @param pedoutfile Name of the file to which the graph is written
    # @retval None
    def savegenes(self, pedoutfile=0):
        """
        Save a pedigree to a file in GENES 1.20 (dBase III) format.
        """
        if not pedoutfile:
            pedoutfile = '%s.dbf' % (self.kw['pedfile'])
        try:
            pyp_io.save_to_genes(self, pedoutfile)
            logging.info('[savegenes]: Saved GENES pedigree to the file %s.', pedoutfile)
        except:
            logging.error('[savegenes]: Unable to save GENES pedigree to the file %s.', pedoutfile)

    ##
    # savedb() saves a pedigree to a database table in ASDx format
    # for NewAnimals and LightAnimals.
    # @param self Reference to current object.
    # @param drop Boolean indicating if existing data should be kept (False) or deleted (True); the default is False.
    # @retval _savedb_status Boolean indicating if the pedigree was successfully saved.
    def savedb(self, drop=False):
        """
        savedb() saves a pedigree to a database table in ASDx format
        for NewAnimals and LightAnimals.
        """
        _savedb_status = False
        _table_loaded = False
        _table_created = False
        # Create the database -- this will overwrite an existing DB with the
        # same name!
        if pyp_db.doesTableExist(self) and drop:
            pyp_db.deleteTable(self)
        conn = pyp_db.connectToDatabase(self)
        if conn:
            if not pyp_db.doesTableExist(self):
                try:
                    sql = 'create table %s ( \
                        animalName   varchar(128) primary key, \
                        sireName     varchar(128), \
                        damName      varchar(128), \
                        sex          char(1) \
                    );' % (self.kw['database_table'])
                    cursor = conn.Execute(sql)
                    cursor.Close()
                    _table_created = True
                except:
                    pass
            else:
                if self.kw['messages'] == 'verbose':
                    print('[WARNING]: The table %s already exists in database %s and you told me to save the'
                          ' existing data. You may end up with duplicate data or multiple pedigrees stored in'
                          ' the same table!' % (self.kw['database_table'], self.kw['database_name']))
                logging.warning(
                    'The table %s already exists in database %s and you told me to save the existing data. You'
                    ' may end up with duplicate data or multiple pedigrees stored in the same table!',
                    self.kw['database_table'], self.kw['database_name'])
            # Load the pedigree data into the table.
            if pyp_db.doesTableExist(self):
                try:
                    for p in self.pedigree:
                        an = p.name
                        si = p.sireName
                        da = p.damName
                        if si == self.kw['missing_name']:
                            si = self.kw['missing_parent']
                        if da == self.kw['missing_name']:
                            da = self.kw['missing_parent']
                        sql = ("INSERT INTO %s ( animalName, sireName, damName, sex ) VALUES ('%s', '%s', '%s', '%s')" %
                               (self.kw['database_table'], an, si, da, p.sex))
                        cursor = conn.Execute(sql)
                        cursor.Close()
                    _table_loaded = True
                except:
                    pass
            conn.Close()
        else:
            pass
        if _table_loaded:
            if self.kw['messages'] == 'verbose':
                print('[INFO]: Saved pedigree to %s.%s at %s.' % (self.kw['database_name'],
                                                                  self.kw['database_table'], pyp_utils.pyp_nice_time()))
            logging.info('Saved pedigree to %s.%s at %s.', self.kw['database_name'],
                         self.kw['database_table'], pyp_utils.pyp_nice_time())
            _savedb_status = True
        else:
            if self.kw['messages'] == 'verbose':
                print('[ERROR]: Could not save pedigree to %s.%s at %s.' % (
                    self.kw['database_name'], self.kw['database_table'], pyp_utils.pyp_nice_time()))
            logging.error('Could not save pedigree to %s.%s at %s.', self.kw['database_name'],
                          self.kw['database_table'], pyp_utils.pyp_nice_time())
        return _savedb_status

    ##
    # preprocess() processes a pedigree file, which includes reading the animals
    # into a list of animal objects, forming lists of sires and dams, and checking for
    # common errors.
    # @param self Reference to current object
    # @param textstream String containing animal records
    # @param dbstream List of tuples of animal records
    # @retval None
    def preprocess(self, textstream='', dbstream=''):
        """
        Preprocess a pedigree file, which includes reading the animals into a list, forming lists of sires and dams,
        and checking for common errors.
        """
        line_counter = 0  # count the number of lines in the pedigree file
        animal_counter = 0  # count the number of animal records in the pedigree file
        # pedformat_codes = ['a','s','d','g','x','b','f','r','n','y','l','e','p','A','S','D','L','Z','h','H','u']
        critical_count = 0  # Number of critical errors encountered
        pedformat_locations = {}  # Stores columns numbers for input data
        _sires = {}  # We need to track the sires and dams read from the pedigree
        _dams = {}  # file in order to insert records for any parents that do not
        # have their own records in the pedigree file.
        # A variable, 'pedformat, is passed as a parameter that indicates the format of the
        # pedigree in the input file.  Note that A PEDIGREE FORMAT STRING IS NO LONGER
        # REQUIRED in the input file, and any found will be ignored.  The index of the single-
        # digit code in the format string indicates the column in which the corresponding
        # variable is found.  Duplicate values in the pedformat atring are ignored.
        # print self.kw['pedformat']
        if not self.kw['pedformat']:
            self.kw['pedformat'] = 'asd'
            logging.error('Null pedigree format string assigned a default value of %s.', self.kw['pedformat'])
            if self.kw['messages'] == 'verbose':
                print('[ERROR]: Null pedigree format string assigned a default value of %s.' % (self.kw['pedformat']))
        # This is where we check the format string to figure out what we have in the input file.
        # Check for valid characters...
        _pedformat = []
        for _char in self.kw['pedformat']:
            if _char in self.pedformat_codes and _char != 'Z':
                _pedformat.append(_char)
            elif _char in self.pedformat_codes and _char == 'Z':
                _pedformat.append('.')
                if self.kw['messages'] == 'verbose':
                    print('[INFO]: Skipping one or more columns in the input file')
                logging.info(
                    'Skipping one or more columns in the input file as requested by the pedigree format string %s',
                    self.kw['pedformat'])
            else:
                # Replace the invalid code with a period, which is ignored when the string is parsed.
                _pedformat.append('.')
                if self.kw['messages'] == 'verbose':
                    print('[DEBUG]: Invalid format code, %s, encountered!' % _char)
                logging.error('Invalid column format code %s found while reading pedigree format string %s',
                              _char, self.kw['pedformat'])
        for _char in _pedformat:
            try:
                pedformat_locations['animal'] = _pedformat.index('a')
            except ValueError:
                try:
                    pedformat_locations['animal'] = _pedformat.index('A')
                except ValueError:
                    print('[CRITICAL]: No animal identification code was specified in the pedigree format string %s!'
                          ' This is a critical error and the program will halt.' % _pedformat)
                    critical_count = critical_count + 1
            try:
                pedformat_locations['sire'] = _pedformat.index('s')
            except ValueError:
                try:
                    pedformat_locations['sire'] = _pedformat.index('S')
                except ValueError:
                    print('[CRITICAL]: No sire identification code was specified in the pedigree format string %s!'
                          ' This is a critical error and the program will halt.' % _pedformat)
                    critical_count = critical_count + 1
            try:
                pedformat_locations['dam'] = _pedformat.index('d')
            except ValueError:
                try:
                    pedformat_locations['dam'] = _pedformat.index('D')
                except ValueError:
                    print('[CRITICAL]: No dam identification code was specified in the pedigree format string %s!'
                          ' This is a critical error and the program will halt.' % _pedformat)
                    critical_count = critical_count + 1
            try:
                pedformat_locations['generation'] = _pedformat.index('g')
            except ValueError:
                pedformat_locations['generation'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No generation code was specified in the pedigree format string %s. This program'
                          ' will continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['gencoeff'] = _pedformat.index('p')
                if not self.kw['gen_coeff']:
                    self.kw['gen_coeff'] = 1
            except ValueError:
                pedformat_locations['gencoeff'] = -999
                if self.kw['gen_coeff']:
                    self.kw['gen_coeff'] = 0
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No generation coefficient was specified in the pedigree format string %s. This'
                          ' program will continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['sex'] = _pedformat.index('x')
            except ValueError:
                pedformat_locations['sex'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No sex code was specified in the pedigree format string %s. This program will'
                          ' continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['birthyear'] = _pedformat.index('y')
            except ValueError:
                pedformat_locations['birthyear'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No birth date (YYYY) code was specified in the pedigree format string %s. This'
                          ' program will continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['inbreeding'] = _pedformat.index('f')
            except ValueError:
                pedformat_locations['inbreeding'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No coefficient of inbreeding code was specified in the pedigree format string %s.'
                          ' This program will continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['breed'] = _pedformat.index('r')
            except ValueError:
                pedformat_locations['breed'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No breed code was specified in the pedigree format string %s. This program will'
                          ' continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['name'] = _pedformat.index('n')
            except ValueError:
                pedformat_locations['name'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No name code was specified in the pedigree format string %s. This program will'
                          ' continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['birthdate'] = _pedformat.index('b')
            except ValueError:
                pedformat_locations['birthdate'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No birth date (MMDDYYYY) code was specified in the pedigree format string %s.'
                          ' This program will continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['alive'] = _pedformat.index('l')
            except ValueError:
                pedformat_locations['alive'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No alive/dead code was specified in the pedigree format string %s. This program'
                          ' will continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['age'] = _pedformat.index('e')
            except ValueError:
                pedformat_locations['age'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No age code was specified in the pedigree format string %s. This program will'
                          ' continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['alleles'] = _pedformat.index('L')
                if self.kw['alleles_sepchar'] == self.kw['sepchar']:
                    if self.kw['messages'] == 'all':
                        print('[DEBUG]: The same separating character was specified for both columns of input (option'
                              ' sepchar) and alleles (option alleles_sepchar) in an animal\'s allelotype. The'
                              ' allelotypes will not be used in this pedigree.')
                    logging.warning(
                        'The same separating character was specified for both columns of input (option sepchar) and'
                        ' alleles (option alleles_sepchar) in an animal\'s allelotype. The allelotypes will not be'
                        ' used in this pedigree.')
                    pedformat_locations['alleles'] = -999
            except ValueError:
                pedformat_locations['alleles'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No alleles code was specified in the pedigree format string %s. This program'
                          ' will continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['herd'] = _pedformat.index('h')
            except ValueError:
                pedformat_locations['herd'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No herd code was specified in the pedigree format string %s. This program will'
                          ' continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['herd'] = _pedformat.index('H')
            except ValueError:
                pedformat_locations['herd'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No herd code was specified in the pedigree format string %s. This program will'
                          ' continue.' % self.kw['pedformat'])
            try:
                pedformat_locations['userfield'] = _pedformat.index('u')
            except ValueError:
                pedformat_locations['userfield'] = -999
                if self.kw['messages'] == 'all':
                    print('[DEBUG]: No user-defined field was specified in the pedigree format string %s. This'
                          ' program will continue.' % self.kw['pedformat'])
        # print self.kw['pedformat']
        # print _pedformat
        # print pedformat_locations
        # If the pedigree file includes coefficients of inbreeding flag the
        # pedigree.
        if 'f' in self.kw['pedformat']:
            self.kw['f_computed'] = 1
        if critical_count > 0:
            sys.exit(0)
        else:
            if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                print('[INFO]: Opening pedigree file %s' % (self.kw['pedfile']))
            logging.info('Opening pedigree file %s', self.kw['pedfile'])
            if textstream == '' and dbstream == '':
                infile = open(self.kw['pedfile'], 'r')
            elif dbstream == '':
                # Parse the textstream
                # Note that this will cause the loss of the last record in the
                # string if that record DOES NOT have a trailing \n as the
                # documentation says it must.
                infile = textstream.split('\n')
                infile = infile[:-1]
            else:
                # dbstream is a list of tuples from a database
                infile = dbstream
                counter = 0
            while 1:
                if textstream == '' and dbstream == '':
                    line = infile.readline()  # print line
                elif dbstream == '':
                    try:
                        line = infile.pop()
                        # print 'line: %s' % ( line )
                    except IndexError:
                        logging.warning('Reached the end of the textstream after reading %s records.',
                                        line_counter)
                        line = False
                else:
                    # Do tuple unpacking on database records
                    try:
                        # dbline = dbstream.pop()
                        # Code from Matt Kelly -- dbstream.pop() didn't wprl for him on OS/X 1.0.4
                        dbline = dbstream[counter]
                        line = ','.join(dbline)
                        counter = counter + 1
                    except IndexError:
                        logging.info('Reached the end of the dbstream after reading %s records.',
                                     line_counter)
                        line = False
                if not line:
                    logging.info('Reached end-of-line in %s after reading %s lines.', self.kw['pedfile'],
                                 line_counter)
                    break
                else:
                    # 29 March 2005
                    # This causes problems b/c it eats the last column of the last record in a pedigree
                    # file.  I think I added it way back when to deal with some EOL-character annoyance,
                    # but I am not sure.  So...I am turning it off (for now).
                    # line = string.strip(line[:-1])
                    line_counter = line_counter + 1
                    if line_counter <= self.kw['log_ped_lines']:
                        logging.info('Pedigree (line %s): %s', line_counter, line.strip())
                    # This code prepends a comment character the first line of inpuit if the has_header
                    # option is set to 1.
                    if line_counter == 1 and self.kw['has_header'] == 1:
                        logging.info(
                            'Converted the first line in the input file into a comment because the pedigree file has'
                            ' a header row.')
                        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
                            print('[INFO]: Converted the first line in the input file into a comment because the'
                                  ' pedigree file has a header row.')
                        line = '# %s' % line
                    # Handle comment lines.
                    if line[0] == '#':
                        logging.info('Pedigree comment (line %s): %s', line_counter, line.strip())
                        pass
                    # Raise a warning if somebody is still using an old file with an embedded pedigree
                    # format code.
                    elif line[0] == '%':
                        self.kw['old_pedformat'] = line[1:].strip()  # this lets us specify the pedigree file format
                        logging.warning('Encountered deprecated pedigree format string (%s) on line %s of the'
                                        ' pedigree file.', line, line_counter)
                    # Thomas von Hassel sent me a pedigree whose last line was blank but for a tab.  In
                    # debugging that problem I realized that there was no check for null lines.  This 'elif'
                    # catches blank lines so that they are not treated as actual records, and logs them.
                    elif len(line.strip()) == 0:
                        logging.warning('Encountered an empty (blank) record on line %s of the pedigree file.',
                                        line_counter)
                    else:
                        animalCounter = animal_counter + 1
                        if numpy.fmod(animal_counter, self.kw['counter']) == 0:
                            logging.info('Records read: %s ', animalCounter)
                        # string.strip()-ing line deals with problems from trailing sepchars,
                        # most notably spaces. Is there a nice way to deal with the situation
                        # of multiple sepchars with no data between them?
                        # l = string.split(string.strip(line), self.kw['sepchar'])
                        l = line.strip().split(self.kw['sepchar'])

                        # print l
                        # I am adding in a check here to make sure that the number of fields
                        # expected from the pedigree format string and the number of fields in
                        # the datalines of the pedigree are the same.  If they are not, there is
                        # a problem that the user needs to handle.
                        if len(self.kw['pedformat']) == len(l):
                            self.namemap = {}
                            self.namebackmap = {}
                            # print line
                            # print l
                            # Some people *cough* Brad Heins *cough* insist on sending me pedigree
                            # files vomited out by Excel, which pads cells in a column with spaces
                            # to right-align them...
                            for i in range(len(l)):
                                l[i] = l[i].strip()
                            if len(l) < 3:
                                error_string = ('The record on line %s of file %s is too short - all records'
                                                ' must contain animal, sire, and dam ID numbers (%s fields'
                                                ' detected).\n') % (line_counter, self.kw['pedfile'], len(l))
                                print('[ERROR]: %s' % error_string)
                                print('[ERROR]: %s' % line)
                                sys.exit(0)
                            else:
                                if l[0] != self.kw['missing_parent']:
                                    if self.kw['animal_type'] == 'light':
                                        an = LightAnimal(pedformat_locations, l, self.kw)
                                    else:
                                        an = NewAnimal(pedformat_locations, l, self.kw)
                                        # print an.animalID,' ',an.sireID,' ',an.damID
                                        # an.printme()
                                else:
                                    error_string = ('The record on line %s of file %s has an animal ID that is the'
                                                    ' same as the missing value code specified for the pedigree. This'
                                                    ' animal is being skipped and will not have an entry in the'
                                                    ' pedigree.\n') % (line_counter, self.kw['pedfile'])
                                    print('[ERROR]: %s' % error_string)
                                    logging.error(error_string)
                                # print 'Animal Name: ', an.name
                                # If strings are used for sire and dam IDs we need
                                # to put the names in the _sires or _dams dictionary
                                # rather than the ID.  If we put in the IDs the
                                # missing sire and dam catcher code will not work
                                # correctly.
                                # print 'Animal ID: ', an.animalID
                                if 'S' in self.kw['pedformat']:
                                    if an.sireName != self.kw['missing_name']:
                                        _sires[an.sireName] = an.sireName
                                    else:
                                        # print '\tAnimal %s has sire %s' % ( an.animalID, an.sireID )
                                        pass
                                else:
                                    # if str(an.sireID) != str(self.kw['missing_parent']):
                                    if str(an.sireID) != str(self.kw['missing_parent']):
                                        _sires[an.sireID] = an.sireID
                                if 'D' in self.kw['pedformat']:
                                    if an.damName != self.kw['missing_name']:
                                        _dams[an.damName] = an.damName
                                    else:
                                        # print '\tAnimal %s has dam %s' % ( an.animalID, an.damID )
                                        pass
                                else:
                                    if str(an.damID) != str(self.kw['missing_parent']):
                                        _dams[an.damID] = an.damID
                                # print an.sireID
                                # print an.damID
                                self.pedigree.append(an)
                                # If strings are used for animals names we need
                                # to put those names in idmap and backmap so that
                                # the missing sire and dam assignment code will
                                # work correctly.
                                # !!! Note that this is broken if you renumber
                                # the pedigree. In that case, use the namemap
                                # to map from name to original ID, and the
                                # backmap to go from the original ID to the
                                # renumbered ID.
                                if 'A' in self.kw['pedformat']:
                                    self.idmap[an.name] = an.name
                                    self.backmap[an.name] = an.name
                                    if self.kw['animal_type'] == 'new':
                                        self.namemap[an.name] = an.name
                                        self.namebackmap[an.name] = an.name
                                else:
                                    self.idmap[an.animalID] = an.animalID
                                    self.backmap[an.animalID] = an.animalID
                                    if self.kw['animal_type'] == 'new':
                                        self.namemap[an.name] = an.animalID
                                        self.namebackmap[an.animalID] = an.name
                        else:
                            errorString = (('The record on line %s of file %s has %s columns, but the pedigree format'
                                            ' string (%s) says that it should have %s columns. Please check your'
                                            ' pedigree file and the pedigree format string for errors.\n') %
                                           (line_counter, self.kw['pedfile'], len(l), self.kw['pedformat'],
                                           len(self.kw['pedformat'])))
                            print('[ERROR]: %s' % error_string)
                            logging.error(error_string)
                            sys.exit(0)
            #
            # This is where we deal with parents with no pedigree file entry.
            # Things are kind of tricky when we are working with the S and D
            # codes.
            #
            _null_locations = pedformat_locations
            for _n in list(_null_locations.keys()):
                _null_locations[_n] = -999
            _null_locations['animal'] = 0
            _null_locations['sire'] = 1
            _null_locations['dam'] = 2
            # print _null_locations
            # print 'INFO: idmap = %s' % (self.idmap)
            # print 'INFO: _sires = %s' % (_sires)
            # print 'INFO: _dams = %s' % (_dams)
            for _s in list(_sires.keys()):
                try:
                    _i = self.idmap[_s]
                except KeyError:
                    if ('S' in self.kw['pedformat'] and str(_s) != str(self.kw['missing_name'])) or (
                                    's' in self.kw['pedformat'] and str(_s) != str(self.kw['missing_parent'])):
                        an = NewAnimal(_null_locations, [_s, self.kw['missing_parent'], self.kw['missing_parent']],
                                       self.kw)
                        # an.printme()
                        self.pedigree.append(an)
                        self.idmap[an.animalID] = an.animalID
                        self.backmap[an.animalID] = an.animalID
                        self.namemap[an.name] = an.animalID
                        self.namebackmap[an.animalID] = an.name
                        logging.info('Added pedigree entry for sire %s' % _s)
                        if self.kw['messages'] == 'verbose':
                            print('[NOTE]: Added pedigree entry for sire %s' % _s)
            for _d in list(_dams.keys()):
                try:
                    _i = self.idmap[_d]
                except KeyError:
                    if ('D' in self.kw['pedformat'] and str(_d) != str(self.kw['missing_name'])) or (
                                    'd' in self.kw['pedformat'] and str(_d) != str(self.kw['missing_parent'])):
                        an = NewAnimal(_null_locations, [_d, self.kw['missing_parent'], self.kw['missing_parent']],
                                       self.kw)
                        #                    an.printme()
                        self.pedigree.append(an)
                        self.idmap[an.animalID] = an.animalID
                        self.backmap[an.animalID] = an.animalID
                        self.namemap[an.name] = an.animalID
                        self.namebackmap[an.animalID] = an.name
                        logging.info('Added pedigree entry for dam %s' % _d)
                        if self.kw['messages'] == 'verbose':
                            print('[NOTE]: Added pedigree entry for dam %s' % _d)
            #
            # Finish up.
            #
            logging.info('Closing pedigree file')
            if textstream == '' and dbstream == '':
                infile.close()
            elif textstream == '':
                del dbstream
                del infile
            else:
                del textstream
                del infile

    ##
    # fromgraph() loads the animals to populate the pedigree from a
    # DiGraph object.
    # @param self Reference to current object.
    # @param pedgraph DiGraph object containing a pedigree.
    # @retval None
    def fromgraph(self, pedgraph):
        """
        fromgraph() loads the animals to populate the pedigree from an
        DiGraph object.
        """
        missing = ['sex', 'generation', 'gencoeff', 'birthyear',
                   'inbreeding', 'breed', 'name', 'birthdate', 'alive', 'age',
                   'alleles', 'herd', 'userfield']
        pedformat_locations = {
            'animal': 0,
            'sire': 1,
            'dam': 2,
        }
        for _m in missing:
            pedformat_locations[_m] = -999
        for _n in pedgraph.nodes():
            # print pedgraph.node[_n]
            # print 'sire: ', pedgraph.node[_n]['sire']
            # print 'dam:  ', pedgraph.node[_n]['dam']
            _s = pedgraph.node[_n]['sire']
            _d = pedgraph.node[_n]['dam']
            an = NewAnimal(pedformat_locations, [_n, _s, _d], self.kw)
            self.pedigree.append(an)
            self.idmap[an.animalID] = an.animalID
            self.backmap[an.animalID] = an.animalID
            self.namemap[an.name] = an.animalID
            self.namebackmap[an.animalID] = an.name
            if self.kw['debug_messages'] > 0:
                logging.info('Added pedigree entry for animal %s' % _n)

    ##
    # fromnull() creates a new pedigree with no animal records in it.
    # @param self Reference to current object
    # @retval None
    def fromnull(self):
        """
         fromnull() creates a new pedigree with no animal records in it.
        """
        # Let's see if it's this easy!
        logging.info('Created a null (empty) pedigree.')
        return True

    ##
    # fromanimallist() populates a NewPedigree with instances of NewAnimal objects.
    # @param self Reference to current object.
    # @param animallist A list of instances of NewAnimals.
    # @retval None
    def fromanimallist(self, animallist):
        """
        fromanimallist() populates a NewPedigree with instances of NewAnimal objects.
        """
        if len(animallist) > 0:
            # There is a lingering issue here with the pedformat. For now, we're
            # going to use my terribly clever pedformat guesser to figure it out.
            self.kw['pedformat'] = pyp_utils.guess_pedformat(animallist[0], self.kw)
            for an in animallist:
                if an.__class__.__name__ == 'NewAnimal':
                    self.pedigree.append(an)
                    self.idmap[an.animalID] = an.animalID
                    self.backmap[an.animalID] = an.animalID
                    self.namemap[an.name] = an.animalID
                    self.namebackmap[an.animalID] = an.name
                else:
                    logging.error('An entry in the animallist was not a NewAnimal object, skipping!')
                if self.kw['debug_messages'] > 0:
                    logging.info('Added pedigree entry for animal %s' % an.originalID)
        else:
            if self.kw['messages']:
                print('[ERROR]: Could not create a pedigree from an empty animal list!')
            logging.error('Could not create a pedigree from an empty animal list!')
            return False

    ##
    # tostream() creates a text stream from a pedigree.
    # @param self Reference to current object.
    # @retval None
    def tostream(self):
        """
        tostream() creates a text stream from a pedigree.
        """
        streamout = ''
        try:
            for p in self.pedigree:
                an = p.name
                si = p.sireName
                da = p.damName
                if si == self.kw['missing_name']:
                    si = self.kw['missing_parent']
                if da == self.kw['missing_name']:
                    da = self.kw['missing_parent']
                streamout = '%s%s,%s,%s\\n' % (streamout, an, si, da)
            if self.kw['messages'] == 'verbose':
                print('[INFO]: Created text stream from pedigree.')
            logging.info('Created text stream from pedigree.')
        except:
            if self.kw['messages'] == 'verbose':
                print('[ERROR]: Could not create text stream from pedigree!')
            logging.error('Could not create text stream from pedigree!')
        return streamout

    ##
    # renumber() updates the ID map after a pedigree has been renumbered so that all references
    # are to renumbered rather than original IDs.
    # @param self Reference to current object
    # @retval None
    def renumber(self):
        """
        renumber() updates the ID map after a pedigree has been renumbered so that all
        references are to renumbered rather than original IDs.
        """
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]: Renumbering pedigree at %s' % (pyp_utils.pyp_nice_time()))
            print('\t\t[INFO]: Reordering pedigree at %s' % (pyp_utils.pyp_nice_time()))
        logging.info('Reordering pedigree')
        if ('b' in self.kw['pedformat'] or 'y' in self.kw['pedformat']) and not self.kw['slow_reorder']:
            self.pedigree = pyp_utils.fast_reorder(self.pedigree)
        else:
            self.pedigree = pyp_utils.reorder(self.pedigree, missingparent=self.kw['missing_parent'],
                                              max_rounds=self.kw['reorder_max_rounds'])
        # self.pedigree = pyp_utils.reorder(self.pedigree,missingparent=self.kw['missing_parent'],
        # max_rounds=self.kw['reorder_max_rounds'])
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t\t[INFO]: Renumbering at %s' % (pyp_utils.pyp_nice_time()))
        logging.info('Renumbering pedigree')
        self.pedigree = pyp_utils.renumber(self.pedigree, missingparent=self.kw['missing_parent'],
                                           animaltype=self.kw['animal_type'])
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t\t[INFO]: Updating ID map at %s' % (pyp_utils.pyp_nice_time()))
        logging.info('Updating ID map')
        self.updateidmap()

        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]: Assigning offspring at %s' % (pyp_utils.pyp_nice_time()))
        logging.info('Assigning offspring')
        pyp_utils.assign_offspring(self)
        self.kw['pedigree_is_renumbered'] = 1
        self.kw['assign_offspring'] = 1

    ##
    # addanimal() adds a new animal of class NewAnimal to the pedigree.
    # @param self Reference to current object.
    # @param animalID ID of the new animal to be added to the pedigree.
    # @param sireID Sire ID of the new animal to be added to the pedigree.
    # @param damID Dam ID of the new animal to be added to the pedigree.
    # @retval 1 on success, 0 on failure
    def addanimal(self, animalID, sireID, damID):
        # print 'animalID: ', animalID
        # print 'sireID: ', sireID
        # print 'damID: ', damID
        _added = 0
        if not self.kw['pedigree_is_renumbered']:
            logging.warning('Adding an animal to an unrenumbered pedigree using NewPedigree::addanimal() is unsafe!')
        try:
            missing = ['sex', 'generation', 'gencoeff', 'birthyear',
                       'inbreeding', 'breed', 'name', 'birthdate', 'alive', 'age',
                       'alleles', 'herd', 'userfield']
            pedformat_locations = {
                'animal': 0,
                'sire': 1,
                'dam': 2,
            }
            for _m in missing:
                pedformat_locations[_m] = -999
            l = [animalID]
            if sireID == 0:
                l.append(self.kw['missing_parent'])
            elif 'S' in self.kw['pedformat']:
                # l.append(self.namebackmap[sireID])
                l.append(self.namebackmap[self.backmap[sireID]])
            else:
                l.append(str(sireID))
            if damID == 0:
                l.append(self.kw['missing_parent'])
            elif 'D' in self.kw['pedformat']:
                # l.append(self.namebackmap[damID])
                l.append(self.namebackmap[self.backmap[damID]])
            else:
                l.append(str(damID))
            # This is a hack. When the ASD format is used,
            # NewAnimal::__init__() will hash the animal
            # ID we pass it unless we have some way of
            # telling it that this particular animal
            # should be handled in a way that is different
            # from that specified in the pedformat.
            self.kw['newanimal_caller'] = 'addanimal'
            an = NewAnimal(pedformat_locations, l, self.kw)
            self.kw['newanimal_caller'] = 'loader'
            self.pedigree.append(an)

            # If the pedigree is renumbered, we need to
            # renumber the new animal or we'll get index
            # out of range errors.
            # print 'animalID: ', an.animalID
            an.animalID = max(self.idmap.values()) + 1
            an.renumberedID = an.animalID
            if 'n' in self.kw['pedformat']:
                an.name = self.kw['missing_name']
            if an.name == an.originalID:
                an.name = an.renumberedID
            an.sireID = self.idmap[an.sireID]
            an.damID = self.idmap[an.damID]
            # Now update the various ID and name maps
            self.idmap[an.originalID] = an.animalID
            self.backmap[an.animalID] = an.originalID
            self.namemap[an.name] = an.originalID
            self.namebackmap[an.originalID] = an.name
            # print self.idmap
            _added = 1
        except:
            _added = 0
        return _added

    ##
    # delanimal() deletes an animal from the pedigree. Note that this
    # method DOES not update the metadata attached to the pedigree
    # and should only be used if that is not important. As of 04/10/2006
    # delanimal() is intended for use by pyp_metrics/mating_coi() rather
    # than directly by users.
    # @param self Reference to current object
    # @param animalID ID of the animal to be deleted
    # @retval 1 on success, 0 on failure
    def delanimal(self, animalID):
        _deleted = 0
        if not self.kw['pedigree_is_renumbered']:
            logging.warning(
                'Deleting an animal from an unrenumbered pedigree using NewPedigree::delanimal() is unsafe!')
        try:
            anidx = self.idmap[animalID] - 1
            del (self.namebackmap[self.pedigree[anidx].originalID])
            del (self.namemap[self.pedigree[anidx].name])
            del (self.backmap[self.pedigree[anidx].renumberedID])
            del (self.idmap[animalID])
            del (self.pedigree[anidx])
            _deleted = 1
        except:
            # Should this be an assignment, e.g., "_deleted = 0"?
            # _deleted
            pass
        return _deleted

    ##
    # updateidmap() updates the ID map after a pedigree has been renumbered so that all references
    # are to renumbered rather than original IDs.
    # @param self Reference to current object
    # @retval None
    def updateidmap(self):
        """
        updateidmap() updates the ID map after a pedigree has been renumbered so that
        all references are to renumbered rather than original IDs.
        """
        # print '[updateidmap]: Entered...'
        self.idmap = {}
        self.backmap = {}
        self.namemap = {}
        self.namebackmap = {}
        for _a in self.pedigree:
            try:
                # if str(_a.originalID) == '43859378':
                #    print '[updateidmap]: originalID = 43859378'
                #    print '[updateidmap]: animalID = ', _a.animalID
                #    print '[updateidmap]: sireID = ', _a.sireID
                #    print '[updateidmap]: damID = ', _a.damID
                self.idmap[_a.originalID] = _a.animalID
                self.backmap[_a.renumberedID] = _a.originalID
                if self.kw['animal_type'] == 'new':
                    self.namemap[_a.name] = _a.originalID
                    self.namebackmap[_a.originalID] = _a.name
                    # print '%s => %s' % ( _a.renumberedID, self.backmap[_a.renumberedID] )
            except KeyError:
                pass
            #         print self.idmap
            #         print self.backmap

    ##
    # printoptions() prints the contents of the options dictionary.
    # @param self Reference to current object
    # @retval None
    def printoptions(self):
        """
        printoptions() prints the contents of the options dictionary.
        """
        print('%s OPTIONS' % (self.kw['pedname']))
        for _k, _v in self.kw.items():
            if len(_k) <= 14:
                print('\t%s:\t\t%s' % (_k, _v))
            else:
                print('\t%s:\t%s' % (_k, _v))

    ##
    # simulate() simulates an arbitrary pedigree of size n with g generations
    # starting from n_s base sires and n_d base dams.  This method is based on
    # the concepts and algorithms in the Pedigree::sample method from Matvec
    # 1.1a.  The arguments are read from the pedigree object's options
    # dictionary.
    # @param self Reference to current object
    # @retval None
    def simulate(self):
        """
        Simulate simulates an arbitrary pedigree of size n with g generations
        starting from n_s base sires and n_d base dams.  This method is based
        on the concepts and algorithms in the Pedigree::sample method from
        Matvec 1.1a (src/classes/pedigree.cpp), although all of the code in
        this implementation was written from scratch.
        """
        # import random
        if self.kw['messages'] == 'verbose':
            print('[SIMULATE]: Preparing to simulate a pedigree')
            logging.info('Preparing to simulate a pedigree')
        # If the current pedigree object has already been populated with
        # animals simulate() will not overwrite those entries.
        if len(self.pedigree) > 0:
            logging.error(
                'The simulate() method did not create a new randomly-generated pedigree because the pedigree %s has ' +
                'already been populated with animals.', self.kw['pedname']
            )
            if self.kw['messages'] == 'verbose':
                print('[ERROR]: The simulate() method did not create a new randomly-generated pedigree because the '
                      'pedigree %s has already been populated with animals.' % self.kw['pedname'])
        # Check arguments and assign defaults when invalid values are
        # provided by the user.  Write messages to the log and console
        # whenever user-specified values are overridden.
        self.kw['simulate_n'] = int(self.kw['simulate_n'])
        self.kw['simulate_g'] = int(self.kw['simulate_g'])
        self.kw['simulate_ns'] = int(self.kw['simulate_ns'])
        self.kw['simulate_nd'] = int(self.kw['simulate_nd'])
        self.kw['simulate_sr'] = float(self.kw['simulate_sr'])
        self.kw['simulate_ir'] = float(self.kw['simulate_ir'])
        self.kw['simulate_pmd'] = int(self.kw['simulate_pmd'])
        self.kw['simulate_seed'] = int(self.kw['simulate_seed'])
        if self.kw['simulate_n'] < 1:
            logging.warning(
                'You asked that a pedigree containing an invalid number of animals, %s, be simulated. The default ' +
                'number of animals, 15, is being used.', self.kw['simulate_n']
            )
            if self.kw['messages'] == 'verbose':
                print('\t[SIMULATE]: You asked that a pedigree containing an invalid number of animals, %s, be '
                      'simulated. The default number of animals, 15, is being used.' % self.kw['simulate_n'])
            self.kw['simulate_n'] = 15
        if self.kw['simulate_g'] < 1:
            logging.warning(
                'You asked that a pedigree containing an invalid number of generations, %s, be simulated. The ' +
                'default number of generations, 3, is being used.', self.kw['simulate_g']
            )
            if self.kw['messages'] == 'verbose':
                print('\t[SIMULATE]: You asked that a pedigree containing an invalid number of generations, %s, be '
                      'simulated. The default number of generations, 3, is being used.' % self.kw['simulate_g'])
            self.kw['simulate_g'] = 3
        if self.kw['simulate_ns'] < 1:
            logging.warning(
                'You asked that a pedigree containing an invalid number of sires, %s, be simulated. The default ' +
                'number of sires, 4, is being used.', self.kw['simulate_ns']
            )
            if self.kw['messages'] == 'verbose':
                print('\t[SIMULATE]: You asked that a pedigree containing an invalid number of sires, %s, be '
                      'simulated. The default number of sires, 4, is being used.' % self.kw['simulate_ns'])
            self.kw['simulate_ns'] = 4
        if self.kw['simulate_nd'] < 1:
            logging.warning(
                'You asked that a pedigree containing an invalid number of dams, %s, be simulated. The default ' +
                'number of dams, 4, is being used.', self.kw['simulate_nd']
            )
            if self.kw['messages'] == 'verbose':
                print('\t[SIMULATE]: You asked that a pedigree containing an invalid number of dams, %s, be '
                      'simulated. The default number of dams, 4, is being used.' % self.kw['simulate_nd'])
            self.kw['simulate_nd'] = 4
        if self.kw['simulate_sr'] < 0. or self.kw['simulate_sr'] > 1.:
            logging.warning(
                'You asked that a pedigree with an invalid sex ratio, %s, be simulated. The default sex ratio, 0.5,' +
                ' is being used.', self.kw['simulate_sr']
            )
            if self.kw['messages'] == 'verbose':
                print('\t[SIMULATE]: You asked that a pedigree containing an invalid sex ratio, %s, be simulated. '
                      'The default sex ratio, 0.5, is being used.' % self.kw['simulate_sr'])
            self.kw['simulate_sr'] = 0.5
        if self.kw['simulate_ir'] < 0. or self.kw['simulate_ir'] > 1.:
            logging.warning(
                'You asked that a pedigree with an invalid immigration rate, %s, be simulated. The default rate, ' +
                '0.5, is being used.', self.kw['simulate_ir']
            )
            if self.kw['messages'] == 'verbose':
                print('\t[SIMULATE]: You asked that a pedigree containing an invalid immigration rate, %s, be '
                      'simulated. The default rate, 0.5, is being used.' % self.kw['simulate_ir'])
            self.kw['simulate_ir'] = 0.5
        if self.kw['simulate_ns'] >= self.kw['simulate_n']:
            logging.error(
                'You asked that a pedigree with more founder sires than total animals be simulated.  This is a ' +
                'fatal error!'
            )
            if self.kw['messages'] == 'verbose':
                print('\t[SIMULATE]: You asked that a pedigree with more founder sires than total animals be '
                      'simulated.  This is a fatal error!')
            sys.exit(0)
        if self.kw['simulate_nd'] >= self.kw['simulate_n']:
            logging.error(
                'You asked that a pedigree with more founder dams than total animals be simulated.  This is a fatal ' +
                'error!'
            )
            if self.kw['messages'] == 'verbose':
                print('\t[SIMULATE]: You asked that a pedigree with more founder dams than total animals be '
                      'simulated.  This is a fatal error!')
            sys.exit(0)
        if (self.kw['simulate_ns'] + self.kw['simulate_ns']) > self.kw['simulate_n']:
            logging.error(
                'You asked that a pedigree with more founder parents than total animals be simulated.  This is a ' +
                'fatal error!'
            )
            if self.kw['messages'] == 'verbose':
                print('\t[SIMULATE]: You asked that a pedigree with more founder parents than total animals be '
                      'simulated.  This is a fatal error!')
            sys.exit(0)
        if self.kw['simulate_pmd'] < 1:
            logging.warning(
                'You specified an invalid number of maximum parent draws, %s. The default number of maximum draws, ' +
                '100, is being used.', self.kw['simulate_pmd']
            )
            if self.kw['messages'] == 'verbose':
                print('\t[SIMULATE]: You specified an invalid number of maximum parent draws, %s. The default '
                      'number of maximum draws, 100, is being used.' % self.kw['simulate_pmd'])
            self.kw['simulate_pmd'] = 100
        # Seed the RNG
        # seed = 5048665
        if self.kw['simulate_seed']:
            numpy.random.seed(self.kw['simulate_seed'])
            logging.info('Seeded the random number generator with the value ' + self.kw['simulate_seed'] + '.')
        else:
            _seed = int(time.time())
            numpy.random.seed(_seed)
            logging.info('Seeded the random number generator with the value ' + _seed + '.')
        # Now that we've checked the input, go ahead and setup some
        # structures that we're going to need.
        # Make local copies of the simulation defaults to save lots of typing.
        #
        # We add two to the requested number of animals because
        # one of the initial sires and dams is an unknown parent.
        # We give back simulate_n-2 animals, so the bump is needed.
        _snt = self.kw['simulate_n'] + 2
        _sng = self.kw['simulate_g']
        _sns = self.kw['simulate_ns']
        _snd = self.kw['simulate_nd']
        _ssr = self.kw['simulate_sr']
        _smp = self.kw['simulate_mp']
        _sir = self.kw['simulate_ir']
        _spo = self.kw['simulate_po']
        _sfs = self.kw['simulate_fs']
        _spmd = self.kw['simulate_pmd']
        _sff = int(round(_snt * 0.1))
        # _smd is the maximum number of daughters allowed, and is a
        # function of the number of the total number of animals in
        # the pedigree, the number of foundation sires and dams in
        # the pedigree, and the sex ratio.
        _smd = int(round((_snt - _sns - _snd) * (1 - _ssr)))
        # _sms is the maximum number of sons allowed
        _sms = int(round((_snt - _sns - _snd) * _ssr))
        # _smf is the maximum number of females allowed in the
        # pedigree, and is a function of the total number of dams,
        # total sons, total daughters, and a "fudge factor" of 10%
        # of the total pedigree size (arbitrary) that allows the
        # number of females to vary from pedigree to pedigree.  _smm
        # is the max number of males allowed in the pedigree, computed
        # similarly to _smf.
        _smf = _snd + _smd + _sff
        _smm = _sns + _sms + _sff
        # Total number of generated sires and dams? These values are
        # incremented "down below", but there are no helpful comments
        # in the Matvec source to guide me here.
        _tgdam = _snd
        _tdam = _snd
        _tgsire = _sns
        _tsire = _sns
        # These dicts will store ???
        females = []
        males = []
        # Initialize the females and males lists
        # for i in range(_smf):
        # females.append(None)
        # for i in range(_smm):
        # males.append(None)
        # Assign IDs to the sires and dams. Dam IDs range from
        # 0 .. _snd-1 and sire IDs range from _snd .. _sns-1.
        # Note that there is always a sire and a dam with ID 0.
        for i in range(_snd):
            # females[i] = i
            females.append(i)
        # print 'females:\t%s' % ( females )
        for i in range(_sns):
            if i == 0:
                # males[i] = 0
                males.append(0)
            else:
                # males[i] = _snd + i
                males.append(_snd + i)
        # print 'males:\t\t%s' % ( males )
        # Number of slots unavailable b/c they are used by sires
        # and dams.
        _totalna = _snd + _sns
        # Number of animals per generation. Each generation will
        # contain at least 1 animal. We take out the sires and
        # dams because those spots are already taken.
        _npg = ((_snt - _snd - _sns) / _sng) + 1
        # _pedholder is a temporary structure for storing
        # animal, sire, and dam IDs and sex codes.
        _pedholder = []
        # So we loop to add entries to _pedholder for the
        # sires and dams in the males and females lists.
        for i in range(_snt + 1):
            _pedholder.append(None)
        for i in range(_snd):
            _pedholder[i] = SimAnimal(females[i], 0, 0, 'f', 0)
        for i in range(_snd, _totalna):
            _pedholder[i] = SimAnimal(males[i - _snd], 0, 0, 'm', 0)

        #
        # Start of big. long generate animal loop.
        #
        # Loop over number of generations:
        for g in range(_sng):
            _tgdam = _tdam
            _tgsire = _tsire
            if _totalna >= _snt:
                break
            for _j in range(_npg):
                if _totalna >= _snt:
                    break
                # If a random uniform variate is greater than the
                # immigration rate, we need to create a new animal
                # with a sire and a dam chosen at random from the
                # males and females dictionaries, respectively.
                # if random.random() > _sir:
                if numpy.random.ranf() > _sir:
                    # The number-of-tries counter is used to
                    # track the number of draws needed to get
                    # a set of parents which meets all of the
                    # MP, OP, and FS restrictions.
                    _ntry = 0
                    while 1:
                        # print 'females:\t%s' % ( females )
                        # print 'males:\t\t%s' % ( males )
                        # Select a random sire and dam
                        # _selsire = random.randint(0,len(males)-1)
                        _selsire = numpy.random.randint(0, len(males) - 1)
                        # _seldam = random.randint(0,len(females)-1)
                        _seldam = numpy.random.randint(0, len(females) - 1)
                        # In the Matvec code, when an unknown sire or
                        # dam is selected their sire (dam) is set the
                        # same ID as the "missing parent" flag. This
                        # results in a slight bias in favor of the
                        # first non-missing sire (dam) ID. It also
                        # means that the definition of the missing
                        # parent flag as described on p. 12 of the
                        # manual is counterintuitive -- 0 indicates
                        # that missing parents are allowed, not 1. I've
                        # fixed that here in PyPedal: an MP flag of
                        # 1 indicates that MP are allowed. That's the
                        # reason for the "1 - _smp" below.
                        if _selsire == 0:
                            _selsire = 1 - _smp
                        # print '_selsire:\t%s' % ( _selsire )
                        if _seldam == 0:
                            _seldam = 1 - _smp
                        # print '_seldam:\t%s' % ( _seldam )
                        # Now we're going to store the sire and dam IDs,
                        # as well as their parents' IDs, for use in
                        # detecting parent-offspring and full-sib matings.
                        _d = females[_seldam]
                        _s = males[_selsire]
                        _dd = _pedholder[_d].damID
                        _ds = _pedholder[_d].sireID
                        _sd = _pedholder[_s].damID
                        _ss = _pedholder[_s].sireID
                        _tryagain = 0
                        # print 'Animal: %s' % ( _totalna )
                        # print 'Sire: %s' % ( _s )
                        # print 'Dam: %s' % ( _d )
                        # print 'Dam-Dam: %s' % ( _dd )
                        # print 'Dam-Sire: %s' % ( _ds )
                        # print 'Sire-Dam: %s' % ( _sd )
                        # print 'Sire-Sire: %s' % ( _ss )
                        # If offspring-parent matings are not allowed,
                        # check to see if both parents are known. If one
                        # or both is unknown, draw new samples until they
                        # are either (i) known or (ii) simulate_pmd
                        # (simulate parent max draws) is reached. If _smpd
                        # is reached, set the parents to unknown even if
                        # _smp == 0.
                        if not _spo:
                            if _d > 0:
                                if _sd == _d:
                                    # Draw a new dam
                                    _tryagain = 1
                            if _s > 0:
                                if _ss == _s:
                                    # Draw a new sire
                                    _tryagain = 1
                        # If no full-sib matings are allowed, make sure
                        # that the parents aren't brother and sister.
                        if not _sfs:
                            if _ss > 0 and _sd == 0:
                                if _ss == _ds and _sd == _dd:
                                    _tryagain = 1
                        if _tryagain:
                            _ntry = _ntry + 1
                        if _ntry > _spmd:
                            # print '> %d draws required to meet all parental restrictions. Parents set to
                            # missing.' % ( _spmd )
                            _tryagain = 0
                            _seldam = 0
                            _selsire = 0
                        # If we met the MP, PO, and FS conditions
                        # we're done and can exit the loop.
                        if not _tryagain:
                            break
                            # print '%d draws required to meet all parental restrictions.' % ( _ntry+1 )
                else:
                    # The new animal is an immigrant with unknown
                    # parents.
                    _selsire = 0
                    _seldam = 0
                # We've added an animal to the pedigree.
                _totalna = _totalna + 1

                # if random.random() < _ssr and _tgdam < _smf:
                if numpy.random.ranf() < _ssr and _tgdam < _smf:
                    _tgdam = _tgdam + 1
                    # females[_tgdam] = _totalna
                    females.append(_totalna)
                    _pedholder[_totalna] = SimAnimal(_totalna, males[_selsire], females[_seldam], 'f', g + 1)
                else:
                    if _tgsire < _smm:
                        _tgsire = _tgsire + 1
                        # males[_tgsire] = _totalna
                        males.append(_totalna)
                        _pedholder[_totalna] = SimAnimal(_totalna, males[_selsire], females[_seldam], 'm', g + 1)
                    else:
                        _tgdam = _tgdam + 1
                        # females[_tgdam] = _totalna
                        females.append(_totalna)
                        _pedholder[_totalna] = SimAnimal(_totalna, males[_selsire], females[_seldam], 'f', g + 1)
                _tdam = _tgdam
                _tsire = _tgsire
                #
                # End of long generate animal loop.
                #

                # print '_pedholder:'
                # print '\tAnimal\tSire\tDam\tSex'
                # for _ip in range(len(_pedholder)):
                # if _pedholder[_ip]:
                # _pedholder[_ip].printme()

        #
        # Now we have to put the animals into an actual pedigree object.
        #

        # First, process the pedigree format code. This is easy
        # b/c we are using SimAnimal() objects.
        self.kw['pedformat'] = 'asdxg'
        pedformat_locations = {
            'animal': 0,
            'sire': 1,
            'dam': 2,
            'sex': 3,
            'generation': 4,
            'gencoeff': -999,
            'birthyear': -999,
            'inbreeding': -999,
            'breed': -999,
            'name': -999,
            'birthdate': -999,
            'alive': -999,
            'age': -999,
            'alleles': -999,
            'herd': -999,
            'userfield': -999,
        }
        # print pedformat_locations

        for _ip in _pedholder:
            if _ip:
                # We don't want to include our missing
                # parents in the final pedigree.
                if _ip.animalID != 0:
                    # _ip.printme()
                    l = [str(_ip.animalID)]
                    # 0 is used in the simulate routine to
                    # indicate a missing parent, but the user
                    # may have specified a different MP
                    # indicator.
                    if _ip.sireID == 0:
                        l.append(self.kw['missing_parent'])
                    else:
                        l.append(str(_ip.sireID))
                    if _ip.damID == 0:
                        l.append(self.kw['missing_parent'])
                    else:
                        l.append(str(_ip.damID))
                    l.append(_ip.sex)
                    l.append(_ip.gen)
                    if self.kw['animal_type'] == 'light':
                        an = LightAnimal(pedformat_locations, l, self.kw)
                        # an.printme()
                        self.pedigree.append(an)
                        self.idmap[an.animalID] = an.animalID
                        self.backmap[an.animalID] = an.animalID
                        # self.namemap[an.name] = an.animalID
                        # self.namebackmap[an.animalID] = an.name
                    else:
                        an = NewAnimal(pedformat_locations, l, self.kw)
                        # an.printme()
                        self.pedigree.append(an)
                        self.idmap[an.animalID] = an.animalID
                        self.backmap[an.animalID] = an.animalID
                        self.namemap[an.name] = an.animalID
                        self.namebackmap[an.animalID] = an.name

        if self.kw['pedigree_save']:
            try:
                _sfn = '%s.ped' % (self.kw['filetag'])
                of = open(_sfn, 'w')
                for _ip in _pedholder:
                    if _ip and _ip.animalID != 0:
                        _ofl = '%s\n' % (_ip.stringme())
                        of.write(_ofl)
                of.close()
            except:
                pass

        # Cleanup
        del males
        del females
        del _pedholder


##
# The SimAnimal() class is a placeholder used for simulating animals.
class SimAnimal:
    """The simple class is a placeholder used for simulating animals."""

    ##
    # __init__() initializes a SimAnimal() object.
    # @param self Reference to current object.
    # @param animalID Animal's ID.
    # @param sireID Sire's ID.
    # @param damID Dam's ID.
    # @param sex Sex of animal.
    # @param gen Generation to which an animal belongs.
    # @retval An instance of a SimAnimal() object populated with data
    def __init__(self, animalID, sireID=0, damID=0, sex='u', gen=0):
        self.animalID = animalID
        self.sireID = sireID
        self.damID = damID
        self.sex = sex
        self.gen = gen

    ##
    # printme() prints a summary of the data stored in a SimAnimal() object.
    # @param self Reference to current object
    # @retval None
    def printme(self):
        try:
            print('\t%s\t%s\t%s\t%s\t%s' % (self.animalID, self.sireID,
                                            self.damID, self.sex, self.gen))
        except:
            pass

    ##
    # stringme() returns the data stored in a SimAnimal() object as a string.
    # @param self Reference to current object
    # @retval None
    def stringme(self):
        try:
            mystring = '%s %s %s %s %s' % (self.animalID, self.sireID,
                                           self.damID, self.sex, self.gen)
            return mystring
        except:
            return 0


##
# The NewAnimal() class is holds animals records read from a pedigree file.
class NewAnimal:
    """A simple class to hold animapyp_utils/union(), and pyp_utils/intersection() records read from a pedigree file."""

    ##
    # __init__() initializes a NewAnimal() object.
    # @param self Reference to current object.
    # @param locations A dictionary containing the locations of variables in the input line.
    # @param data The line of input read from the pedigree file.
    # @param mykw A dictionary of keyword arguments.
    # @retval An instance of a NewAnimal() object populated with data
    def __init__(self, locations, data, mykw):
        """
        __init__() initializes a NewAnimal() object.
        """
        # print locations
        # print data
        if locations['animal'] != -999:
            # If the animal's ID is actually a string, we need to be clever.
            # Put a copy of the string in the 'Name' field.  Then use the
            # hash function to convert the ID to an integer.
            if 'A' in mykw['pedformat']:
                if mykw['newanimal_caller'] == 'addanimal':
                    self.name = str(data[locations['animal']])
                    self.animalID = data[locations['animal']]
                    self.originalID = data[locations['animal']]
                else:
                    # If the animal ID is not a string, we have to cast it
                    # before we can strip it. At any rate, the animalName
                    # needs to be a string.
                    self.animalID = self.string_to_int(data[locations['animal']])
                    self.originalID = self.string_to_int(data[locations['animal']])
                    self.name = str(data[locations['animal']]).strip()
            else:
                if locations['name'] != -999:
                    self.name = str(data[locations['name']]).strip()
                else:
                    self.name = str(data[locations['animal']]).strip()
                self.animalID = int(str(data[locations['animal']]).strip())
                self.originalID = int(str(data[locations['animal']]).strip())
        if locations['sire'] != -999 and str(data[locations['sire']]) != str(mykw['missing_parent']):
            if 'S' in mykw['pedformat']:
                self.sireID = self.string_to_int(data[locations['sire']])
            else:
                # We need to check types before trying to strip IDs. If the
                # ID is an integer, we're going to let the int() function
                # eat any leading or trailing whitespace.
                # if type(data[locations['sire']]) == 'str':
                if isinstance(data[locations['sire']], str):
                    self.sireID = int(data[locations['sire']].strip())
                else:
                    self.sireID = int(data[locations['sire']])
            # If the sire ID is not a string, we have to cast it before we
            # can strip it. At any rate, the sireName needs to be a string.
            # if type(data[locations['sire']]) == 'str':
            if isinstance(data[locations['sire']], str):
                self.sireName = data[locations['sire']].strip()
            else:
                self.sireName = str(data[locations['sire']]).strip()
        else:
            self.sireID = mykw['missing_parent']
            self.sireName = mykw['missing_name']
        if locations['dam'] != -999 and str(data[locations['dam']]) != str(mykw['missing_parent']):
            if 'D' in mykw['pedformat']:
                self.damID = self.string_to_int(str(data[locations['dam']]))
            else:
                # if type(data[locations['dam']]) == 'str':
                if isinstance(data[locations['dam']], str):
                    self.damID = int(data[locations['dam']].strip())
                else:
                    self.damID = int(data[locations['dam']])
            # if type(data[locations['dam']]) == 'str':
            if isinstance(data[locations['dam']], str):
                self.damName = data[locations['dam']].strip()
            else:
                self.damName = str(data[locations['dam']]).strip()
        else:
            self.damID = mykw['missing_parent']
            self.damName = mykw['missing_name']
        if locations['generation'] != -999:
            self.gen = data[locations['generation']]
        else:
            # self.gen = -999
            self.gen = mykw['missing_gen']
        if locations['gencoeff'] != -999.:
            self.gencoeff = data[locations['gencoeff']]
        else:
            # self.gencoeff = -999.
            self.gencoeff = mykw['missing_gencoeff']
        if locations['sex'] != -999:
            self.sex = data[locations['sex']].strip().lower()
        else:
            self.sex = mykw['missing_sex']
        if locations['birthdate'] != -999:
            self.bd = data[locations['birthdate']].strip()
        else:
            self.bd = mykw['missing_bdate']
        if locations['birthyear'] != -999:
            self.by = int(data[locations['birthyear']].strip())
            if self.by == 0:
                self.by = mykw['missing_byear']
        elif locations['birthyear'] == -999 and locations['birthdate'] != -999:
            self.by = int(data[locations['birthdate']].strip()[:4])
        else:
            self.by = mykw['missing_byear']
        if locations['inbreeding'] != -999:
            self.fa = float(data[locations['inbreeding']].strip())
        else:
            # self.fa = 0.
            self.fa = mykw['missing_inbreeding']
        if locations['breed'] != -999:
            self.breed = data[locations['breed']].strip()
        else:
            self.breed = mykw['missing_breed']
        if locations['age'] != -999:
            self.age = int(data[locations['age']].strip())
        else:
            # self.age = -999
            self.age = mykw['missing_age']
        if locations['alive'] != -999:
            self.alive = int(data[locations['alive']].strip())
        else:
            # self.alive = 0
            self.alive = mykw['missing_alive']
        if locations['herd'] != -999:
            if 'H' in mykw['pedformat']:
                self.herd = self.string_to_int(data[locations['herd']])
            else:
                self.herd = int(data[locations['herd']].strip())
            self.originalHerd = data[locations['herd']].strip()
        else:
            self.herd = self.string_to_int(mykw['missing_herd'])
            self.originalHerd = mykw['missing_herd']
        self.renumberedID = -999
        self.igen = mykw['missing_igen']
        if str(self.sireID) == str(mykw['missing_parent']) and str(self.damID) == str(mykw['missing_parent']):
            self.founder = 'y'
        else:
            self.founder = 'n'
        self.paddedID = self.pad_id()
        self.ancestor = 0
        self.sons = {}
        self.daus = {}
        self.unks = {}
        # Assign alleles for use in gene-dropping runs.  Automatically assign two
        # distinct alleles to founders.
        if locations['alleles'] != -999:
            self.alleles = [data[locations['alleles']].split(mykw['alleles_sepchar'])[0],
                            data[locations['alleles']].split(mykw['alleles_sepchar'])[1]]
        else:
            # Founders contribute two novel alleles
            if self.founder == 'y':
                _allele_1 = '%s%s' % (self.paddedID, '__1')
                _allele_2 = '%s%s' % (self.paddedID, '__2')
                self.alleles = [_allele_1, _allele_2]
            # Half-founders contribute one novel allele
            elif self.sireID == mykw['missing_parent']:
                _allele_1 = '%s%s' % (self.paddedID, '__1')
                _allele_2 = ''
                self.alleles = [_allele_1, _allele_2]
            elif self.damID == mykw['missing_parent']:
                _allele_1 = ''
                _allele_2 = '%s%s' % (self.paddedID, '__2')
                self.alleles = [_allele_1, _allele_2]
            else:
                # self.alleles = ['','']
                self.alleles = mykw['missing_alleles']
                # self.pedcomp = -999.9
            self.pedcomp = mykw['missing_pedcomp']
        if locations['userfield'] != -999:
            self.userField = data[locations['userfield']].strip()
        else:
            # self.userField = ''
            self.userField = mykw['missing_userfield']
            # print '%s\t%s\t%s' % (self.animalID, self.sireID, self.damID)

    ##
    # __equals() is used to determine if two NewAnimal objects are identical.
    # I think that the way to do this may be to hash both objects and do some
    # sort of checksum comparison. Assuming that NewAnimals are hashable...
    def __equals__(self, other):
        if self.__class__.__name__ == 'NewAnimal' and other.__class__.__name__ == 'NewAnimal':
            logging.info('Testing animals %s and %s for equality', self.animalID,
                         other.animalID)
        # if self.kw['debug_messages']:
        #     print('[DEBUG]: self and other both are NewAnimal objects. We can test them for equality.')
        # The naive way to do this is to compare each attribute of the two animals
        # to determine if they're identical. This seems inelegant...
        #
        # Need to think about this -- sires and dams can be the same but have
        # different sireID and damID because those are renumbered IDs.
        is_equal = True
        # if self.animalID != other.animalID:
        #     is_equal = False
        if self.name != other.name:
            is_equal = False
        # if self.sireID != other.sireID:
        #   is_equal = False
        if self.sireName != other.sireName:
            is_equal = False
        # if self.damID != other.damID:
        #   is_equal = False
        if self.damName != other.damName:
            is_equal = False
        if self.gen != other.gen:
            is_equal = False
        if self.gencoeff != other.gencoeff:
            is_equal = False
        if self.igen != other.igen:
            is_equal = False
        if self.by != other.by:
            is_equal = False
        if self.bd != other.bd:
            is_equal = False
        if self.sex != other.sex:
            is_equal = False
        if self.fa != other.fa:
            is_equal = False
        if self.founder != other.founder:
            is_equal = False
        if self.sons != other.sons:
            is_equal = False
        if self.daus != other.daus:
            is_equal = False
        if self.unks != other.unks:
            is_equal = False
        if self.ancestor != other.ancestor:
            is_equal = False
        if self.alleles != other.alleles:
            is_equal = False
        if self.originalID != other.originalID:
            is_equal = False
        # if self.renumberedID != other.renumberedID:
        #   is_equal = False
        if self.pedcomp != other.pedcomp:
            is_equal = False
        if self.breed != other.breed:
            is_equal = False
        if self.age != other.age:
            is_equal = False
        if self.alive != other.alive:
            is_equal = False
        if self.herd != other.herd:
            is_equal = False
        if self.originalHerd != other.originalHerd:
            is_equal = False
        if self.userField != other.userField:
            is_equal = False
        return is_equal

    ##
    # The NewAnimal class is not iterable, so raise an exception if anyonw tries it.
    # @param self Reference to current object
    # @retval None
    def __iter__(self):
        raise Exception("The NewAnimal class is not iterable")

    ##
    # printme() prints a summary of the data stored in the NewAnimal() object.
    # @param self Reference to current object
    # @retval None
    def printme(self):
        """
        Print the contents of an animal record - used for debugging.
        """
        print('ANIMAL %s RECORD' % self.animalID)
        print('\tAnimal ID:\t%s' % self.animalID)
        print('\tAnimal name:\t%s' % self.name)
        print('\tSire ID:\t%s' % self.sireID)
        print('\tSire name:\t%s' % self.sireName)
        print('\tDam ID:\t\t%s' % self.damID)
        print('\tDam name:\t%s' % self.damName)
        print('\tGeneration:\t%s' % self.gen)
        print('\tGen coeff:\t%s' % self.gencoeff)
        print('\tInferred gen.:\t%s' % self.igen)
        print('\tBirth Year:\t%s' % self.by)
        print('\tBirth Date:\t%s' % self.bd)
        print('\tSex:\t\t%s' % self.sex)
        print('\tCoI (f_a):\t%s' % self.fa)
        print('\tFounder:\t%s' % self.founder)
        print('\tSons:\t\t%s' % self.sons)
        print('\tDaughters:\t%s' % self.daus)
        print('\tUnknowns:\t%s' % self.unks)
        print('\tAncestor:\t%s' % self.ancestor)
        print('\tAlleles:\t%s' % self.alleles)
        print('\tOriginal ID:\t%s' % self.originalID)
        print('\tRenumbered ID:\t%s' % self.renumberedID)
        print('\tPedigree Comp.:\t%s' % self.pedcomp)
        print('\tBreed:\t%s' % self.breed)
        print('\tAge:\t%s' % self.age)
        print('\tAlive:\t%s' % self.alive)
        print('\tHerd:\t%s' % self.herd)
        print('\tHerd name:\t%s' % self.originalHerd)
        if self.userField != '':
            print('\tUser field:\t%s' % self.userField)

    ##
    # stringme() returns a summary of the data stored in the NewAnimal() object
    # as a string.
    # @param self Reference to current object
    # @retval None
    def stringme(self):
        """
        Return the contents of an animal record as a string.
        """
        _me = ''
        _me = '%s%s' % (_me, 'ANIMAL %s RECORD\n' % int(self.animalID))
        _me = '%s%s' % (_me, '\tAnimal ID:\t%s\n' % int(self.animalID))
        _me = '%s%s' % (_me, '\tAnimal name:\t%s\n' % self.name)
        _me = '%s%s' % (_me, '\tSire ID:\t%s\n' % int(self.sireID))
        _me = '%s%s' % (_me, '\tSire name:\t%s\n' % self.sireName)
        _me = '%s%s' % (_me, '\tDam ID:\t\t%s\n' % int(self.damID))
        _me = '%s%s' % (_me, '\tDam name:\t%s\n' % self.damName)
        _me = '%s%s' % (_me, '\tGeneration:\t%s\n' % self.gen)
        _me = '%s%s' % (_me, '\tGen coeff:\t%s\n' % self.gencoeff)
        _me = '%s%s' % (_me, '\tInferred gen.:\t%s\n' % self.igen)
        _me = '%s%s' % (_me, '\tBirth Year:\t%s\n' % int(self.by))
        _me = '%s%s' % (_me, '\tBirth Date:\t%s\n' % int(self.bd))
        _me = '%s%s' % (_me, '\tSex:\t\t%s\n' % self.sex)
        _me = '%s%s' % (_me, '\tCoI (f_a):\t%s\n' % self.fa)
        _me = '%s%s' % (_me, '\tFounder:\t%s\n' % self.founder)
        _me = '%s%s' % (_me, '\tSons:\t\t%s\n' % self.sons)
        _me = '%s%s' % (_me, '\tDaughters:\t%s\n' % self.daus)
        _me = '%s%s' % (_me, '\tUnknowns:\t%s\n' % self.unks)
        _me = '%s%s' % (_me, '\tAncestor:\t%s\n' % self.ancestor)
        _me = '%s%s' % (_me, '\tAlleles:\t%s\n' % self.alleles)
        _me = '%s%s' % (_me, '\tOriginal ID:\t%s\n' % self.originalID)
        _me = '%s%s' % (_me, '\tRenumbered ID:\t%s\n' % self.renumberedID)
        _me = '%s%s' % (_me, '\tPedigree Comp.:\t%s\n' % self.pedcomp)
        _me = '%s%s' % (_me, '\tBreed:\t%s' % self.breed)
        _me = '%s%s' % (_me, '\tAge:\t%s' % self.age)
        _me = '%s%s' % (_me, '\tAlive:\t%s' % self.alive)
        _me = '%s%s' % (_me, '\tHerd:\t%s\n' % self.herd)
        _me = '%s%s' % (_me, '\tHerd name:\t%s\n' % self.originalHerd)
        if self.originalHerd != '':
            _me = '%s%s' % (_me, '\tUser field:\t%s\n' % self.userField)
        return _me

    ##
    # dictme() returns a summary of the data stored in the NewAnimal() object
    # as a dictionary.
    # @param self Reference to current object
    # @retval None
    def dictme(self):
        """
        Return the contents of an animal record in a dictionary.
        """
        try:
            _dict = {
                'animalID': self.animalID,
                'name:': self.name,
                'sireID': self.sireID,
                'sireName': self.sireName,
                'damID': self.damID,
                'damName': self.damName,
                'gen': self.gen,
                'gencoeff': self.gencoeff,
                'igen': self.igen,
                'by': self.by,
                'bd': self.bd,
                'sex': self.sex,
                'fa': self.fa,
                'founder': self.founder,
                'sons': self.sons,
                'daus': self.daus,
                'unks': self.unks,
                'ancestor': self.ancestor,
                'alleles': self.alleles,
                'originalID': self.originalID,
                'renumberedID': self.renumberedID,
                'pedcomp': self.pedcomp,
                'breed': self.breed,
                'age': self.age,
                'alive': self.alive,
                'herd': self.herd,
                'originalHerd': self.originalHerd,
                'userField': self.userField,
            }
            return _dict
        except:
            return {}

    ##
    # trap() checks for common errors in NewAnimal() objects
    # @param self Reference to current object
    # @retval None
    def trap(self):
        """
        Trap common errors in pedigree file entries.
        """
        if int(self.animalID) == int(self.sireID):
            print('[ERROR]: Animal %s has an ID number equal to its sire\'s ID (sire ID %s).\n' % (
                self.animalID, self.sireID))
        if int(self.animalID) == int(self.damID):
            print('[ERROR]: Animal %s has an ID number equal to its dam\'s ID (dam ID %s).\n' % (
                self.animalID, self.damID))
        if int(self.animalID) < int(self.sireID):
            print('[ERROR]: Animal %s is older than its sire (sire ID %s).\n' % (self.animalID, self.sireID))
        if int(self.animalID) < int(self.damID):
            print('[ERROR]: Animal %s is older than its dam (dam ID %s).\n' % (self.animalID, self.damID))

    ##
    # pad_id() takes an Animal ID, pads it to fifteen digits, and prepends the birthyear
    # (or 1950 if the birth year is unknown).  The order of elements is: birthyear, animalID,
    # count of zeros, zeros.
    # @param self Reference to current object
    # @retval A padded ID number that is supposed to be unique across animals
    def pad_id(self):
        """
        Take an Animal ID, pad it to fifteen digits, and prepend the birthyear (or 1900
        if the birth year is unknown).  The order of elements is: birthyear, animalID,
        count of zeros, zeros.
        """
        # print 'Animal ID: ', self.animalID
        l = len(str(self.animalID))
        pl = 15 - l - 1
        if pl > 0:
            zs = '0' * pl
            pid = '%s%s%s%s' % (self.by, zs, self.animalID, l)
        else:
            pid = '%s%s%s' % (self.by, self.animalID, l)
        return pid

    ##
    # string_to_int() takes an Animal/Sire/Dam ID as a string and returns a
    # hash.
    # @param self Reference to current object.
    # @param idstring String to be hashed using the Python hashlib MD5 implementation.
    # @param mymaxint Constant used by earlier iterations of this function.
    # @retval A hashed value representing the input string.
    def string_to_int(self, idstring, mymaxint=9223372036854775807):
        """
        Convert a string to an integer.
        """
        # This algorithm is taken from "Character String Keys" in "Data
        # Structures and Algorithms with Object-Oriented Design Patterns
        # in Python" by Bruno R. Preiss:
        # http://www.brpreiss.com/books/opus7/html/page220.html#progstrnga
        # shift = 6
        # mask = ~0 << ( 31 - shift )
        # result = 0
        # for c in idstring:
        #    result = ( ( result & mask ) ^ result << shift ^ ord(c) ) & sys.maxint

        # This is a test to try and fix the problems on Mac OS/X and Windows.
        # import md5
        import hashlib
        try:
            # If we can, let's use the Python MD5 implementation
            # md5hash = md5.md5(idstring)
            result = hashlib.md5(idstring).hexdigest()
            # result = string.atoi(md5hash.hexdigest(),16)
        except:
            # If we have some sort of problem with the MD5 hash then try this.
            # WARNING -- This algorithm was broken on Mac OS/X and Windows,
            # but not on (some) Linuxes. The problem may have been related to
            # platform-specific values of sys.maxint, so I've hard-coded that
            # as sys.maxint from a 64-bit system. It gets cast to a long on 32-
            # bit platforms, but I haven't found that to be a problem -- yet.
            #
            # This algorithm is taken from "Character String Keys" in "Data
            # Structures and Algorithms with Object-Oriented Design Patterns
            # in Python" by Bruno R. Preiss:
            # http://www.brpreiss.com/books/opus7/html/page220.html#progstrnga
            shift = 6
            mask = ~0 << (31 - shift)
            result = 0
            for c in idstring:
                result = ((result & mask) ^ result << shift ^ ord(c)) & mymaxint
        return result


##
# The LightAnimal() class holds animals records read from a pedigree file. It
# is a much simpler object than the NewAnimal() object and is intended for use
# with the graph theoretic routines in pyp_network. The only attributes of these
# objects are: animal ID, sire ID, dam ID, original ID, birth year, and sex.
class LightAnimal:
    """
    The LightAnimal() class holds animals records read from a pedigree file. It
    is a much simpler object than the NewAnimal() object and is intended for use
    with the graph theoretic routines in pyp_network. The only attributes of these
    objects are: animal ID, sire ID, dam ID, original ID, birth year, and sex.A simple class to
    hold animals records read from a pedigree file.
    """

    ##
    # __init__() initializes a LightAnimal() object.
    # @param self Reference to current object.
    # @param locations A dictionary containing the locations of variables in the input line.
    # @param data The line of input read from the pedigree file.
    # @param mykw A dictionary of keyword arguments.
    # @retval An instance of a LightAnimal() object populated with data
    def __init__(self, locations, data, mykw):
        """
        __init__() initializes a LightAnimal() object.
        """
        if locations['animal'] != -999:
            # If the animal's ID is actually a string, we need to be clever.  Put a copy of
            # the string in the 'Name' field.  Then use the hash function to convert the ID
            # to an integer.
            if 'A' in mykw['pedformat']:
                self.animalID = self.string_to_int(data[locations['animal']])
                self.originalID = self.string_to_int(data[locations['animal']])
            else:
                self.animalID = data[locations['animal']].strip()
                self.originalID = data[locations['animal']].strip()
        if locations['sire'] != -999 and data[locations['sire']].strip() != mykw['missing_parent']:
            if 'S' in mykw['pedformat']:
                if data[locations['sire']] == mykw['missing_parent']:
                    self.sireID = data[locations['sire']]
                else:
                    self.sireID = self.string_to_int(data[locations['sire']])
            else:
                self.sireID = data[locations['sire']].strip()
        else:
            # self.sireID = '0'
            self.sireID = mykw['missing_parent']
        if locations['dam'] != -999 and data[locations['dam']].strip() != mykw['missing_parent']:
            if 'D' in mykw['pedformat']:
                if data[locations['dam']] == mykw['missing_parent']:
                    self.damID = data[locations['dam']]
                else:
                    self.damID = self.string_to_int(data[locations['dam']])
            else:
                self.damID = data[locations['dam']].strip()
        else:
            # self.damID = '0'
            self.damID = mykw['missing_parent']
        if locations['sex'] != -999:
            self.sex = data[locations['sex']].strip()
        else:
            self.sex = 'u'
        if locations['birthyear'] != -999:
            self.by = int(data[locations['birthyear']].strip())
            if self.by == 0:
                self.by = mykw['missing_byear']
        elif locations['birthyear'] == -999 and locations['birthdate'] != -999:
            self.by = int(data[locations['birthdate']].strip())
            self.by = self.by[:4]
        else:
            self.by = mykw['missing_byear']
        self.paddedID = self.pad_id()

    ##
    # printme() prints a summary of the data stored in the LightAnimal() object.
    # @param self Reference to current object
    # @retval None
    def printme(self):
        """
        Print the contents of an animal record - used for debugging.
        """
        print('ANIMAL %s RECORD' % (int(self.animalID)))
        print('\tAnimal ID:\t%s' % (int(self.animalID)))
        print('\tSire ID:\t%s' % (int(self.sireID)))
        print('\tDam ID:\t\t%s' % (int(self.damID)))
        print('\tBirth Year:\t%s' % (int(self.by)))
        print('\tSex:\t\t%s' % self.sex)
        print('\tOriginal ID:\t%s' % self.originalID)
        try:
            print('\tRenumbered ID:\t%s' % self.renumberedID)
        except AttributeError:
            pass

    ##
    # stringme() returns a summary of the data stored in the LightAnimal() object
    # as a string.
    # @param self Reference to current object.
    # @retval A string containing the contents of a LightAnimal object.
    def stringme(self):
        """
        Return the contents of an animal record as a string.
        """
        _me = ''
        _me = '%s%s' % (_me, 'ANIMAL %s RECORD\n' % (int(self.animalID)))
        _me = '%s%s' % (_me, '\tAnimal ID:\t%s\n' % (int(self.animalID)))
        _me = '%s%s' % (_me, '\tSire ID:\t%s\n' % (int(self.sireID)))
        _me = '%s%s' % (_me, '\tDam ID:\t\t%s\n' % (int(self.damID)))
        _me = '%s%s' % (_me, '\tBirth Year:\t%s\n' % (int(self.by)))
        _me = '%s%s' % (_me, '\tSex:\t\t%s\n' % self.sex)
        _me = '%s%s' % (_me, '\tOriginal ID:\t%s\n' % self.originalID)
        try:
            _me = '%s%s' % (_me, '\tRenumbered ID:\t%s\n' % self.renumberedID)
        except AttributeError:
            pass
        return _me

    ##
    # dictme() returns a summary of the data stored in the NewAnimal() object
    # as a dictionary.
    # @param self Reference to current object
    # @retval A dictionary containing the contents of a LightAnimal object.
    def dictme(self):
        """
        Return the contents of an animal record in a dictionary.
        """
        try:
            _dict = {
                'animalID': self.animalID,
                'sireID': self.sireID,
                'damID': self.damID,
                'by': self.by,
                'sex': self.sex,
                'originalID': self.originalID,
            }
            try:
                _dict['renumberedID'] = self.renumberedID
            except AttributeError:
                pass
            return _dict
        except:
            return {}

    ##
    # trap() checks for common errors in LightAnimal() objects
    # @param self Reference to current object
    # @retval None
    def trap(self):
        """
        Trap common errors in pedigree file entries.
        """
        if int(self.animalID) == int(self.sireID):
            print('[ERROR]: Animal %s has an ID number equal to its sire\'s ID (sire ID %s).\n' % (
                self.animalID, self.sireID))
        if int(self.animalID) == int(self.damID):
            print('[ERROR]: Animal %s has an ID number equal to its dam\'s ID (dam ID %s).\n' % (
                self.animalID, self.damID))
        if int(self.animalID) < int(self.sireID):
            print('[ERROR]: Animal %s is older than its sire (sire ID %s).\n' % (self.animalID, self.sireID))
        if int(self.animalID) < int(self.damID):
            print('[ERROR]: Animal %s is older than its dam (dam ID %s).\n' % (self.animalID, self.damID))

    ##
    # pad_id() takes an Animal ID, pads it to fifteen digits, and prepends the birthyear
    # (or 1950 if the birth year is unknown).  The order of elements is: birthyear, animalID,
    # count of zeros, zeros.
    # @param self Reference to current object
    # @retval A padded ID number that is supposed to be unique across animals
    def pad_id(self):
        """
        Take an Animal ID, pad it to fifteen digits, and prepend the birthyear (or 1900
        if the birth year is unknown).  The order of elements is: birthyear, animalID,
        count of zeros, zeros.
        """
        # print self.animalID
        l = len(self.animalID)
        pl = 15 - l - 1
        if pl > 0:
            zs = '0' * pl
            pid = '%s%s%s%s' % (self.by, zs, self.animalID, l)
        else:
            pid = '%s%s%s' % (self.by, self.animalID, l)
        return pid

    ##
    # string_to_int() takes an Animal/Sire/Dam ID as a string and returns a
    # hash.
    # @param self Reference to current object.
    # @param idstring String to be hashed using the Python hashlib MD5 implementation.
    # @param mymaxint Constant used by earlier iterations of this function.
    # @retval A hashed value representing the input string.
    def string_to_int(self, idstring, mymaxint=9223372036854775807):
        """
        Convert a string to an integer.
        """
        # This algorithm is taken from "Character String Keys" in "Data
        # Structures and Algorithms with Object-Oriented Design Patterns
        # in Python" by Bruno R. Preiss:
        # http://www.brpreiss.com/books/opus7/html/page220.html#progstrnga
        # shift = 6
        # mask = ~0 << ( 31 - shift )
        # result = 0
        # for c in idstring:
        #    result = ( ( result & mask ) ^ result << shift ^ ord(c) ) & sys.maxint

        # This is a test to try and fix the problems on Mac OS/X and Windows.
        # import md5
        import hashlib
        try:
            # If we can, let's use the Python MD5 implementation
            # md5hash = md5.md5(idstring)
            result = hashlib.md5(idstring).hexdigest()
            # result = string.atoi(md5hash.hexdigest(),16)
        except:
            # If we have some sort of problem with the MD5 hash then try this.
            # WARNING -- This algorithm was broken on Mac OS/X and Windows,
            # but not on 9some) Linuxes. The problem may have been related to
            # platform-specific values of sys.maxint, so I've hard-coded that
            # as sys.maxint from a 64-bit system. It gets cast to a long on 32-
            # bit platforms, but I haven't found that to be a problem -- yet.
            #
            # This algorithm is taken from "Character String Keys" in "Data
            # Structures and Algorithms with Object-Oriented Design Patterns
            # in Python" by Bruno R. Preiss:
            # http://www.brpreiss.com/books/opus7/html/page220.html#progstrnga
            shift = 6
            mask = ~0 << (31 - shift)
            result = 0
            for c in idstring:
                result = ((result & mask) ^ result << shift ^ ord(c)) & mymaxint
        return result


##
# The PedigreeMetadata() class stores metadata about pedigrees.  Hopefully this will help improve performance in
# some procedures, as well as provide some useful summary data.
class PedigreeMetadata:
    """A class to hold pedigree metadata. Hopefully this will help improve performance in some procedures, as well as
    provide some useful summary data."""

    ##
    # __init__() initializes a PedigreeMetadata object.
    # @param self Reference to current object.
    # @param myped A PyPedal pedigree.
    # @param kw A dictionary of options.
    # @retval An instance of a Pedigree() object populated with data.
    def __init__(self, myped, kw):
        """
        Initialize a pedigree record.
        """
        self.kw = kw
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Instantiating a new PedigreeMetadata() object...')
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Naming the Pedigree()...')
        self.name = kw['pedname']
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Assigning a filename...')
        self.filename = kw['pedfile']
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Attaching a pedigree...')
        self.myped = myped
        if kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Setting the pedcode...')
        self.pedcode = kw['pedformat']
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Counting the number of animals in the pedigree...')
        self.num_records = len(self.myped)
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Counting and finding unique sires...')
        self.num_unique_sires, self.unique_sire_list = self.nus()
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Counting and finding unique dams...')
        self.num_unique_dams, self.unique_dam_list = self.nud()
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Setting renumbered flag...')
        self.renumbered = kw['renumber']
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Counting and finding unique generations...')
        self.num_unique_gens, self.unique_gen_list = self.nug()
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Counting and finding unique birthyears...')
        self.num_unique_years, self.unique_year_list = self.nuy()
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Counting and finding unique founders...')
        self.num_unique_founders, self.unique_founder_list = self.nuf()
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Counting and finding unique herds...')
        self.num_unique_herds, self.unique_herd_list = self.nuherds()
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary']:
            print('\t[INFO]:  Detaching pedigree...')
        self.myped = []

    ##
    # printme() prints a summary of the metadata stored in the Pedigree() object.
    # @param self Reference to current object
    # @retval None
    def printme(self):
        """
        Print the pedigree metadata.
        """
        print('Metadata for %s (%s)' % (self.name, self.filename))
        print('\tRecords:\t\t%s' % self.num_records)
        print('\tUnique Sires:\t\t%s' % self.num_unique_sires)
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary'] > 1:
            print('\tSires:\t\t%s' % self.unique_sire_list)
        print('\tUnique Dams:\t\t%s' % self.num_unique_dams)
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary'] > 1:
            print('\tDams:\t\t%s' % self.unique_dam_list)
        print('\tUnique Gens:\t\t%s' % self.num_unique_gens)
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary'] > 1:
            print('\tGenerations:\t\t%s' % self.unique_gen_list)
        print('\tUnique Years:\t\t%s' % self.num_unique_years)
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary'] > 1:
            print('\tYear:\t\t%s' % self.unique_year_list)
        print('\tUnique Founders:\t%s' % self.num_unique_founders)
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary'] > 1:
            print('\tFounders:\t\t%s' % self.unique_founder_list)
        print('\tUnique Herds:\t\t%s' % self.num_unique_herds)
        if self.kw['messages'] == 'verbose' and self.kw['pedigree_summary'] > 1:
            print('\tHerds:\t\t%s' % self.unique_herd_list)
        print('\tPedigree Code:\t\t%s' % self.pedcode)

    ##
    # stringme() returns a summary of the metadata stored in the pedigree as
    # a string.
    # @param self Reference to current object.
    # @retval A summary of the metadata stored in the pedigree as a string.
    def stringme(self):
        """
        Build a string from the pedigree metadata.
        """
        _me = ''
        _me = '%s%s' % (_me, 'PEDIGREE %s (%s)\n' % (self.name, self.filename))
        _me = '%s%s' % (_me, '\tRecords:\t\t\t%s\n' % self.num_records)
        _me = '%s%s' % (_me, '\tUnique Sires:\t\t%s\n' % self.num_unique_sires)
        _me = '%s%s' % (_me, '\tUnique Dams:\t\t%s\n' % self.num_unique_dams)
        _me = '%s%s' % (_me, '\tUnique Gens:\t\t%s\n' % self.num_unique_gens)
        _me = '%s%s' % (_me, '\tUnique Years:\t\t%s\n' % self.num_unique_years)
        _me = '%s%s' % (_me, '\tUnique Founders:\t%s\n' % self.num_unique_founders)
        _me = '%s%s' % (_me, '\tUnique Herds:\t%s\n' % self.num_unique_herds)
        _me = '%s%s' % (_me, '\tPedigree Code:\t\t%s\n' % self.pedcode)
        return _me

    ##
    # fileme() writes the metada stored in the Pedigree() object to disc.
    # @param self Reference to current object
    # @retval None
    def fileme(self):
        """
        Save the pedigree metadata to a file.
        """
        outputfile = '%s%s%s' % (self.name, '_ped_metadata_', '.dat')
        aout = open(outputfile, 'w')
        line = '=' * 60 + '\n'
        aout.write('%s\n' % line)
        aout.write('PEDIGREE %s (%s)\n' % (self.name, self.filename))
        aout.write('\tPedigree Code:\t%s\n' % self.pedcode)
        aout.write('\tRecords:\t%s\n' % self.num_records)
        aout.write('\tUnique Sires:\t%s\n' % self.num_unique_sires)
        aout.write('\tUnique Dams:\t%s\n' % self.num_unique_dams)
        aout.write('\tUnique Founders:\t%s\n' % self.num_unique_founders)
        aout.write('\tUnique Gens:\t%s\n' % self.num_unique_gens)
        aout.write('\tUnique Years:\t%s\n' % self.num_unique_years)
        aout.write('\tUnique Herds:\t%s\n' % self.num_unique_herds)
        aout.write('%s\n' % line)
        aout.write('\tUnique Sire List:\t%s\n' % self.unique_sire_list)
        aout.write('\tUnique Dam List:\t%s\n' % self.unique_dam_list)
        aout.write('\tUnique Founder List:\t%s\n' % self.unique_founder_list)
        aout.write('\tUnique Gen List:\t%s\n' % self.unique_gen_list)
        aout.write('\tUnique Year List:\t%s\n' % self.unique_year_list)
        aout.write('\tUnique Herd List:\t%s\n' % self.unique_herd_list)
        aout.write('%s\n' % line)
        aout.close()

    ##
    # nus() returns the number of unique sires in the pedigree along with a list of the sires
    # @param self Reference to current object
    # @retval The number of unique sires in the pedigree and a list of those sires
    def nus(self):
        """
        Count the number of unique sire IDs in the pedigree.  Returns an integer count
        and a Python list of the unique sire IDs.
        """
        sirelist = set([x.sireID for x in self.myped if x.sireID != self.kw['missing_parent']])
        return len(sirelist), sirelist

    ##
    # nud() returns the number of unique dams in the pedigree along with a list of the dams
    # @param self Reference to current object
    # @retval The number of unique dams in the pedigree and a list of those dams
    def nud(self):
        """
        Count the number of unique dam IDs in the pedigree.  Returns an integer count
        and a Python list of the unique dam IDs.
        """
        damlist = set([x.damID for x in self.myped if x.damID != self.kw['missing_parent']])
        return len(damlist), damlist

    ##
    # nug() returns the number of unique generations in the pedigree along with a list of the generations
    # @param self Reference to current object
    # @retval The number of unique generations in the pedigree and a list of those generations
    def nug(self):
        """
        Count the number of unique generations in the pedigree.  Returns an integer
        count and a Python list of the unique generations.
        """
        if self.kw['animal_type'] == 'light':
            genlist = []
        else:
            genlist = set([x.gen for x in self.myped])
        return len(genlist), genlist

    ##
    # nuy() returns the number of unique birthyears in the pedigree along with a list of the birthyears
    # @param self Reference to current object
    # @retval The number of unique birthyears in the pedigree and a list of those birthyears
    def nuy(self):
        """
        Count the number of unique birth years in the pedigree.  Returns an integer
        count and a Python list of the unique birth years.
        """
        bylist = set([x.by for x in self.myped])
        return len(bylist), bylist

    ##
    # nuf() returns the number of unique founders in the pedigree along with a list of the founders
    # @param self Reference to current object
    # @retval The number of unique founders in the pedigree and a list of those founders
    def nuf(self):
        """
        Count the number of unique founders in the pedigree.
        """
        if self.kw['animal_type'] == 'light':
            # There is no 'founder' flag on LightAnimal records, so we need to
            # check for unknown parents in order to identify founders.
            flist = set([x.animalID for x in self.myped if
                         x.sireID == self.kw['missing_parent'] and x.damID == self.kw['missing_parent']])
        else:
            flist = set([x.animalID for x in self.myped if x.founder == 'y'])
        return len(flist), flist

    ##
    # nuherds() returns the number of unique herds in the pedigree along with a list of the herds.
    # @param self Reference to the current Pedigree() object
    # @retval The number of unique herds in the pedigree and a list of those herds
    def nuherds(self):
        """
        Count the number of unique herds in the pedigree.
        """
        if self.kw['animal_type'] == 'light':
            herdlist = []
        else:
            herdlist = set([x.originalHerd for x in self.myped])
        return len(herdlist), herdlist


##
# NewAMatrix provides an instance of a numerator relationship matrix as a Numarray array of
# floats with some convenience methods.  The idea here is to provide a wrapper around a NRM
# so that it is easier to work with.  For large pedigrees it can take a long time to compute
# the elements of A, so there is real value in providing an easy way to save and retrieve a
# NRM once it has been formed.
class NewAMatrix:
    ##
    # __init__() initializes a NewAMatrix object.
    # @param self Reference to current object.
    # @param kw A dictionary of options.
    # @retval An instance of a NewAMatrix() object
    def __init__(self, kw):
        """
        Initialize a new numerator relationship matrix.
        """
        if 'messages' not in kw:
            kw['messages'] = 'verbose'
        if 'nrm_method' not in kw:
            kw['nrm_method'] = 'nrm'
        # nrm_format can take the values 'text' or 'binary'.
        if 'nrm_format' not in kw:
            kw['nrm_format'] = 'text'
        self.kw = kw
        self.nrm = False

    ##
    # form_a_matrix() calls pyp_nrm/fast_a_matrix() or pyp_nrm/fast_a_matrix_r()
    # to form a NRM from a pedigree.
    # @param self Reference to current object.
    # @param pedigree The pedigree used to form the NRM.
    # @retval A NRM on success, 0 on failure.
    def form_a_matrix(self, pedigree):
        """
        form_a_matrix() calls pyp_nrm/fast_a_matrix() or pyp_nrm/fast_a_matrix_r()
        to form a NRM from a pedigree.
        """
        if self.kw['nrm_method'] not in ['nrm', 'frm']:
            self.kw['nrm_method'] = 'nrm'
        if self.kw['messages'] == 'verbose':
            print('[INFO]: Forming A-matrix from pedigree at %s.' % (pyp_utils.pyp_nice_time()))
        logging.info('Forming A-matrix from pedigree')
        # Try and form the NRM where COI are not adjusted for the inbreeding
        # of parents.
        if self.kw['nrm_method'] == 'nrm':
            try:
                self.nrm = pyp_nrm.fast_a_matrix(pedigree, self.kw)
                if self.kw['messages'] == 'verbose':
                    print('[INFO]: Formed A-matrix from pedigree using pyp_nrm.fast_a_matrix() at %s.' % (
                        pyp_utils.pyp_nice_time()))
                logging.info('Formed A-matrix from pedigree using pyp_nrm.fast_a_matrix()')
            except:
                if self.kw['messages'] == 'verbose':
                    print('[ERROR]: Unable to form A-matrix from pedigree using pyp_nrm.fast_a_matrix() at %s.' % (
                        pyp_utils.pyp_nice_time()))
                logging.error('Unable to form A-matrix from pedigree using pyp_nrm.fast_a_matrix()')
                return 0
        # Otherwise try and form the NRM where COI are adjusted for the inbreeding
        # of parents.
        else:
            try:
                self.nrm = pyp_nrm.fast_a_matrix_r(pedigree, self.kw)
                if self.kw['messages'] == 'verbose':
                    print('[INFO]: Formed A-matrix from pedigree using pyp_nrm.fast_a_matrix_r() at %s.' % (
                        pyp_utils.pyp_nice_time()))
                logging.info('Formed A-matrix from pedigree using pyp_nrm.fast_a_matrix_r()')
            except:
                if self.kw['messages'] == 'verbose':
                    print('[ERROR]: Unable to form A-matrix from pedigree using pyp_nrm.fast_a_matrix_r() at %s.' % (
                        pyp_utils.pyp_nice_time()))
                logging.error('Unable to form A-matrix from pedigree using pyp_nrm.fast_a_matrix_r()')
                return 0

    ##
    # load() uses the Numarray Array Function "fromfile()" to load an array from a
    # binary file.  If the load is successful, self.nrm contains the matrix.
    # @param self Reference to current object.
    # @param nrm_filename The file from which the matrix should be read.
    # @retval A load status indicator (0: failed, 1: success).
    def load(self, nrm_filename):
        """
        load() uses the Numarray Array Function "fromfile()" to load an array from a
        binary file.  If the load is successful, self.nrm contains the matrix.
        """
        import math
        if self.kw['messages'] == 'verbose':
            print('[INFO]: Loading A-matrix from file %s at %s.' % (nrm_filename, pyp_utils.pyp_nice_time()))
        logging.info('Loading A-matrix from file %s', nrm_filename)
        try:
            self.nrm = numpy.fromfile(nrm_filename, dtype='Float64', sep=self.kw['sepchar'])
            self.nrm = numpy.reshape(self.nrm, (int(math.sqrt(self.nrm.shape[0])), int(math.sqrt(self.nrm.shape[0]))))
            if self.kw['messages'] == 'verbose':
                print('[INFO]: A-matrix successfully loaded from file %s at %s.' % (
                    nrm_filename, pyp_utils.pyp_nice_time()))
            logging.info('A-matrix successfully loaded from file %s', nrm_filename)
            return 1
        except:
            if self.kw['messages'] == 'verbose':
                print('[ERROR]: Unable to load A-matrix from file %s at %s.' % (nrm_filename,
                                                                                pyp_utils.pyp_nice_time()))
            logging.error('Unable to load A-matrix from file %s', nrm_filename)
            return 0

    ##
    # save() uses the Numarray method "tofile()" to save an array to a binary file.
    # @param self Reference to current object.
    # @param nrm_filename The file to which the matrix should be written.
    # @param nrm_format String indicating the format to use when writing the NRM to a file (binary|string).
    # @retval A save status indicator (0: failed, 1: success).
    def save(self, nrm_filename, nrm_format=''):
        """
        save() uses the NumPy method "tofile()" to save an array to a binary file.
        """
        if self.kw['messages'] == 'verbose':
            print('[INFO]: Saving A-matrix to file %s at %s.' % (nrm_filename, pyp_utils.pyp_nice_time()))
        logging.info('Saving A-matrix to file %s', nrm_filename)
        try:
            # If the user passes in an nrm_format keyword it overrides the
            # option in the keywords dictionary.
            if nrm_format == '':
                nrm_format = self.kw['nrm_format']
            # If the nrm_format is not binary the matrix is written as a text file.
            if nrm_format == 'binary':
                self.nrm.tofile(nrm_filename)
            else:
                self.nrm.tofile(nrm_filename, sep=self.kw['sepchar'])
            if self.kw['messages'] == 'verbose':
                print('[INFO]: A-matrix successfully saved to file %s at %s.' % (
                    nrm_filename, pyp_utils.pyp_nice_time()))
            logging.info('A-matrix successfully saved to file %s', nrm_filename)
            return 1
        except:
            if self.kw['messages'] == 'verbose':
                print('[ERROR]: Unable to save A-matrix to file %s at %s.' % (nrm_filename, pyp_utils.pyp_nice_time()))
            logging.error('Unable to save A-matrix to file %s', nrm_filename)
            return 0

    ##
    # printme() prints the NRM to the screen.
    # @param self Reference to current object.
    # @retval None
    def printme(self):
        """
        printme() prints the NRM to the screen.
        """
        try:
            print(self.nrm)
        except:
            pass


##
# load_pedigree() wraps pedigree creation and loading into a one-step
# process.  If the user passes both a dictionary and a filename, the
# dictionary will be used instead of the filename unless the dictionary
# is empty.
# @param options Dictionary of pedigree options.
# @param optionsfile File from which pedigree options should be read.
# @param pedsource Source of the pedigree ('file'|'graph'|'graphfile'|'db'|'gedcomfile'|'genesfile'|'textstream').
# @param pedgraph DiGraph from which to load the pedigree.
# @param pedstream String of tuples to unpack into a pedigree.
# @param debug_load When True, print debugging messages while loading (True|False).
# @retval An instance of a NewPedigree object on success, a 0 on failure.
def load_pedigree(options={}, optionsfile='pypedal.ini', pedsource='file', pedgraph=0, pedstream='', debug_load=False):
    """
    load_pedigree() wraps pedigree creation and loading into a one-step
    process.  If the user passes both a dictionary and a filename, the
    dictionary will be used instead of the filename unless the dictionary
    is empty.
    """
    if debug_load:
        print('[DEBUG]: Debugging pyp_newclasses/load_pedigree()...')
        _pedigree = NewPedigree(kw=options, kwfile=optionsfile)
        _pedigree.load(pedsource=pedsource, pedgraph=pedgraph, pedstream=pedstream)
        return _pedigree
    else:
        try:
            _pedigree = NewPedigree(kw=options, kwfile=optionsfile)
            _pedigree.load(pedsource=pedsource, pedgraph=pedgraph, pedstream=pedstream)
            return _pedigree
        except:
            print('[ERROR]: pyp_newclasses.load_pedigree() was unable to instantiate and load the pedigree.')
        return 0


##
# PyPedalError is the base class for exceptions in PyPedal. The exceptions
# are based on the examples from "An Introduction to Python" by Guido van
# Rossum and Fred L. Drake,Jr.
# (http://www.network-theory.co.uk/docs/pytut/tut_64.html).
# @param None
# @retval None
class PyPedalError(Exception):
    """PyPedalError is the base class for exceptions in PyPedal."""
    pass


##
# PyPedalPedigreeInputFileNameError is raised when a simulated pedigree
# is not requested and a pedigree file name is not provided.
# @param None
# @retval None
class PyPedalPedigreeInputFileNameError(PyPedalError):
    """PyPedalPedigreeInputFileNameError is raised when a simulated pedigree
    is not requested and a pedigree file name is not provided.
    """

    ##
    # __init__() returns a new instance of a PyPedalPedigreeInputFileNameError object
    # @param self Reference to current object
    # @retval A new PyPedalPedigreeInputFileNameError object
    def __init__(self):
        self.message = ('You did not request that a pedigree be simulated, and you did not provide the name of a'
                        ' pedigree file to be read.')

    ##
    # __str__() returns an instance of a PyPedalPedigreeInputFileNameError object represented as a string
    # @param self Reference to current object
    # @retval A string representation of a  PyPedalPedigreeInputFileNameError object
    def __str__(self):
        return repr(self.message)
