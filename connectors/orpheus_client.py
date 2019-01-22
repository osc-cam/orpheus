'''
Orpheus client is a python wrapper for the Orpheus Restful API
'''

import json
import logging
import re
import requests
import sys
import time
import urllib.parse

try:
    from keys_local import ORPHEUS_URL, CLIENT_USERNAME, CLIENT_PASSWORD
except ImportError:
    sys.exit('keys_local.py file could not be found')

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

if ORPHEUS_URL == 'https://orpheus-prod.lib.cam.ac.uk/':
    if input('Orpheus_client set to work on production instance at https://orpheus-prod.lib.cam.ac.uk. '
              'Are you sure you wish to continue? [y/N]') not in ['y', 'Y', 'yes']:
        sys.exit('Aborted!')

TIMEOUT = 10
RETRY = 10

# let's use urllib.parse.quote for all of these, except İ
html_url_encoding_dict = { # see for a comprehensive list: https://www.w3schools.com/tags/ref_urlencode.asp
    # ';' : '%3B',
    # '&' : '%26',
    # '+' : '%2B',
    'İ' : 'I',
}

def escape_invalid_url(str):
    for k, v in html_url_encoding_dict.items():  # escape illegal characters
        str = str.replace(k, v)
    str = urllib.parse.quote(str)
    return str

# region methods
def orpheus_get(get_url):
    try:
        response = requests.get(get_url, timeout=TIMEOUT)
    except:
        logger.exception('An error occurred; retrying in {} seconds'.format(RETRY))
        time.sleep(RETRY)
        response = orpheus_get(get_url)
    return(response)

def orpheus_post(post_url, data, **kwargs):
    kwargs.update(data)
    logger.debug(kwargs)
    data_json = json.dumps(kwargs)
    # data.update(**kwargs)
    # logger.debug(data)
    # data_json = json.dumps(data)
    headers = {'Content-type': 'application/json'}
    try:
        response = requests.post(post_url, timeout=TIMEOUT, auth=(CLIENT_USERNAME, CLIENT_PASSWORD), data=data_json,
                             headers=headers)
    except:
        logger.exception('An error occurred; retrying in {} seconds'.format(RETRY))
        time.sleep(RETRY)
        response = orpheus_post(post_url, data, **kwargs)
    return(response)

def orpheus_patch(patch_url, data, **kwargs):
    data.update(**kwargs)
    data_json = json.dumps(data)
    headers = {'Content-type': 'application/json'}
    try:
        response = requests.patch(patch_url, timeout=TIMEOUT, auth=(CLIENT_USERNAME, CLIENT_PASSWORD), data=data_json,
                              headers=headers)
    except:
        logger.exception('An error occurred; retrying in {} seconds'.format(RETRY))
        time.sleep(RETRY)
        response = orpheus_patch(patch_url, data, **kwargs)
    return(response)

def orpheus_delete(delete_url):
    try:
        response = requests.delete(delete_url, auth=(CLIENT_USERNAME, CLIENT_PASSWORD))
    except:
        logger.exception('An error occurred; retrying in {} seconds'.format(RETRY))
        time.sleep(RETRY)
        response = orpheus_delete(delete_url)
    return(response)
# endregion

# region translation functions
def node_name2id(name):
    '''
    :param name: Node name to lookup
    :return: id of node name in Orpheus or, if name was not found, None
    '''

    url = ORPHEUS_URL + 'policies/api/nodes/?name=' + escape_invalid_url(name)
    try:
        return(orpheus_get(url).json()['results'][0]['id'])
    except IndexError:
        return(None)

def node_issn2id(issn):
    
    '''
    :param issn: Node issn or eissn to lookup
    :return: id of node in Orpheus or, if issn was not found, None
    '''
    url = ORPHEUS_URL + 'policies/api/nodes/?issn=' + issn
    try:
        return(orpheus_get(url).json()['results'][0]['id'])
    except IndexError:
        return(None)

def node_id2record(id):
    '''
    :param id: Node id to lookup
    :return: record of node id in Orpheus or, if id was not found, None
    '''
    url = ORPHEUS_URL + 'policies/api/nodes/?id=' + str(id)
    try:
        return (orpheus_get(url).json()['results'][0])
    except IndexError:
        return (None)

def node_name2record(name):
    '''
    :param name: Node name to lookup
    :return: record of node name in Orpheus or, if name was not found, None
    '''
    url = ORPHEUS_URL + 'policies/api/nodes/?name=' + escape_invalid_url(name)
    logger.debug(url)
    try:
        return (orpheus_get(url).json()['results'][0])
    except IndexError:
        return (None)

