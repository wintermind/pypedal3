###############################################################################
# NAME: pyp_db.py
# VERSION: 3.0.0 (3DECEMBER2025)
# AUTHOR: John B. Cole (john.cole@uscdcb.com)
# LICENSE: LGPL
###############################################################################
# FUNCTIONS:
#   connect_to_database()
#   create_pedigree_table()
#   delete_table()
#   populate_pedigree_table()
#   does_table_exist()
#   table_count_rows()
#   table_drop_rows()
###############################################################################

## @package pyp_db
# pyp_db contains a set of procedures used to create, modify, and query pedigrees stored in relational databases.

import logging
import math
import os
import string
import sys
from PyPedal import pyp_io
from PyPedal import pyp_nrm
from PyPedal import pyp_utils
from pydal import DAL, Field


##
# connect_to_database() opens a connection to a user-specified database.
# @param pedobj A PyPedal pedigree object.
# @retval A pyDAL connection on success, None otherwise.
def connect_to_database(pedobj):
    """
    connect_to_database() opens a connection to a user-specified database.
    """
    db = None
    drivers = ['mysql', 'postgres', 'sqlite']
    if pedobj.kw['database_type'] not in drivers:
        print('[ERROR]: The database type %s is not recognized by pyp_db/connect_to_database!' %
              pedobj.kw['database_type'])
        logging.error('The database type %s is not recognized by pyp_db/connect_to_database!',
                      pedobj.kw['database_type'])
        return None

    # Create the connection object.

    # SQLite -- If the named database file doesn't exist, it's created when DAL() is called.
    if pedobj.kw['database_type'] == 'sqlite':
        database_name = 'sqlite://' + pedobj.kw['database_name'] + '.db'
        db = DAL(database_name)

    if not db:
        # If we can't connect to the specified database, try and create the database.
        print(f'[ERROR]: Could not connect to database {database_name} using the database_type '
              f'{pedobj.kw["database_type"]}.')
        logging.error(f'Could not connect to database {database_name} using the database_type '
                      f'{pedobj.kw["database_type"]}.')

    # Return the connection (or False).
    return db


