#!/usr/bin/env python3

import hashlib
import binascii
import os
import sys
from functools import partial
import requests
from time import sleep

providers = {
    'certum': 'http://time.certum.pl/',
    'comodo': 'http://timestamp.comodoca.com/',
    'symantec': 'http://sha256timestamp.ws.symantec.com/sha256/timestamp',
    'geotrust': 'https://timestamp.geotrust.com/tsa',
    'globalsign': 'http://timestamp.globalsign.com/scripts/timstamp.dll',
    'globaltrust': 'http://services.globaltrustfinder.com/adss/tsa',
    }
    

def hash_file(filename, hashtype, chunksize=2**15, bufsize=-1):
    h = hashtype()
    with open(filename, 'rb', bufsize) as readfile:
        for chunk in iter(partial(readfile.read, chunksize), b''):
            h.update(chunk)
    return h

def generate_ts_query(filename):
    sha512 = hash_file(filename, hashlib.sha512)
    query = b''.join([b'\x30\x59\x02\x01\x01\x30\x51\x30\x0D\x06\x09\x60\x86\x48\x01\x65\x03\x04\x02\x03\x05\x00\x04\x40',
                   sha512.digest(), b'\x01\x01\xff'])
    return query

def get_timestamps(filename, query, logger):
    headers = { 'Content-Type': 'application/timestamp-query' }
    timestamps = []
    for provider, url in providers.items():
        full_filename = filename+"_"+provider+".tsr"
        with open(full_filename, 'wb') as tsr:
            logger.debug("Requesting timestamp from {}".format(provider))
            try:
                reply = requests.post(url, data=query, headers=headers)
            except:
                logger.warning("Something has gone wrong with {} provider!".format(provider))
            logger.debug("Got reply from {}".format(provider))
            tsr.write(reply.content)
            timestamps.append(os.path.basename(full_filename))
    if len(timestamps) != 0:
        logger.info("Successfully created the following timestamp files: {}.".format(",".join(timestamps)))


def main(filename):
    query = generate_ts_query(filename)
    get_timestamps(filename, query)
    
if __name__ == '__main__':
    main(sys.argv[1])
