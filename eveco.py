import sys
import time
import os
import logging
from logging.config import dictConfig
import getopt
from configobj import ConfigObj
from datetime import datetime
from datetime import timedelta

import numpy as np
import pandas as pd
import csv
import unicodedata
import re
import ipaddress

from ftplib import FTP
import codecs
import binascii
import gzip
import multiprocessing
import threading
import queue

import requests
import json

import pymongo
import boto3
import geoip2.database

###############################################################################
# pip install --upgrade pip
# pip install --upgrade pandas
# pip install --upgrade xlrd
# pip install --upgrade requests
# pip install --upgrade configobj
###############################################################################

###############################################################################
# Globals
###############################################################################
thisname='eveco'
company_file_cols = {
    "Nom de l'entreprise": "company_name",
    "Code\nISO\nPays": "company_country_code",
    "Adresse du site internet": "company_website",
    "Numéro BvD": "company_bvd_num",
    "Total des produits d'exploitation (Dernière année)\nkUSD": "company_revenue",
    "Effectifs (dernière valeur)": "company_num_employees",
    "Code d'identifiant": "company_id",
    "Libellé d'identifiant": "company_id_label",
    "Type d'identifiant": "company_id_type",
    "NACE Rev. 2\nCode principal": "company_nace_code",
    "NACE Principal Rev. 2, description textuelle": "company_nace_label",
    "NAICS 2017\nCode principal": "company_naics_code",
    "NAICS, description textuelle": "company_naics_label",
    "US SIC\nCode principal (3 chiffres)": "company_sic_code",
    "US SIC Principal Rev. 2, description textuelle": "company_sic_label",
    "Tête de groupe - Nom": "hq_name",
    "Tête de groupe - Numéro BvD": "hq_bvd_num",
    "Tête de groupe - Type": "hq_type",
    "Tête de groupe - % direct": "hq_direct_own",
    "Tête de groupe - % total": "hq_total_own",
    "Tête de groupe - Total des produits d'exploitation (Chiffre d'affaires)\nmUSD": "hq_revenue",
    "Tête de groupe - Nombre d'employés": "hq_num_employees"
}

###############################################################################
def is_gz_file(filepath):
    with open(filepath, 'rb') as test_f:
        return binascii.hexlify(test_f.read(2)) == b'1f8b'

###############################################################################
def mongo_dbconnect():
    client=pymongo.MongoClient(config['db_connection_string'])

    logger.info('Client = {}'.format(client))
    iporg_db=None

    try:
        client.admin.command('ismaster')
        iporg_db=client.iporg
    except pymongo.errors.ConnectionFailure as errc:
        logger.info('Mongodb Connection Error ({})'.format(errc))
        exit(1)
    
    return(iporg_db)

###############################################################################
def main():
    logger.info('-------------------------------------------------------------------')
    logger.info('Start '+thisname)

    logger.info('Params list=[{}]'.format(params))
    logger.info('Config list=[{}]'.format(config))

    db_mgo=mongo_dbconnect()

    # Parse input Excel
    co_df=pd.read_excel(params['file_name'],
                        sheet_name='Résultats',
                        na_values=['-', 'n.d.'])
    co_df=co_df.rename(index=str,columns=company_file_cols)
    co_df=co_df.drop(co_df.columns[0],axis=1)
    co_df['hq_total_own']=pd.to_numeric(co_df['hq_total_own'], errors='coerce')
    co_df['hq_direct_own']=pd.to_numeric(co_df['hq_direct_own'], errors='coerce')
    logger.info('excel content={}'.format(co_df))

    # Bulk insert keeping NaN
    # co_json=json.dumps(co_df.to_dict('records'))
    # Bulk insert removing NaN
    # co_json=[row.dropna().to_dict() for index,row in co_df.iterrows()]
    # logger.info('json excel content={}'.format(co_json))
    # db_mgo.raw_company_data.insert_many(co_json)

    # Insert by row to prevent duplicate (Delete then insert)
    for r in [row.dropna().to_dict() for index,row in co_df.iterrows()]:
        logger.info('Inserting row = {}'.format(r))
        db_mgo.raw_company_data.delete_many({'company_bvd_num':r['company_bvd_num']})
        db_mgo.raw_company_data.insert_one(r)

    logger.info('Done '+thisname)
    logger.info('-------------------------------------------------------------------')

## -------------------------------------------------------------------
## ---- Tech functions

## -------------------------------------------------------------------
## init_log():
def init_log():
    ## Logging init
    logging_config = { 
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': { 
            'standard': {'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'}
        },
        'handlers': { 
            'ch': {'level': 'INFO','formatter': 'standard','class': 'logging.StreamHandler'},
            'fh': {'level': 'INFO','formatter': 'standard','class': 'logging.handlers.RotatingFileHandler',
                   'filename': thisname+'.log','mode': 'a','encoding': 'utf-8',
                   'maxBytes': 10485760,'backupCount': 5,}
       },
        'loggers': {
            '': {'handlers': ['ch','fh'],'level': 'INFO','propagate': True},
        }
    }
    logging.config.dictConfig(logging_config)
    logging_init=logging.getLogger()
    return(logging_init)

## -------------------------------------------------------------------
## read_cli():
def read_cli():
    help_str=thisname+'.py -f <file_name>'
    params={'file_name':''}
    logger.info('Reading params')
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hf:",["file_name="])
    except getopt.GetoptError as opterr:        
        logger.error(opterr)
        logger.error(help_str)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            logger.error(help_str)
            sys.exit()
        elif opt in ("-f", "--file_name"):
            params['file_name'] = arg
    if(params['file_name']==''):
        logger.error(help_str)
        sys.exit()

    logger.info('In read_cli list=[{}]'.format(params['file_name']))
    return(params)

## -------------------------------------------------------------------
## read_config():
def read_config():
    cwd=os.getcwd()
    return(ConfigObj(cwd+'/python_run_prod.env'))

## -------------------------------------------------------------------
## Main procedure
if __name__ == '__main__':
    logger=init_log()
    config=read_config()
    params=read_cli()

    main()