##
# create_pedigree_table() creates a new pedigree table in a database.
# @param pedobj A PyPedal pedigree object.
# @param db An existing ADOdb connection or False to create one
# @param drop Boolean indicating if the data should be dropped from an existing table with the same name
# @retval True on success, False otherwise.
def create_pedigree_table(pedobj, db=False, drop=False):
    """
    create_pedigree_table() creates a new pedigree table in a database. Note that the table has a simple,
    fixed structure that may not include all attributes of a NewAnimal object.

    If the table already exists in the specified database a warning will be issued and the table will
    not be created. If the drop parameter is set to True then an existing table will be dropped and
    a new one created -- this may cause loss of data!
    """
    table_created = False
    # If the user doesn't pass us a conn then try and connect to the database
    if not db:
        db = connect_to_database(pedobj)
    else:
        logging.info('pyp_db/create_pedigree_table() established a connection to the database!')
    # If the user didn't give us a connection and we weren't able to connect to the
    # database ourselves then we have to give up.
    if not db:
        logging.error('The conn passed to pyp_db/create_pedigree_table() did not contain a valid connection and a '
                      'connection to the database could not be established!')
    # If the table already exists we need to warn the user instead of clobbering their data.
    if does_table_exist(pedobj, db=db):
        if pedobj.kw['database_debug']:
            print('[INFO]: The table %s already exists in the database %s in pyp_db/create_pedigree_table().' %
                  (pedobj.kw['database_table'], pedobj.kw['database_name']))
        logging.info('The table %s already exists in the database %s in pyp_db/create_pedigree_table().',
                     pedobj.kw['database_table'], pedobj.kw['database_name'])
        # Only delete data if specifically told to do so.
        if drop:
            table_drop_rows(pedobj, db=db)
            if pedobj.kw['database_debug']:
                print('[WARNING]: Dropping rows from the table %s in the database %s in pyp_db/create_pedigree_table() '
                      'because you told me to.' % (pedobj.kw['database_table'], pedobj.kw['database_name']))
            logging.warning('Dropping rows from the table %s in the database %s in pyp_db/create_pedigree_table() '
                            'because you told me to.', pedobj.kw['database_table'], pedobj.kw['database_name'])
        # Warn that data may be lost so the operation was cancelled.
        else:
            if pedobj.kw['database_debug']:
                print('[INFO]: The table %s in the database %s in pyp_db/create_pedigree_table() already exists and '
                      'contains data that you did not tell me to delete.' % (pedobj.kw['database_table'],
                                                                             pedobj.kw['database_name']))
            logging.info('The table %s in the database %s in pyp_db/create_pedigree_table() already exists and '
                         'contains data that you did not tell me to delete.', pedobj.kw['database_table'],
                         pedobj.kw['database_name'])
            return table_created
    # If you don't like the structure of the pedigree table then this is where you need to make changes. Make sure you
    # carefully check for side effects. For example, if you define a new table structure make sure you fix the loader
    # in pyp_newclasses so that your new attributes also are loaded.
    else:
        try:
            db.define_table(
                pedobj.kw['database_table'],
                Field('animalID', type='integer'),
                Field('animalName', type='string', length=128),
                Field('sireID', type='integer'),
                Field('sireName', type='string', length=128),
                Field('damID', type='integer'),
                Field('damName', type='string', length=128),
                Field('generation', type='double'),
                Field('gencoeff', type='double'),
                Field('infGeneration', type='double'),
                Field('birthdate', type='integer'),
                Field('birthyear', type='integer'),
                Field('sex', type='string', length=1),
                Field('coi', type='double'),
                Field('founder', type='string', length=1),
                Field('ancestor', type='string', length=1),
                Field('originalID', type='string', length=128),
                Field('renumberedID', type='integer'),
                Field('pedigreeComp', type='double'),
                Field('breed', type='string', length=128),
                Field('age', type='double'),
                Field('alive', type='string', length=1),
                Field('num_sons', type='integer'),
                Field('num_daus', type='integer'),
                Field('num_unk', type='integer'),
                Field('herd', type='integer'),
                Field('originalHerd', type='string', length=128),
                Field('alleles', type='string', length=256),
                Field('userField', type='string', length=128),
            )
        # Crumbs...something went horribly wrong here!
        except:
            if pedobj.kw['database_debug']:
                print('[ERROR]: Could not create the table %s in the database %s in pyp_db/connectToDatabase!' %
                      (pedobj.kw['database_table'], pedobj.kw['database_name']))
            logging.error('Could not create the table %s in the database %s in pyp_db/connectToDatabase!',
                          pedobj.kw['database_table'], pedobj.kw['database_name'])
    return table_created


##
# delete_table() drops a table from a database -- this can cause data loss if used carelessly!
# @param pedobj A PyPedal pedigree object.
# @param table_name The name of the table to delete.
# @param db An existing ADOdb connection or False to create one
# @retval True on success, False otherwise.
def delete_table(pedobj, table_name=False, db=False):
    """
    delete_table() drops a table from a database, which can cause data loss if used carelessly!
    """
    # If no table name is specified use the default associated with the pedigree
    if not table_name:
        table_name = pedobj.kw['database_table']
    table_dropped = False
    # If the user doesn't pass us a conn then try and connect to the database
    if not db:
        db = connect_to_database(pedobj)
    else:
        logging.info('pyp_db/delete_table() established a connection to the database!')
    # If the user didn't give us a connection and we weren't able to connect to the
    # database ourselves then we have to give up.
    if not db:
        logging.error('The db passed to pyp_db/delete_table() did not contain a valid connection and a connection '
                      'to the database could not be established!')
    # If we did get a good connection then let the massacre begin! Won't someone please think of the poor data?
    else:
        # Did it work? Yes!
        try:
            db['table_name'].drop()
            if pedobj.kw['database_debug']:
                print('[ERROR]: Deleted the table %s from the database %s in pyp_db/delete_table()!' %
                      (table_name, pedobj.kw['database_name']))
            logging.error('Deleted the table %s from the database %s in pyp_db/delete_table()!',
                          table_name, pedobj.kw['database_name'])
        # ...or not.
        except:
            if pedobj.kw['database_debug']:
                print('[ERROR]: Could not delete the table %s from the database %s in pyp_db/delete_table()!' %
                      (table_name, pedobj.kw['database_name']))
            logging.error('Could not delete the table %s from the database %s in pyp_db/delete_table()!',
                          table_name, pedobj.kw['database_name'])
    return table_dropped