def node_name2records(name):
    '''
    :param name: Node name to lookup
    :return: list of node records in Orpheus matching the given name
    '''
    url = ORPHEUS_URL + 'policies/api/nodes/?name=' + escape_invalid_url(name)
    logger.debug(url)
    return (orpheus_get(url).json()['results'])

def node_issn2record(issn):
    '''
    :param issn: Node issn or eissn to lookup
    :return: record of node in Orpheus or, if issn was not found, None
    '''
    url = ORPHEUS_URL + 'policies/api/nodes/?issn=' + issn
    try:
        return (orpheus_get(url).json()['results'][0])
    except IndexError:
        return (None)

def node_issn2records(issn):
    '''
    :param issn: Node issn or eissn to lookup
    :return: list of node records in Orpheus matching the given issn
    '''
    url = ORPHEUS_URL + 'policies/api/nodes/?issn=' + issn
    #logger.debug(url)
    return (orpheus_get(url).json()['results'])

def romeo_id2records(romeo_id):
    '''
    :param romeo_id: Publisher id in RoMEO database
    :return: Orpheus records matching romeo_id
    '''
    url = ORPHEUS_URL + 'policies/api/nodes/?romeo=' + romeo_id
    return (orpheus_get(url).json()['results'])
# endregion

# region get functions
def get_node4node_id(node_id):
    url = ORPHEUS_URL + 'policies/api/nodes/?id=' + str(node_id)
    return(orpheus_get(url).json()['results'][0])

def get_synonyms4node_id(node_id):
    url = ORPHEUS_URL + 'policies/api/nodes/attributes/?id=' + str(node_id)
    logger.debug(url)
    return(orpheus_get(url).json()['results'][0])

def get_gold_policies4node_id(node_id):
    url = ORPHEUS_URL + 'policies/api/goldpolicies/?node=' + str(node_id)
    return(orpheus_get(url))

def get_green_policies4node_id(node_id):
    url = ORPHEUS_URL + 'policies/api/greenpolicies/?node=' + str(node_id)
    return(orpheus_get(url))

def get_oastatus4node_id(node_id):
    url = ORPHEUS_URL + 'policies/api/oastatus/?node=' + str(node_id)
    return(orpheus_get(url))

def get_sources4name(name):
    url = ORPHEUS_URL + 'policies/api/sources/?name=' + escape_invalid_url(str(name))
    return(orpheus_get(url))

def get_licence4shortname(name):
    url = ORPHEUS_URL + 'policies/api/licences/?shortname=' + escape_invalid_url(str(name))
    return(orpheus_get(url))

def get_licence4longname(name):
    url = ORPHEUS_URL + 'policies/api/licences/?longname=' + escape_invalid_url(str(name))
    return(orpheus_get(url))

def get_outlet4name(name):
    url = ORPHEUS_URL + 'policies/api/outlets/?name=' + escape_invalid_url(str(name))
    return(orpheus_get(url))

def get_version4shortname(name):
    url = ORPHEUS_URL + 'policies/api/versions/?shortname=' + escape_invalid_url(str(name))
    return(orpheus_get(url))

def get_version4longname(name):
    url = ORPHEUS_URL + 'policies/api/versions/?longname=' + escape_invalid_url(str(name))
    return(orpheus_get(url))

def get_gold_policies():
    url = ORPHEUS_URL + 'policies/api/goldpolicies/'
    return(orpheus_get(url))

def get_green_policies():
    url = ORPHEUS_URL + 'policies/api/greenpolicies/'
    return(orpheus_get(url))

def get_oastatus():
    url = ORPHEUS_URL + 'policies/api/oastatus/'
    return(orpheus_get(url))
# endregion

# region post functions
def validate_node_fields(k, v):
    if v:
        if k in ['parent', 'romeo_id']:
            return k, int(v)
        elif k in ['issn', 'eissn']:
            t = re.compile('[0-9]{4,4}-[0-9]{3,3}[0-9X]')
            m = t.match(v)
            if m:
                return k, v
            else:
                return k, None
        else:
            return k, v
    else:
        return k, v

def create_node(node_name, node_name_status, node_type, node_source, node_vetted=False, **kwargs):
    url = ORPHEUS_URL + 'policies/api/nodes/'
    #logger.debug(kwargs)
    validated_kwargs = {}
    for k, v in kwargs.items():
        valid_k, valid_v = validate_node_fields(k, v)
        validated_kwargs[valid_k] = valid_v
    data = {
        "name" : node_name,
        "name_status" : node_name_status,
        "type" : node_type,
        "source" : node_source,
        "vetted" : node_vetted
    }
    # logger.debug(validated_kwargs)
    # logger.debug(data)
    return(orpheus_post(url, data, **validated_kwargs))

