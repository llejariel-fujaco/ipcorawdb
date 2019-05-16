import sys
import time
import os
import logging
from logging.config import dictConfig
import getopt
from configobj import ConfigObj
from datetime import datetime
from datetime import timedelta

import ipwhois
import ipaddress

import numpy as np
import pandas as pd
import csv
import unicodedata
import re

from ftplib import FTP
import codecs
import binascii
import gzip
import shutil
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
# pip install --upgrade requests
# pip install --upgrade configobj
# pip install --upgrade ipwhois
# pip install --upgrade boto3
# pip install --upgrade geoip2
###############################################################################

###############################################################################
# Globals
###############################################################################
thisname='eveip'
ip_address_status=['TO_PROCESS','']

CIDRS_RESERVED = {
    'software': ['0.0.0.0/8',],
    'private': ['10.0.0.0/8','100.64.0.0/10','172.16.0.0/12',
                '192.0.0.0/24','192.168.0.0/16','198.18.0.0/15',],
    'host': ['127.0.0.0/8',],
    'subnet': ['169.254.0.0/16','255.255.255.255/32'],
    'documentation': ['192.0.2.0/24','198.51.100.0/24','203.0.113.0/24',],
    'internet': ['192.88.99.0/24','224.0.0.0/4','240.0.0.0/4',],
    
}

