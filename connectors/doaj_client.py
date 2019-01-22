'''
Client for DOAJ API
'''

import requests
import logging

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
# logger.addHandler(ch)


DOAJ_URL = 'https://doaj.org/api/v1/search/journals/'

def issn_search(issn):
    '''
    :param issn: Journal's ISSN
    :return: DOAJ response
    '''
    url = DOAJ_URL + 'issn:' + issn
    print(url)
    try:
        return (requests.get(url).json()['results'][0])
    except IndexError:
        return (None)