def update_node(node_id, **kwargs):
    url = ORPHEUS_URL + 'policies/api/nodes/' + str(node_id) + '/'
    data = {}
    return(orpheus_patch(url, data, **kwargs))

def create_licence(short_name, long_name=None, url_field=None):
    url = ORPHEUS_URL + 'policies/api/licences/'
    data = {
        "short_name" : short_name,
        "long_name" : long_name,
        "url" : url_field
    }
    return(orpheus_post(url, data))

def create_source(description, type='WEBSITE', url_field=None):
    url = ORPHEUS_URL + 'policies/api/sources/'
    data = {
        "description" : description,
        "type" : type,
        "url" : url_field
    }
    return(orpheus_post(url, data))

def create_oastatus(node_id, oa_status, source, vetted=False, **kwargs):
    url = ORPHEUS_URL + 'policies/api/oastatus/'
    logger.debug(kwargs)
    data = {
        'node' : node_id,
        'oa_status' : oa_status,
        'source' : source,
        'vetted' : vetted
    }
    return (orpheus_post(url, data, **kwargs))

def update_oastatus(policy_id, **kwargs):
    url = ORPHEUS_URL + 'policies/api/oastatus/' + str(policy_id) + '/'
    data = {}
    return(orpheus_patch(url, data, **kwargs))

def create_green_policy(node_id, outlet_list, version_list, source, vetted=False, **kwargs):
    url = ORPHEUS_URL + 'policies/api/greenpolicies/'
    data = {
        'node' : node_id,
        'outlet' : outlet_list,
        'version' : version_list,
        'source' : source,
        'vetted' : vetted
    }
    return (orpheus_post(url, data, **kwargs))

def update_green_policy(green_policy_id, **kwargs):
    url = ORPHEUS_URL + 'policies/api/greenpolicies/' + str(green_policy_id) + '/'
    data = {}
    return(orpheus_patch(url, data, **kwargs))

def create_gold_policy(node_id, source, vetted=False, **kwargs):
    url = ORPHEUS_URL + 'policies/api/goldpolicies/'
    logger.debug(kwargs)
    data = {
        'node': node_id,
        'source': source,
        'vetted': vetted
    }
    return (orpheus_post(url, data, **kwargs))

def update_gold_policy(gold_policy_id, **kwargs):
    url = ORPHEUS_URL + 'policies/api/goldpolicies/' + str(gold_policy_id) + '/'
    data = {}
    return(orpheus_patch(url, data, **kwargs))
# endregion

# region delete functions
def delete_green_policy(green_policy_id):
    url = ORPHEUS_URL + 'policies/api/greenpolicies/' + str(green_policy_id) + '/'
    return(orpheus_delete(url))

def delete_gold_policy(gold_policy_id):
    url = ORPHEUS_URL + 'policies/api/goldpolicies/' + str(gold_policy_id) + '/'
    return(orpheus_delete(url))

def delete_oastatus(policy_id):
    url = ORPHEUS_URL + 'policies/api/oastatus/' + str(policy_id) + '/'
    return(orpheus_delete(url))
# endregion

# # Function below replaced by orpheus.policies.management.commands.nuke_content_tables, which is much faster. To run it:
# # $ python manage.py nuke_content_tables
# def nuke_content_tables():
#     if input('Are you sure you want to delete all Orpheus content tables (Nodes, Open Access stata, Gold policies'
#           'and Green Policies? (y/n)') in ['y', 'Y']:
#         logger.debug('Fetching green policies')
#         green_policies = get_green_policies()
#         if green_policies.ok:
#             for gp in green_policies.json()['results']:
#                 delete_green_policy(gp['id'])
#                 logger.debug('Deleted green policy {}'.format(gp['id']))
#         logger.debug('Fetching gold policies')
#         gold_policies = get_gold_policies()
#         if gold_policies.ok:
#             for gp in gold_policies.json()['results']:
#                 delete_gold_policy(gp['id'])
#                 logger.debug('Deleted gold policy {}'.format(gp['id']))
#         logger.debug('Fetching oastata')
#         policies = get_oastatus()
#         if policies.ok:
#             for p in policies.json()['results']:
#                 delete_oastatus(p['id'])
#                 logger.debug('Deleted oastatus {}'.format(p['id']))