CIDRS_ACLASS = {
    'Level 3 Communications': ['4.0.0.0/8',],
    'AT&T Services': ['12.0.0.0/8',],
    'Apple Inc': ['17.0.0.0/8',],
    'Ford Motor Company': ['19.0.0.0/8',],
    'PSINet': ['38.0.0.0/8',],
    'Amateur Radio Digital Communications': ['44.0.0.0/8',],
    'Prudential Securities': ['48.0.0.0/8',],
    'US Postal Service': ['56.0.0.0/8',],
    'Comcast Corporation': ['73.0.0.0/8',],
    'DoD': ['6.0.0.0/8','7.0.0.0/8','11.0.0.0/8',
		    '21.0.0.0/8','22.0.0.0/8','26.0.0.0/8',
		    '28.0.0.0/8','29.0.0.0/8','30.0.0.0/8',
		    '33.0.0.0/8','55.0.0.0/8','214.0.0.0/8',
		    '215.0.0.0/8',],
    'AFRINIC': ['41.0.0.0/8','102.0.0.0/8','105.0.0.0/8',
                '154.0.0.0/8','196.0.0.0/8','197.0.0.0/8',],
    'APNIC': [  '1.0.0.0/8','14.0.0.0/8','27.0.0.0/8',
                '36.0.0.0/8','39.0.0.0/8','42.0.0.0/8',
                '43.0.0.0/8','49.0.0.0/8','58.0.0.0/8',
                '59.0.0.0/8','60.0.0.0/8','61.0.0.0/8',
                '101.0.0.0/8','103.0.0.0/8','106.0.0.0/8',
                '110.0.0.0/8','111.0.0.0/8','112.0.0.0/8',
                '113.0.0.0/8','114.0.0.0/8','115.0.0.0/8',
                '116.0.0.0/8','117.0.0.0/8','118.0.0.0/8',
                '119.0.0.0/8','120.0.0.0/8','121.0.0.0/8',
                '122.0.0.0/8','123.0.0.0/8','124.0.0.0/8',
                '125.0.0.0/8','126.0.0.0/8','133.0.0.0/8',
                '150.0.0.0/8','153.0.0.0/8','163.0.0.0/8',
                '171.0.0.0/8','175.0.0.0/8','180.0.0.0/8',
                '182.0.0.0/8','183.0.0.0/8','202.0.0.0/8',
                '203.0.0.0/8','210.0.0.0/8','211.0.0.0/8',
                '218.0.0.0/8','219.0.0.0/8','220.0.0.0/8',
                '221.0.0.0/8','222.0.0.0/8','223.0.0.0/8',],
    'ARIN': [	'3.0.0.0/8','8.0.0.0/8','9.0.0.0/8',
                '13.0.0.0/8','15.0.0.0/8','16.0.0.0/8',
                '18.0.0.0/8','20.0.0.0/8','23.0.0.0/8',
                '24.0.0.0/8','32.0.0.0/8','34.0.0.0/8',
                '35.0.0.0/8','40.0.0.0/8','45.0.0.0/8',
                '47.0.0.0/8','50.0.0.0/8','52.0.0.0/8',
                '54.0.0.0/8','63.0.0.0/8','64.0.0.0/8',
                '65.0.0.0/8','66.0.0.0/8','67.0.0.0/8',
                '68.0.0.0/8','69.0.0.0/8','70.0.0.0/8',
                '71.0.0.0/8','72.0.0.0/8','73.0.0.0/8',
                '74.0.0.0/8','75.0.0.0/8','76.0.0.0/8',
                '96.0.0.0/8','97.0.0.0/8','98.0.0.0/8',
                '99.0.0.0/8','100.0.0.0/8','104.0.0.0/8',
                '107.0.0.0/8','108.0.0.0/8','128.0.0.0/8',
                '129.0.0.0/8','130.0.0.0/8','131.0.0.0/8',
                '132.0.0.0/8','134.0.0.0/8','135.0.0.0/8',
                '136.0.0.0/8','137.0.0.0/8','138.0.0.0/8',
                '139.0.0.0/8','140.0.0.0/8','142.0.0.0/8',
                '143.0.0.0/8','144.0.0.0/8','146.0.0.0/8',
                '147.0.0.0/8','148.0.0.0/8','149.0.0.0/8',
                '152.0.0.0/8','155.0.0.0/8','156.0.0.0/8',
                '157.0.0.0/8','158.0.0.0/8','159.0.0.0/8',
                '160.0.0.0/8','161.0.0.0/8','162.0.0.0/8',
                '164.0.0.0/8','165.0.0.0/8','166.0.0.0/8',
                '167.0.0.0/8','168.0.0.0/8','169.0.0.0/8',
                '170.0.0.0/8','172.0.0.0/8','173.0.0.0/8',
                '174.0.0.0/8','184.0.0.0/8','192.0.0.0/8',
                '198.0.0.0/8','199.0.0.0/8','204.0.0.0/8',
                '205.0.0.0/8','206.0.0.0/8','207.0.0.0/8',
                '208.0.0.0/8','209.0.0.0/8','216.0.0.0/8',],
    'LACNIC': [	'177.0.0.0/8','179.0.0.0/8','181.0.0.0/8',
                '186.0.0.0/8','187.0.0.0/8','189.0.0.0/8',
                '190.0.0.0/8','191.0.0.0/8','200.0.0.0/8',
                '201.0.0.0/8',],
    'RIPE NCC': [	'2.0.0.0/8','5.0.0.0/8','25.0.0.0/8',
                    '31.0.0.0/8','37.0.0.0/8','46.0.0.0/8',
                    '51.0.0.0/8','53.0.0.0/8','57.0.0.0/8',
                    '62.0.0.0/8','77.0.0.0/8','78.0.0.0/8',
                    '79.0.0.0/8','80.0.0.0/8','81.0.0.0/8',
                    '82.0.0.0/8','83.0.0.0/8','84.0.0.0/8',
                    '85.0.0.0/8','86.0.0.0/8','87.0.0.0/8',
                    '88.0.0.0/8','89.0.0.0/8','90.0.0.0/8',
                    '91.0.0.0/8','92.0.0.0/8','93.0.0.0/8',
                    '94.0.0.0/8','95.0.0.0/8','109.0.0.0/8',
                    '141.0.0.0/8','145.0.0.0/8','151.0.0.0/8',
                    '176.0.0.0/8','178.0.0.0/8','185.0.0.0/8',
                    '188.0.0.0/8','193.0.0.0/8','194.0.0.0/8',
                    '195.0.0.0/8','212.0.0.0/8','213.0.0.0/8',
                    '217.0.0.0/8',],
}