##
# populate_pedigree_table() takes a PyPedal pedigree object and loads
# the animal records in that pedigree into a database table.
# @param pedobj A PyPedal pedigree object.
# @param db An existing ADOdb connection or False to create one
# @retval True on success, False otherwise.
def populate_pedigree_table(pedobj, db=False):
    """
    populate_pedigree_table() takes a PyPedal pedigree object and loads
    the animal records in that pedigree into a database table.
    """
    table_loaded = False
    # If the user doesn't pass us a conn then try and connect to the database
    if not db:
        db = connect_to_database(pedobj)
    else:
        logging.info('pyp_db/populate_pedigree_table() established a connection to the database!')
    # If the user didn't give us a connection and we weren't able to connect to the
    # database ourselves then we have to give up.
    if not db:
        logging.error('The db passed to pyp_db/populate_pedigree_table() did not contain a valid connection and a '
                      'connection to the database could not be established!')
    else:
        # If the pedigree table doesn't exist try and create it.
        if not does_table_exist(pedobj, db=db):
            created_table = create_pedigree_table(pedobj, db)
            # If we can't create the table then we have to bail out.
            if not created_table:
                logging.error('Unable to create pedigree table in pyp_db/populate_pedigree_table()!')
            # Woohoo! We created the table!
            else:
                logging.info('Created pedigree table in pyp_db/populate_pedigree_table()!')
        # Okay, the pedigree table should now exist.
        if does_table_exist(pedobj, db=db):
            # print 'Pedigree table does exist!'
            try:
                for _p in pedobj.pedigree:
                    alleles = '__'.join(_p.alleles)
                    db[pedobj.kw['database_table']].insert(animalID=_p.animalID,
                                                           animalName=_p.animalName,
                                                           sireID=_p.sireID,
                                                           sireName=_p.sireName,
                                                           damID=_p.damID,
                                                           damName=_p.damName,
                                                           generation=float(_p.gen),
                                                           infGeneration=float(_p.igen),
                                                           birthdate=int(_p.bd),
                                                           birthyear=int(_p.by),
                                                           sex=_p.sex,
                                                           coi=_p.fa,
                                                           founder=_p.founder,
                                                           ancestor=_p.ancestor,
                                                           originalID=_p.originalID,
                                                           renumberedID=_p.renumberedID,
                                                           pedigreeComp=float(_p.pedcomp),
                                                           breed=_p.breed,
                                                           age=int(_p.age),
                                                           alive=_p.alive,
                                                           num_sons=len(_p.sons),
                                                           num_daus=len(_p.daus),
                                                           num_unk=len(_p.unks),
                                                           herd=_p.originalHerd,
                                                           gencoeff=float(_p.gencoeff),
                                                           alleles=alleles,
                                                           userField=str(_p.userField)
                                                           )
            except:
                if pedobj.kw['database_debug']:
                    print('[ERROR]: Unable to write records to table %s in the database %s!' %
                          (pedobj.kw['database_table'], pedobj.kw['database_name']))
                logging.error('Unable to write records to table %s in the database %s!',
                              pedobj.kw['database_table'], pedobj.kw['database_name'])
        # Try and create the table
        else:
            if pedobj.kw['database_debug']:
                print('[ERROR]: The pedigree table %s does not exist in the database %s in '
                      'pyp_db/populate_pedigree_table()!' % (pedobj.kw['database_table'], pedobj.kw['database_name']))
            logging.error('The pedigree table %s does not exist in the database %s in '
                          'pyp_db/populate_pedigree_table()!', pedobj.kw['database_table'],
                          pedobj.kw['database_name'])
    return table_loaded