CIDRS_BOT = {
    'Amazon': ['107.20.0.0/14', '122.248.192.0/19', '122.248.224.0/19',
               '172.96.96.0/20', '174.129.0.0/16', '175.41.128.0/19',
               '175.41.160.0/19', '175.41.192.0/19', '175.41.224.0/19',
               '176.32.120.0/22', '176.32.72.0/21', '176.34.0.0/16',
               '176.34.144.0/21', '176.34.224.0/21', '184.169.128.0/17',
               '184.72.0.0/15', '185.48.120.0/26', '207.171.160.0/19',
               '213.71.132.192/28', '216.182.224.0/20', '23.20.0.0/14',
               '46.137.0.0/17', '46.137.128.0/18', '46.51.128.0/18',
               '46.51.192.0/20', '50.112.0.0/16', '50.16.0.0/14', '52.0.0.0/11',
               '52.192.0.0/11', '52.192.0.0/15', '52.196.0.0/14',
               '52.208.0.0/13', '52.220.0.0/15', '52.28.0.0/16', '52.32.0.0/11',
               '52.48.0.0/14', '52.64.0.0/12', '52.67.0.0/16', '52.68.0.0/15',
               '52.79.0.0/16', '52.80.0.0/14', '52.84.0.0/14', '52.88.0.0/13',
               '54.144.0.0/12', '54.160.0.0/12', '54.176.0.0/12',
               '54.184.0.0/14', '54.188.0.0/14', '54.192.0.0/16',
               '54.193.0.0/16', '54.194.0.0/15', '54.196.0.0/15',
               '54.198.0.0/16', '54.199.0.0/16', '54.200.0.0/14',
               '54.204.0.0/15', '54.206.0.0/16', '54.207.0.0/16',
               '54.208.0.0/15', '54.210.0.0/15', '54.212.0.0/15',
               '54.214.0.0/16', '54.215.0.0/16', '54.216.0.0/15',
               '54.218.0.0/16', '54.219.0.0/16', '54.220.0.0/16',
               '54.221.0.0/16', '54.224.0.0/12', '54.228.0.0/15',
               '54.230.0.0/15', '54.232.0.0/16', '54.234.0.0/15',
               '54.236.0.0/15', '54.238.0.0/16', '54.239.0.0/17',
               '54.240.0.0/12', '54.242.0.0/15', '54.244.0.0/16',
               '54.245.0.0/16', '54.247.0.0/16', '54.248.0.0/15',
               '54.250.0.0/16', '54.251.0.0/16', '54.252.0.0/16',
               '54.253.0.0/16', '54.254.0.0/16', '54.255.0.0/16',
               '54.64.0.0/13', '54.72.0.0/13', '54.80.0.0/12', '54.72.0.0/15',
               '54.79.0.0/16', '54.88.0.0/16', '54.93.0.0/16', '54.94.0.0/16',
               '63.173.96.0/24', '72.21.192.0/19', '75.101.128.0/17',
               '79.125.64.0/18', '96.127.0.0/17'],
    'Baidu': ['180.76.0.0/16', '119.63.192.0/21', '106.12.0.0/15',
              '182.61.0.0/16'],
    'DO': ['104.131.0.0/16', '104.236.0.0/16', '107.170.0.0/16',
           '128.199.0.0/16', '138.197.0.0/16', '138.68.0.0/16',
           '139.59.0.0/16', '146.185.128.0/21', '159.203.0.0/16',
           '162.243.0.0/16', '178.62.0.0/17', '178.62.128.0/17',
           '188.166.0.0/16', '188.166.0.0/17', '188.226.128.0/18',
           '188.226.192.0/18', '45.55.0.0/16', '46.101.0.0/17',
           '46.101.128.0/17', '82.196.8.0/21', '95.85.0.0/21', '95.85.32.0/21'],
    'Dream': ['173.236.128.0/17', '205.196.208.0/20', '208.113.128.0/17',
              '208.97.128.0/18', '67.205.0.0/18'],
    'Google': ['104.154.0.0/15', '104.196.0.0/14', '107.167.160.0/19',
               '107.178.192.0/18', '108.170.192.0/20', '108.170.208.0/21',
               '108.170.216.0/22', '108.170.220.0/23', '108.170.222.0/24',
               '108.59.80.0/20', '130.211.128.0/17', '130.211.16.0/20',
               '130.211.32.0/19', '130.211.4.0/22', '130.211.64.0/18',
               '130.211.8.0/21', '146.148.16.0/20', '146.148.2.0/23',
               '146.148.32.0/19', '146.148.4.0/22', '146.148.64.0/18',
               '146.148.8.0/21', '162.216.148.0/22', '162.222.176.0/21',
               '173.255.112.0/20', '192.158.28.0/22', '199.192.112.0/22',
               '199.223.232.0/22', '199.223.236.0/23', '208.68.108.0/23',
               '23.236.48.0/20', '23.251.128.0/19', '35.184.0.0/14',
               '35.188.0.0/15', '35.190.0.0/17', '35.190.128.0/18',
               '35.190.192.0/19', '35.190.224.0/20', '8.34.208.0/20',
               '8.35.192.0/21', '8.35.200.0/23',],
    'Hetzner': ['129.232.128.0/17', '129.232.156.128/28', '136.243.0.0/16',
                '138.201.0.0/16', '144.76.0.0/16', '148.251.0.0/16',
                '176.9.12.192/28', '176.9.168.0/29', '176.9.24.0/27',
                '176.9.72.128/27', '178.63.0.0/16', '178.63.120.64/27',
                '178.63.156.0/28', '178.63.216.0/29', '178.63.216.128/29',
                '178.63.48.0/26', '188.40.0.0/16', '188.40.108.64/26',
                '188.40.132.128/26', '188.40.144.0/24', '188.40.48.0/26',
                '188.40.48.128/26', '188.40.72.0/26', '196.40.108.64/29',
                '213.133.96.0/20', '213.239.192.0/18', '41.203.0.128/27',
                '41.72.144.192/29', '46.4.0.128/28', '46.4.192.192/29',
                '46.4.84.128/27', '46.4.84.64/27', '5.9.144.0/27',
                '5.9.192.128/27', '5.9.240.192/27', '5.9.252.64/28',
                '78.46.0.0/15', '78.46.24.192/29', '78.46.64.0/19',
                '85.10.192.0/20', '85.10.228.128/29', '88.198.0.0/16',
                '88.198.0.0/20'],
    'Linode': ['104.200.16.0/20', '109.237.24.0/22', '139.162.0.0/16',
               '172.104.0.0/15', '173.255.192.0/18', '178.79.128.0/21',
               '198.58.96.0/19', '23.92.16.0/20', '45.33.0.0/17',
               '45.56.64.0/18', '45.79.0.0/16', '50.116.0.0/18',
               '80.85.84.0/23', '96.126.96.0/19'],
}