##
# does_table_exist() queries the database to determine whether or not a table exists.
# @param pedobj A PyPedal pedigree object.
# @param tablename The name of the table to delete.
# @param db An existing pyDAL connection or False to create one
# @retval True on success, False otherwise.
def does_table_exist(pedobj, table_name=None, db=None):
    """
    does_table_exist() queries the database to determine whether or not a table exists.
    """
    if not table_name:
        table_name = pedobj.kw['database_table']
    table_exists = False
    # If the user doesn't pass us a conn then try and connect to the database
    if not db:
        db = connect_to_database(pedobj)
    else:
        logging.info('pyp_db/does_table_exist() established a connection to the database!')
    # If the user didn't give us a connection and we weren't able to connect to the
    # database ourselves then we have to give up.
    if not db:
        logging.error('The conn passed to pyp_db/does_table_exist() did not contain a valid connection and a '
                      'connection to the database could not be established!')
        return False
    else:
        try:
            db(db.table_name).select()
            table_exists = True
        except AttributeError:
            if pedobj.kw['database_debug']:
                print('[ERROR]: The table %s does not exist in the database %s!' %
                      (table_name, pedobj.kw['database_name']))
            logging.error('The table %s does not exist in the database %s!',
                          table_name, pedobj.kw['database_name'])
            table_exists = False
    return table_exists


##
# table_count_rows() returns the number of rows in a table.
# @param pedobj A PyPedal pedigree object.
# @param db An existing pyDAL connection or None to create one
# @retval An integer on success, 0 otherwise
def table_count_rows(pedobj, db=None):
    """
    table_count_rows() returns the number of rows in a table.
    """
    table_rows = 0
    # If the user doesn't pass us a conn then try and connect to the database
    if not db:
        db = connect_to_database(pedobj)
    else:
        logging.info('pyp_db/table_count_rows() established a connection to the database!')
    # If the user didn't give us a connection and we weren't able to connect to the
    # database ourselves then we have to give up.
    if not db:
        logging.error('The conn passed to pyp_db/table_count_rows() did not contain a valid connection and a '
                      'connection to the database could not be established!')
    else:
        if does_table_exist(pedobj, db=db):
            try:
                table_rows = int(db(db['pedigree']).count())
            except:
                table_rows = 0
        # does_table_exist() should have logged the table's non-existance for us, so we
        # can simply carry on.
        else:
            pass
    return table_rows


##
# table_drop_rows() deletes the rows from an existing table
# @param pedobj A PyPedal pedigree object.
# @param table_name The name of the table to delete.
# @param db An existing ADOdb connection or False to create one
# @retval The number of rows dropped from the database.
def table_drop_rows(pedobj, table_name=False, db=False):
    """
    table_drop_rows() deletes the rows from an existing table
    """
    if not table_name:
        table_name = pedobj.kw['database_table']
    rows_dropped = 0
    # If the user doesn't pass us a conn then try and connect to the database
    if not db:
        db = connect_to_database(pedobj)
    else:
        logging.info('pyp_db/table_drop_rows() established a connection to the database!')
    # If the user didn't give us a connection and we weren't able to connect to the
    # database ourselves then we have to give up.
    if not db:
        logging.error('The conn passed to pyp_db/table_drop_rows() did not contain a valid connection and a '
                      'connection to the database could not be established!')
    else:
        if does_table_exist(pedobj, table_name, db):
            try:
                myquery = (db[table_name].animalID != None)
                myset = db(myquery)
                rows = myset.select()
                rows_dropped = len(rows)
                myset.delete()
                if pedobj.kw['messages'] != 'quiet':
                    print('[ERROR]: pyp_db/table_drop_rows() deleted %s rows from the table %s in the database '
                          '%s!' % (rows_dropped, pedobj.kw['database_table'], pedobj.kw['database_name']))
                logging.error('pyp_db/table_drop_rows() deleted %s rows from the table %s in the database '
                              '%s!', rows_dropped, pedobj.kw['database_table'], pedobj.kw['database_name'])
            except:
                if pedobj.kw['messages'] != 'quiet':
                    print('[ERROR]: pyp_db/table_drop_rows() could not delete rows from the table %s in the database '
                          '%s!' % (pedobj.kw['database_table'], pedobj.kw['database_name']))
                logging.error('pyp_db/table_drop_rows() could not delete rows from the table %s in the database '
                              '%s!', pedobj.kw['database_table'], pedobj.kw['database_name'])
        # does_table_exist() should have logged the table's non-existance for us, so we can simply carry on.
        else:
            pass
    return rows_dropped