###############################################################################
def get_mmdb():
    mmdb_file=config['mmdb_filename']
    mmdb_gzfile=config['mmdb_filename']+'.gz'

    r = requests.get(config['mmdb_url'], stream=True)  
    with open(mmdb_gzfile, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()

    with gzip.open(mmdb_gzfile, 'rb') as f_in:
        with open(mmdb_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    os.remove(mmdb_gzfile)

###############################################################################
def get_mmdbreader():
    mmdb_file=config['mmdb_filename']

    if(os.path.isfile(mmdb_file)):
        mmdb_mdate=datetime.fromtimestamp(os.path.getmtime(mmdb_file))
        if(mmdb_mdate < (datetime.now() - timedelta(days=30))):
            get_mmdb()
    else:
        get_mmdb()
    return(geoip2.database.Reader(mmdb_file))

###############################################################################
def is_gz_file(filepath):
    with open(filepath, 'rb') as test_f:
        return binascii.hexlify(test_f.read(2)) == b'1f8b'

###############################################################################
def in_cidr(ip, cidr):
        if ipaddress.ip_address(ip) in ipaddress.ip_network(cidr):
            return(True)
        return(False)

###############################################################################
def get_aclass(ip):
        for block_name,block in CIDRS_ACLASS.items():
            for cidr in block:
                if ipaddress.ip_address(ip) in ipaddress.ip_network(cidr):
                    return(block_name)

###############################################################################
def is_bot(ip):
    return(
            any(
                [
                True
                for cidr in [cidr for block in CIDRS_BOT.values() for cidr in block]
                if in_cidr(ipaddress.ip_address(ip),cidr)
                ]
            )
    )

###############################################################################
def is_reserved(ip):
    return(
            any(
                [
                True
                for cidr in [cidr for block in CIDRS_RESERVED.values() for cidr in block]
                if in_cidr(ipaddress.ip_address(ip),cidr)
                ]
            )
    )

###############################################################################
def getgeoip_dict(ip_addr,status):

    url=config['ipstack_url']+'/'+ip_addr
    payload={
        'access_key':config['ipstack_key'],
        'hostname':1,
        'output':'json'
    }
    ip_addr_data=None
    status['geo']='DONE'
    try:
        response=requests.get(url,params=payload,timeout=5)
        response.raise_for_status()
        resp_val=response.json()
        if('success' in resp_val):
            logger.info('Error response.json()={}'.format(response.json()))
            status['geo']='ERR'
        else:
            ip_addr_data=response.json()
    except requests.exceptions.HTTPError as errh:
        logger.info('Ipstack error {}'.format(response.json()))
        logger.info('HTTPError {}'.format(errh))
        status['geo']='ERR'
    except requests.exceptions.ConnectionError as errc:
        logger.info('ConnectionError {}'.format(errc))
        status['geo']='ERR'
    except requests.exceptions.Timeout as errt:
        logger.info('Timeout {}'.format(errt))
        status['geo']='ERR'
    except requests.exceptions.RequestException as err:
        logger.info('RequestException {}'.format(err))
        status['geo']='ERR'

    return(ip_addr_data)

###############################################################################
def getrdapip_dict(ip_addr,status):
    dict_rdap=None
    status['rdap']='DONE'
    try:
        ip_whois = ipwhois.IPWhois(ip_addr)
        dict_rdap = ip_whois.lookup_rdap(depth=0,inc_raw=False, asn_methods=['dns', 'whois', 'http'])
    except ipwhois.exceptions.HTTPLookupError as errh:
        logger.info('HTTPLookupError {}'.format(errh))
        status['rdap']='ERR'
    except ipwhois.exceptions.HTTPRateLimitError as errl:
        logger.info('HTTPRateLimitError {}'.format(errl))
        status['rdap']='ERR'
    except ipwhois.exceptions.IPDefinedError as erri:
        logger.info('IPDefinedError {}'.format(erri))
        status['rdap']='ERR'
    except ipwhois.exceptions.BaseIpwhoisException as errb:
        logger.info('BaseIpwhoisException {}'.format(errb))
        status['rdap']='ERR'

    return(dict_rdap)

###############################################################################
def getgeo2_dict(ip_addr,mmdb_reader,status):
    raw_geo2_data=None
    status['geo2']='DONE'

    try:
        resp= mmdb_reader.city(ip_addr)
        raw_geo2_data={ 'country_iso': resp.country.iso_code,
                        'country': resp.country.name,
                        'state_iso': resp.subdivisions.most_specific.iso_code,
                        'state': resp.subdivisions.most_specific.name,
                        'city': resp.city.name,
                        'postal_code': resp.postal.code,
                        'lng': resp.location.longitude,
                        'lat': resp.location.latitude,
                        'accuracy_radius':resp.location.accuracy_radius,
                        # 'sub2_iso': resp.subdivisions[-1].iso_code if len(resp.subdivisions)>0 else None,
                        # 'sub2': resp.subdivisions[-1].name if len(resp.subdivisions)>0 else None,
                        # 'sub1_iso': resp.subdivisions[-2].iso_code if len(resp.subdivisions)>1 else None,
                        # 'sub1': resp.subdivisions[-2].name if len(resp.subdivisions)>1 else None,
                        # 'traits':resp.traits,
        }        
    except geoip2.errors.AddressNotFoundError as erra:
        logger.info('AddressNotFoundError {}'.format(erra))
        status['geo2']='ERR'
    except geoip2.errors.GeoIP2Error as errg:
        logger.info('GeoIP2Error {}'.format(errg))
        status['geo2']='ERR'

    return(raw_geo2_data)

###############################################################################
def get_raw_ip_data(ip_addr,mmdb_reader):
    raw_ip_data={
            'ip_addr':ip_addr,
            'ip_addr_num':int(ipaddress.ip_address(ip_addr)),
            'aclass': None,
            'acq_dt': datetime.utcnow(),
            'source': config['prg_name'],
            'status': {'status':'TO_PROCESS','rdap':'TO_PROCESS','geo':'TO_PROCESS','geo2':'TO_PROCESS'},
            'geo_data': None,
            'rdap_data': None,
            'geo2_data':None
            }

    if(is_bot(ip_addr)):
        raw_ip_data['status']={'status':'IS_BOT','rdap':'NONE','geo':'NONE','geo2':'NONE'}
    elif(is_reserved(ip_addr)):
        raw_ip_data['status']={'status':'IS_RESERVED','rdap':'NONE','geo':'NONE','geo2':'NONE'}
    else:
        ip_address_status=raw_ip_data['status']
        raw_ip_data['aclass']=get_aclass(ip_addr)
        raw_geoip_data = getgeoip_dict(ip_addr, ip_address_status)
        raw_rdap_data = getrdapip_dict(ip_addr, ip_address_status)
        raw_geo2_data = getgeo2_dict(ip_addr, mmdb_reader, ip_address_status)
        if(ip_address_status['rdap']=='DONE' and ip_address_status['geo']=='DONE' and ip_address_status['geo2']=='DONE'):
            ip_address_status['status']='DONE'

        raw_ip_data['geo_data']=raw_geoip_data
        raw_ip_data['rdap_data']=raw_rdap_data
        raw_ip_data['geo2_data']=raw_geo2_data
        raw_ip_data['status']=ip_address_status

    return(raw_ip_data)

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
    logger.info('Start '+config['prg_name'])

    logger.info('Params list=[{}]'.format(params))
    logger.info('Config list=[{}]'.format(config))

    db_mgo=mongo_dbconnect()
    mmdb_reader=get_mmdbreader()

    # IP List to process (From input file or comma separated list or both)
    eveip_df=pd.DataFrame()
    if(params['ip_list']):
        eveip_df=pd.concat([eveip_df,pd.DataFrame(params['ip_list'],columns=['ip_address'])],ignore_index=True)
    if(params['file_name']):
        eveip_df=pd.concat([eveip_df,pd.read_csv(params['file_name'])],ignore_index=True)
    logger.info('IP list=[{}]'.format(eveip_df))

    # Loop over ip_addresses
    for index,row in eveip_df.iterrows():
        cur_ip_addr_data=get_raw_ip_data(row['ip_address'],mmdb_reader)
        logger.info('cur_ip_addr_data ip=[{}]'.format(cur_ip_addr_data))
    
        # Mongo insert
        # By default replace existing ip
        db_mgo.raw_ip_data.delete_many({'ip_addr':row['ip_address']})
        cur_ip_addr_mgo_id=db_mgo.raw_ip_data.insert_one(cur_ip_addr_data).inserted_id
        logger.info('Mongo inserted_id={}'.format(cur_ip_addr_mgo_id))

    logger.info('Done '+config['prg_name'])
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
                   'filename': config['prg_name']+'.log','mode': 'a','encoding': 'utf-8',
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
    help_str=config['prg_name']+'.py -f <file_name> -i <ip_address list>'
    params={'file_name':'','ip_list':[]}
    logger.info('Reading params')
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hf:i:",["file_name=","ip_list"])
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
        elif opt in ("-i", "--ip_list"):
            params['ip_list'] = arg.split(",")
            
    logger.info('In read_cli file_name=[{}], ip_list=[{}]'.format(params['file_name'],params['ip_list']))
    return(params)

## -------------------------------------------------------------------
## read_config():
def read_config():
    cwd=os.getcwd()
    return(ConfigObj(cwd+'/python_run_prod.env'))

## -------------------------------------------------------------------
## Main procedure
if __name__ == '__main__':
    config=read_config()
    logger=init_log()
    params=read_cli()

    main()
