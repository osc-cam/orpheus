'''
A collection of generic parsers of external datasets that need to be imported into Orpheus.
'''

import difflib
import json
import logging
import random
import sys
from unidecode import unidecode
import urllib.parse

import doaj_client
import orpheus_client
import romeo_client

PUBLISHER_DISAMBIGUATION_STRING = ' (Publisher)'

illegal_characters = {
    'İ' : 'I',
    '\u200b' : '',
}

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
# logger.addHandler(ch)

def convert_illegal_characters(str):
    for k, v in illegal_characters.items():  # escape illegal characters
        str = str.replace(k, v)
    return str

def act_on_orpheus_match(npi, mr_id, mr, match_type, test_mode=False):
    '''
    This function attempts to make a distinction between name matches due to synonymy and matches due to homonymy.
    If a match proves to be a synonym, no new Orpheus node will be created. If it proves to be a homonym,
    then the node name is modified for disambiguation and a new node is created.

    PROBLEM: There is quite a bit of overlap between this function and server_data_match_node()

    :param npi: node_parser_instance i.e. an instance of the NodeParser class representing the prospective
                new node (queried node)
    :param mr_id: matched_record_id i.e. the id of the node record returned by the Orpheus API as a match for npi
    :param mr: matched_record i.e. the node record returned by the Orpheus API as a match for npi
    :param match_type: 'issn' or 'name'
    :param test_mode:
    :return:
    '''

    def check_publishers(npi, mr):
        '''
        Checks if publishers are identified as synonyms in Orpheus or if they are unique
        :return: boolean, True if they are unique or False if they are synonyms
        '''
        unique = True
        logger.debug('Attempting to find Orpheus match to npi publisher {}'.format(npi.publisher))
        p_parser = NodeParser(name=npi.publisher, type='PUBLISHER')
        p_parser.match2node()
        npi_publisher_record = p_parser.node_record #orpheus_client.node_name2record(npi.publisher)
        logger.debug('Attempting to find Orpheus match to mr publisher {}'.format(mr['publisher']))
        mr_p_parser = NodeParser(name=mr['publisher'], type='PUBLISHER')
        mr_p_parser.match2node()
        mr_publisher_record = mr_p_parser.node_record #orpheus_client.node_name2record(mr['publisher'])
        if npi_publisher_record and mr_publisher_record:
            if npi_publisher_record['name_status'] not in ['PRIMARY']:
                npi_preferred_node_id = npi_publisher_record['synonym_of']
            else:
                npi_preferred_node_id = npi_publisher_record['id']
            if mr_publisher_record['name_status'] not in ['PRIMARY']:
                mr_preferred_node_id = mr_publisher_record['synonym_of']
            else:
                mr_preferred_node_id = mr_publisher_record['id']

            if npi_preferred_node_id == mr_preferred_node_id:
                logger.debug('Journal ({}) names are identical in Orpheus and queried node; publisher names '
                             'are distinct, but identified as synonyms in Orpheus. '
                             'No new node is needed'.format(npi.name))
                unique = False
            else:
                logger.debug('Publishers match different preferred Orpheus nodes. They are not synonyms. '
                             'npi_preferred_node_id: {}; mr_preferred_node_id: {}'.format(npi_preferred_node_id,
                                                                                          mr_preferred_node_id))
        else:
            logger.debug('Could not find Orpheus match to at least one of the publishers')
        return unique

    def check_mr_name(npi, mr):
        '''
        A function to check and, if necessary, normalise the name of the Orpheus matching record to avoid false
        negatives in the outer function's duplicate detection logic
        :return: name of the Orpheus matching record, normalised for comparison with queried node name
        '''
        logger.debug('mr_name: {}; npi.name: {}; npi.publisher: {}'.format(mr['name'], npi.name, npi.publisher))
        if ('(journal)' in npi.name.lower()) or ('(publisher)' in npi.name.lower()):
            mr_name = mr['name'].lower().strip()
        else:
            mr_name = mr['name'].lower().replace('(journal)','').replace('(publisher)','').strip()

        if npi.publisher.strip() and (unidecode(npi.publisher).lower() in unidecode(mr_name).lower()) and \
                (('({})'.format(unidecode(npi.publisher).lower()) not in unidecode(npi.name).lower()) or \
                (unidecode(npi.name).lower().replace(unidecode(npi.publisher).lower(), '') == '')): # npi.name is just npi.publisher and nothing else
            logger.debug('Name of matched Orpheus record contains queried node publisher name. Ignoring publisher name')
            mr_name = mr_name.replace('({})'.format(npi.publisher.lower()), '')\
                .replace('({})'.format(unidecode(npi.publisher).lower()), '').strip()
        return mr_name

    def populate_npi_with_mr(npi, mr):
        '''
        A function to set all attributes of npi to values found in matching Orpheus record. This is simplistic and
        misses the chance of improving mr (in the style of function server_data_match_node()). However, simplicity is a
        good thing for now!
        '''
        npi.name = mr['name']
        npi.name_status = mr['name_status']
        npi.issn = mr['issn']
        npi.eissn = mr['eissn']
        npi.url = mr['url']
        npi.romeo_id = mr['romeo_id']
        npi.synonym_of = mr['synonym_of']
        npi.source = mr['source']
        npi.type = mr['type']
        npi.node_record = mr
        npi.node_id = mr['id']
        npi.publisher_node_id = mr['parent']

    def get_mr_publisher_name(mr):
        '''
        Get name of mr Orpheus parent if it has a parent
        :return: parent name or None
        '''
        if mr['parent']:
            parent_record = orpheus_client.node_id2record(mr['parent'])
            return parent_record['name']
        return None

    def get_mr_synonyms(mr):
        '''
        Queries Orpheus and returns any synonyms of mr in the database. If mr is not a preferred name, this
        function returns the preferred name and all its synonyms (including mr itself).
        :return: list of Orpheus synonyms of mr
        '''
        if mr['name_status'] == 'PRIMARY':
            node_attributes = orpheus_client.get_synonyms4node_id(mr['id'])
            synonyms = node_attributes['synonyms']
        else:
            node_attributes = orpheus_client.get_synonyms4node_id(mr['synonym_of'])
            synonyms = node_attributes['synonyms']
            # also add the preferred name
            preferred_name = orpheus_client.get_node4node_id(mr['synonym_of'])
            synonyms.append(preferred_name)
        return synonyms

    def make_decision_on_issn_match(npi, mr, mr_name, create_synonym):
        '''
        Function to handle issn matches. Decides for those matches whether or not to create a new node and of what
        kind (preferred name or synonym)
        :return: two booleans indicating whether or not to create_preferred_name or create_synonym
        '''
        if mr_name == npi.name.lower().strip():
            logger.debug(
                'ISSN and journal name in Orpheus ({}) identical to values in queried node ({}) '
                '[case insensitive]. No new node is needed'.format(mr_name, npi.name))
        else:
            mr_synonyms = get_mr_synonyms(mr)
            logger.debug(
                'ISSN in Orpheus ({}) identical to values in queried node ({}). However, the names are different. '
                'Checking Orpheus synonyms of matching node: {}'.format(mr_name, npi.name, mr_synonyms))
            synonym_match = False
            for syn in mr_synonyms:
                logger.debug('Checking synonym {}'.format(syn['name']))
                if (syn['name'].lower().replace('({})'.format(syn['type'].lower()), '') == npi.name.lower()) or \
                        (syn['name'].lower() == '{} ({})'.format(npi.name, npi.publisher).lower()):
                    logger.debug('ISSN in Orpheus ({}) identical to values in queried node. Queried node name ({}) '
                                'matches synonym of matched node ({}). '
                                 'No new node is needed'.format(mr_name, npi.name, syn['name']))
                    synonym_match = True
                    break
            if not synonym_match:
                logger.debug('Name match to synonyms of ISSN match could not be found. Create a new synonym')
                create_synonym = True
        return create_synonym

    def make_decision_on_name_match(npi, mr, mr_name, create_preferred_name, create_synonym):
        if npi.issn and npi.eissn and mr['issn'] and mr['eissn'] and \
            (npi.issn not in [mr['issn'], mr['eissn']]) and \
            (npi.eissn not in [mr['issn'], mr['eissn']]):
            logger.debug('Both queried and matched nodes have issn and eissn. None of these identifiers match. '
                         'Create a new node.')
            if npi.publisher and (npi.publisher == mr['publisher']):
                logger.debug('Journal ({}) and publisher ({}) names are identical in Orpheus and queried node. '
                             'Appending issn to new node')
                npi.name += ' ({})'.format(npi.issn)

        elif (npi.issn or npi.eissn) and (mr['issn'] or mr['eissn']) and (
                        (npi.issn and (npi.issn in [mr['issn'], mr['eissn']])) or \
                        (npi.eissn and (npi.eissn in [mr['issn'], mr['eissn']]))
                    ):
            logger.debug('Both queried and matched nodes have at least one matching issn. No new node is needed.')
            create_preferred_name = False
        elif mr['publisher'] is None and (mr_name == npi.name.lower()):
            if mr['type'] == npi.type:
                logger.debug('{} ({}) names are identical in Orpheus and queried node. Matched node contains no '
                         'publisher information. No new node is needed'.format(npi.type, npi.name))
                create_preferred_name = False
            else:
                logger.debug('Queried node is {} and matched node is {}. Create new node with '
                             'name += type'.format(npi.type, mr['type']))
                npi.name += ' ({})'.format(npi.type.capitalize())
        elif mr_name == npi.name.lower():
            if npi.publisher and (npi.publisher == mr['publisher']):
                logger.debug('Journal ({}) and publisher ({}) names are identical in Orpheus and queried node. '
                             'No new node is needed'.format(npi.name, npi.publisher))
                create_preferred_name = False
            elif npi.type != mr['type']:
                logger.debug('Queried name ({}) is a {} and matched ({}) name is a {}. Append type to queried '
                             'name and create a new node'.format(npi.name, npi.type, mr_name, mr['type']))
                npi.name += ' ({})'.format(npi.type.capitalize())
            else:
                logger.debug('Journal names are identical, but publisher names are not. '
                             'Check if publisher names are synonyms')
                create_preferred_name = check_publishers(npi, mr)
        else:  # create a new synonym of match
            create_synonym = True

        return create_preferred_name, create_synonym


    if mr_id:
        create_preferred_name = True
        create_synonym = False
        mr_name = check_mr_name(npi, mr)
        mr['publisher'] = get_mr_publisher_name(mr)
        logger.debug('mr_name: {}; mr_publisher: {}'.format(mr_name, mr['publisher']))

        if match_type == 'issn':
            create_preferred_name = False
            create_synonym = make_decision_on_issn_match(npi, mr, mr_name, create_synonym)
        elif match_type == 'name':
            create_preferred_name, create_synonym = make_decision_on_name_match(npi, mr, mr_name, create_preferred_name,
                                                                                create_synonym)
        else:
            logger.critical('match_type ({}) not supported'.format(match_type))
            sys.exit('ERROR generic_parser: match_type ({}) not supported'.format(match_type))

        logger.debug('create_preferred_name: {}; create_synonym: {}'.format(create_preferred_name, create_synonym))

        if create_preferred_name:
            logger.debug('Queried node and matched node are not duplicates or synonyms. Create a new preferred name')
            mr_id, mr = npi.create_node()
        elif create_synonym:
            logger.debug('Name in Orpheus ({}) does not match queried node name ({}). '
                         'Creating synonym'.format(mr_name, npi.name))
            npi.name_status = 'SYNONYM'
            if not npi.synonym_of:
                if mr['name_status'] != 'PRIMARY':
                    mr_id = mr['synonym_of']
                logger.debug('Setting synonym of new node to Orpheus id {}'.format(mr_id))
                npi.synonym_of = mr_id
            else:
                logger.debug('NodeParser instance already set as synonym of Orpheus id {}'.format(npi.synonym_of))
            mr_id, mr = npi.create_node()
        else:
            logger.debug('No new node is needed')

    else:
        logger.debug(
            'Match not found in Orpheus for queried node name ({}). Creating a new node'.format(
                npi.name))
        if test_mode:
            mr_id, mr = npi.create_node(force_creation=True)
        else:
            mr_id, mr = npi.create_node()

    return mr_id, mr

class GreenPolicyInstance:
    '''
    A GreenPolicy object
    '''
    def __init__(self):
        self.node = None # required
        self.outlet = []
        self.version = []
        self.deposit_allowed = True
        self.version_embargo_months = None
        self.version_green_licence = None
        self.version_note = None
        self.source = None # required
        self.verbatim = None
        self.problematic = False
        self.vetted = False
        self.vetted_date = None
        self.last_checked = None
        self.superseded = False
        self.superseded_date = None

    def as_dict(self):
        policy_dict = {
            "node": self.node,
            "deposit_allowed": self.deposit_allowed,
            "version_embargo_months": self.version_embargo_months,
            "version_note": self.version_note,
            "verbatim": self.verbatim,
            "problematic": self.problematic,
            "vetted": self.vetted,
            "vetted_date": self.vetted_date,
            "last_checked": self.last_checked,
            "superseded": self.superseded,
            "superseded_date": self.superseded_date,
            "version_green_licence": self.version_green_licence,
            "source": self.source,
            "outlet": self.outlet,
            "version": self.version
        }
        return policy_dict

class GoldPolicyInstance:
    '''
    A GoldPolicy object
    '''
    def __init__(self):
        self.node = None # required
        self.apc_currency = None
        self.apc_value_min = None
        self.apc_value_max = None
        self.apc_note = None
        self.licence_options = []
        self.default_licence = None
        self.source = None # required
        self.verbatim = None
        self.problematic = False
        self.vetted = False
        self.vetted_date = None
        self.last_checked = None
        self.superseded = False
        self.superseded_date = None
    def as_dict(self):
        policy_dict = {
            "apc_currency": self.apc_currency,
            "apc_value_min": self.apc_value_min,
            "apc_value_max": self.apc_value_max,
            "apc_note": self.apc_note,
            "verbatim": self.verbatim,
            "problematic": self.problematic,
            "vetted": self.vetted,
            "vetted_date": self.vetted_date,
            "last_checked": self.last_checked,
            "superseded": self.superseded,
            "superseded_date": self.superseded_date,
            "node": self.node,
            "default_licence": self.default_licence,
            "source": self.source,
            "licence_options": self.licence_options
        }
        return policy_dict

class LicenceParser:
    '''
    Parses licences
    '''
    def __init__(self, short_name=None, long_name=None, url=None):
        self.short_name = short_name
        self.long_name = long_name
        self.url = url
    def match_licence(self):
        if self.short_name:
            r = orpheus_client.get_licence4shortname(self.short_name)
            if r.ok and r.json():
                return r.json()['results'][0]['id']
            else:
                if self.long_name:
                    r = orpheus_client.get_licence4longname(self.long_name)
                    if r.ok and r.json():
                        return r.json()['results'][0]['id']
                    else:
                        sys.exit('ERROR trying to match licence {} {}. Error message: {}'.format(self.short_name,
                                                                                                 self.long_name,
                                                                                                 r.text))
    def match_or_create_licence(self):
        if self.short_name:
            r = orpheus_client.get_licence4shortname(self.short_name)
            if r.ok and r.json():
                return r.json()['results'][0]['id']
            else:
                if self.long_name:
                    r = orpheus_client.get_licence4longname(self.long_name)
                    if r.ok and r.json():
                        return r.json()['results'][0]['id']
                    else:
                        r = orpheus_client.create_licence(self.short_name, long_name=self.long_name, url_field=self.url)
                        if r.ok and r.json():
                            return r.json()['id']
                        else:
                            sys.exit('ERROR trying to create licence {}. Error message: {}'.format(self.short_name,
                                                                                                   r.text))

class OutletParser:
    '''
    Parses outlets
    '''
    def __init__(self, name=None, url=None):
        self.name = name
        self.url = url
    def match_outlet(self):
        if self.name:
            r = orpheus_client.get_outlet4name(self.name)
            if r.ok and r.json():
                return r.json()['results'][0]['id']
            else:
                sys.exit('ERROR trying to match outlet {}. Error message: {}'.format(self.name, r.text))

class SourceParser:
    '''
    Parses sources
    '''
    def __init__(self, description, type='WEBSITE', url=None):
        self.description = description
        self.type = type
        self.url = url
    def match_or_create_source(self):
        r = orpheus_client.get_sources4name(self.description)
        if r.ok and r.json():
            return r.json()['results'][0]['id']
        else:
            r = orpheus_client.create_source(self.description, type=self.type, url_field=self.url)
            if r.ok and r.json():
                return r.json()['id']
            else:
                sys.exit('ERROR trying to create source {}. Error message: {}'.format(self.description, r.text))

class VersionParser:
    '''
    Parses versions
    '''
    def __init__(self, short_name=None, long_name=None):
        self.short_name = short_name
        self.long_name = long_name
    def match_version(self):
        if self.short_name:
            r = orpheus_client.get_version4shortname(self.short_name)
            if r.ok and r.json():
                return r.json()['results'][0]['id']
            else:
                if self.long_name:
                    r = orpheus_client.get_version4longname(self.long_name)
                    if r.ok and r.json():
                        return r.json()['results'][0]['id']
                    else:
                        sys.exit('ERROR trying to match version {} {}. '
                                 'Error message: {}'.format(self.short_name, self.long_name, r.text))
                else:
                    sys.exit('ERROR trying to match version. Short name ({}) '
                             'unmatched and long name ({}) not known'.format(self.short_name, self.long_name))
        else:
            sys.exit('ERROR trying to match version. Short name ({}) not known'.format(self.short_name))


from orpheus_constants import DOAJ_SOURCE_ID, CCBY_ID, CCBYNC_ID, CCBYNCND_ID

class NodeParser:
    '''
    Parses data for a single node (journal, publisher or conference), including linked policies.
    '''

    def __init__(self, name='', name_status='PRIMARY', issn='', eissn='', publisher='', publisher_node_record=None,
                 publisher_node_id=None, romeo_id=None, synonym_of=None, source='', type='JOURNAL', url=None):
        if len(name) > 200:
            name = name[:197] + '...'
        self.name = convert_illegal_characters(name).replace('  ', ' ').replace('  ', ' ')
        self.name_status = name_status
        self.issn = issn
        self.eissn = eissn
        self.publisher = convert_illegal_characters(publisher).replace('  ', ' ').replace('  ', ' ')
        if url and ('_' in url): # ignore url if it contains underscores; Django does not support them
            url = None
        self.url = url
        self.romeo_id = romeo_id
        self.synonym_of = synonym_of
        self.source = source
        self.type = type
        self.node_record = None
        self.publisher_node_record = publisher_node_record
        self.node_id = None
        self.publisher_node_id = publisher_node_id
        self.oa_status = None  # 'FULLY_OA'
        self.gold_policy = None
        self.green_policies = []

    def populate_from_node_record(self):
        '''
        Populates NodeParser's variables from self.node_record
        :return:
        '''
        self.name = self.node_record['name']
        self.name_status = self.node_record['name_status']
        self.issn = self.node_record['issn']
        self.eissn = self.node_record['eissn']
        self.url = self.node_record['url']
        self.synonym_of = self.node_record['synonym_of']
        self.type = self.node_record['type']
        self.node_id = self.node_record['id']

    # region node functions
    def doaj_match(self):
        '''
        Check if journal is in DOAJ and, if so, import relevant data into Orpheus
        :return:
        '''

        doaj_licence_dict = {
            "CC BY": CCBY_ID,
            "CC BY-NC": CCBYNC_ID,
            "CC BY-NC-ND": CCBYNCND_ID,
        }

        doaj_data = doaj_client.issn_search(self.issn)
        if doaj_data:
            # Add oa_status to Orpheus node
            self.oa_status = 'FULLY_OA'
            _ = self.source
            self.source = DOAJ_SOURCE_ID
            logger.debug('Calling PolicyMatcher(self_outer, policy_type=oa_status).match()')
            self.PolicyMatcher(self, policy_type='oa_status').match()
            self.source = _

            # Add gold policy to Orpheus node
            doaj_licence = doaj_data['bibjson']['license']['title']
            doaj_apc_currency = doaj_data['bibjson']['apc']['currency']
            doaj_apc_value = int(doaj_data['bibjson']['apc']['average_price'])
            logger.debug("doaj_licence: {}; doaj_apc_currency: {}; doaj_apc_value: {}".format(doaj_licence,
                                                                                              doaj_apc_currency,
                                                                                              doaj_apc_value))
            gp = GoldPolicyInstance()
            if self.name_status not in ['PRIMARY']:
                preferred_node_id = self.synonym_of
            else:
                preferred_node_id = self.node_id
            gp.node = preferred_node_id
            gp.source = DOAJ_SOURCE_ID
            logger.debug('doaj_licence: {}'.format(doaj_licence))
            gp.default_licence = doaj_licence_dict[doaj_licence]
            gp.apc_currency = doaj_apc_currency
            gp.apc_value_min = doaj_apc_value
            gp.apc_value_max = doaj_apc_value
            logger.debug("Calling j_parser.PolicyMatcher(j_parser, policy_type='gold').match(**gp.as_dict())")
            self.PolicyMatcher(self, policy_type='gold').match(**gp.as_dict())

    def get_issn_from_romeo(self):
        '''
        Attempts to obtain an issn for journal name via the RoMEO API
        :return:
        '''
        query = '?jtitle={}'.format(urllib.parse.quote(self.name))
        romeo = romeo_client.parser(query)
        romeo.parse_response()
        if romeo.output_dict['apicontrol'] == 'journal':
            logger.debug('RoMEO query returned a single journal')
            if romeo.output_dict['outcome'] in ['singleJournal', 'uniqueZetoc']:
                romeo_issn = romeo.output_dict['romeo_issn_list']
                logger.debug('romeo_issn: {}'.format(romeo_issn))
                self.issn = romeo_issn[0]

            elif (romeo.output_dict['outcome'] in ['manyJournals']):
                if self.publisher:
                    for dic in romeo.output_dict['journals_dicts']: # try exact match
                        if self.publisher in [dic['zetocpub'], dic['romeopub']]:
                            self.issn = dic['issn']
                            logger.debug('More than one journal found in RoMEO; '
                                             'using issn of EXACT publisher match ({})'.format(self.publisher))
                            break
                    if not self.issn: # try close match
                        closest_publisher = None
                        for romeo_pub in romeo.output_dict['romeo_publisher_list']:
                            if self.publisher.lower() in romeo_pub.lower().strip():
                                closest_publisher = romeo_pub
                                break
                        if not closest_publisher:
                            closest_publisher = difflib.get_close_matches(self.publisher,
                                                                      romeo.output_dict['romeo_publisher_list'],
                                                                      n=1, cutoff=0.3)
                        if closest_publisher:
                            for dic in romeo.output_dict['journals_dicts']:
                                if closest_publisher in [dic['zetocpub'], dic['romeopub']]:
                                    self.issn = dic['issn']
                                    logger.debug('More than one journal found in RoMEO; '
                                                 'using issn of CLOSEST publisher match ({})'.format(closest_publisher))
                                    break
                    if not self.issn:
                        logger.debug('More than one journal found in RoMEO; none of the RoMEO publishers ({}) matched '
                                     'the queried publisher ({}) closely '
                                     'enough'.format(romeo.output_dict['romeo_publisher_list'], self.publisher))
                else:
                    logger.debug('ISSN unresolved. More than one journal found in RoMEO; queried node has no publisher '
                                 'info for disambiguation')
            elif romeo.output_dict['outcome'] in ['notFound']:
                logger.debug('ISSN unresolved. RoMEO outcome is {} for query: {}'.format(romeo.output_dict['outcome'],
                                                                                         query))
            else:
                error_message = 'Unexpected RoMEO outcome {} for query: {}'.format(romeo.output_dict['outcome'], query)
                logger.debug(error_message)
                sys.exit(error_message)
        else:
            error_message = 'RoMEO query {} did not return a journal'.format(query)
            logger.error(error_message)
            sys.exit(error_message)

    def match2romeo_publisher(self, test_mode=False):
        '''
        Attempts to identify a match in RoMEO using their API. If a RoMEO match is found externally, attempts to
        identify an Orpheus match corresponding to the RoMEO publisher
        :param test_mode: if True, this function performs a dry run. It does not query the RoMEO API and returns
            instead hardcoded romeo and node ids known to exist in Orpheus.
        :return: The id of the romeo publisher if RoMEO contains self-archiving policy and the node
            exists in Orpheus; None if not
        '''

        def id_match(romeo_id):
            '''
            :param outer: instance of NodeParser class
            :param romeo_id: the id we wish to match
            :return: id of single match or id of PRIMARY match if more than one match is found
            '''
            matching_records = orpheus_client.romeo_id2records(romeo_id)
            if matching_records:
                if len(matching_records) == 1:
                    return matching_records[0]['id']
                elif len(matching_records) > 1: # match to PRIMARY name
                    logger.debug('matching_records: {}'.format(matching_records))
                    for r in matching_records:
                        if r['name_status'] == 'PRIMARY':
                            return r['id']
            return None

        if test_mode == True:
            romeo_id = 1
            node_id = 611
            return romeo_id, node_id

        if self.issn:
            query = '?issn={}'.format(self.issn)
        elif self.eissn:
            query = '?issn={}'.format(self.eissn)
        elif self.name:
            query = '?jtitle={}'.format(urllib.parse.quote(self.name))
        logger.debug('query: {}'.format(query))
        romeo = romeo_client.parser(query)
        romeo.parse_response()
        if romeo.output_dict['apicontrol'] == 'journal':
            logger.debug('RoMEO query returned a single journal')
            if romeo.output_dict['outcome'] == 'singleJournal':
                romeo_id = romeo.output_dict['romeo_id_list'][0]

                romeo_issn = romeo.output_dict['romeo_issn_list'][0]
                if self.issn:
                    if self.issn != romeo_issn:
                        logger.warning('ISSN for this journal ({}) '
                                       'does not match value in RoMEO ({})'.format(self.issn, romeo_issn))
                else:
                    self.issn = romeo_issn

                if romeo_id in ['journal', 'DOAJ']:
                    logger.debug('Sherpa RoMEO does not contain self-archiving policy for this journal. '
                                  'Query: {}'.format(query))
                else:
                    node_id = id_match(romeo_id)
                    if not node_id:
                        error_message = 'Orpheus does not contain a publisher node matching romeo id {}. ' \
                                        'This should have been created during the initial import of RoMEO publishers ' \
                                        'using romeo_parser. If needed, nuke the Orpheus database and repopulate ' \
                                        'using romeo_parser.'.format(romeo_id)
                        logger.error(error_message)
                        raise()
                    else:
                        logger.info('RoMEO publisher match found: romeo_id {}; orpheus_id {}'.format(romeo_id, node_id))
                        if self.type == 'PUBLISHER':
                            self.node_id = node_id
                            self.romeo_id = romeo_id
                        else:
                            self.publisher_node_id = node_id
                        return romeo_id, node_id
            elif romeo.output_dict['outcome'] == 'uniqueZetoc':
                logger.debug('Sherpa RoMEO does not contain self-archiving policy for this journal. '
                             'Query: {}'.format(query))
        else:
            logger.error('RoMEO query {} returned more than '
                          'one publisher'.format(query))
            raise()

    def match2node(self):
        '''
        Attempts to identify an existing node in Orpheus matching the new data given to the parser
        :return: A list containing the Orpheus node id, full record and match type [id, record, match type] or
        [None, None, None] if a match could not be found
        '''
        def issn_match(outer, issn):
            '''
            :param outer: instance of NodeParser class
            :param issn: the issn or eissn we wish to match
            :return: string 'issn' if a match is found; otherwise None
            '''
            match = None
            matching_records = orpheus_client.node_issn2records(issn)
            if matching_records:
                if len(matching_records) == 1:
                    match = matching_records[0]
                elif len(matching_records) > 1: # match to most similar name
                    names = {}
                    for r in matching_records:
                        names[r['name']] = r
                    logger.debug('matches ({}): {}'.format(len(names.keys()), names.keys()))
                    match = names[difflib.get_close_matches(outer.name, names.keys(), n=1, cutoff=0)[0]]
                    logger.debug('closest match: {}'.format(match))
                if match and (match['type'] == outer.type):
                    outer.node_record = match
                    return 'issn'
            return None

        def name_match(outer, name):
            '''
            :param outer: instance of NodeParser class
            :param name: the name we wish to match
            :return: string 'name' if a match is found; otherwise None
            '''
            match = None
            matches = orpheus_client.node_name2records(name)
            if len(matches) == 1:
                outer.node_record = matches[0]
                return 'name'
            elif len(matches) > 1:
                for m in matches:
                    if m['name'].lower() == name.lower():
                        match = m
            if match and (match['type'] == outer.type):
                outer.node_record = match
                return 'name'
            return None

        match_type = None
        if self.issn:
            logger.debug('Attempting mach by issn ({})'.format(self.issn))
            match_type = issn_match(self, self.issn)
        if not self.node_record:
            if self.eissn:
                logger.debug('Attempting mach by e-issn ({})'.format(self.eissn))
                match_type = issn_match(self, self.eissn)
            if not self.node_record:
                if self.name:
                    logger.debug('Attempting mach by name ({})'.format(self.name))
                    raw_query_name = self.name
                    if self.publisher: # try a search with publisher for unambiguous match
                        query_name = '{} ({})'.format(raw_query_name, self.publisher)
                        match_type = name_match(self, query_name)
                    if not self.node_record: # try a search with "name + (type)" for unambiguous match
                        match_type = name_match(self, raw_query_name + ' ({})'.format(self.type.capitalize()))
                        if not self.node_record:
                            query_name = raw_query_name
                            match_type = name_match(self, query_name)
                        # if not self.node_record and (self.type == 'PUBLISHER'):
                        #     match_type = name_match(self, query_name + PUBLISHER_DISAMBIGUATION_STRING)
        if self.node_record:
            logger.debug('Match by {} found to Orpheus node id {}: {}'.format(match_type, self.node_record['id'], self.node_record['name']))
            self.node_id = self.node_record['id']
        else:
            logger.debug('Match not found')

        return [self.node_id, self.node_record, match_type]

    def create_node(self, force_creation=False):
        '''
        Creates a new node in Orpheus
        :param force_creation: if True, a new node will be created in Orpheus even if a node matching this
                self.name already exists. The new node will be generated with a random integer in square brackets
                after the name
        :return: Orpheus node id and record of newly created node
        '''

        if self.name.lower() == self.publisher.lower(): # Journal name matches publisher name
            logger.warning(
                'Node name ({}) identical to its publisher name ({}). Appending "(Publisher)" to publisher name'.format(
                                                                            self.name, self.publisher))
            self.publisher += PUBLISHER_DISAMBIGUATION_STRING

        if self.publisher and not self.publisher_node_id:
            logger.debug('Orpheus node id for publisher "{}" unknown. Attempting match to Orpheus node'.format(
                                                                                                        self.publisher))
            p_parser = NodeParser(name=self.publisher, source=self.source, type='PUBLISHER')
            # self.publisher_node_id, _ = p_parser.match_or_create_node(match_to_preferred=True) # replaced by lines below
            p_node_id, p_node_record, p_match_type = p_parser.match2node()
            self.publisher_node_id, self.publisher_node_record = act_on_orpheus_match(p_parser, p_node_id,
                                                                                         p_node_record, p_match_type)

            if (self.publisher_node_record['name_status'] not in ['PRIMARY']):
                logger.debug('Publisher match is a synonym; using preferred Orpheus node {} instead'.format(
                                                                            self.publisher_node_record['synonym_of']))
                self.publisher_node_id = self.publisher_node_record['synonym_of']
                self.publisher_node_record = orpheus_client.get_node4node_id(self.publisher_node_id)


        # check if exact name already exists; if so, determine if this is a homonym; if so, append publisher's name
        m_record = orpheus_client.node_name2record(self.name)
        if m_record:
            # m_issn = [m_record['issn'], m_record['eissn']]
            # if (self.issn and (self.issn not in m_issn)) or (self.eissn and (self.eissn not in m_issn)):
            if self.publisher:
                logger.debug('Homonym exists in Orpheus. Appending publisher name')
                self.name += ' ({})'.format(self.publisher)
            else:
                logger.warning('Homonym exists in Orpheus but publisher name of new node unknown')

        logger.debug('Calling orpheus_client.create_node for: {}; {}; {}; {}; {}'.format(self.name, self.name_status,
                                                                                         self.type, self.issn, self.eissn))
        r = orpheus_client.create_node(self.name, self.name_status, self.type, self.source,
                                       **{'issn': self.issn, 'eissn': self.eissn, 'url': self.url,
                                          'parent': self.publisher_node_id, 'romeo_id': self.romeo_id,
                                          'synonym_of': self.synonym_of})
        new_node_record = None
        new_node_id = None
        try:
            r_msg = r.json()['name'][0]
        except json.decoder.JSONDecodeError:
            r_msg = None
        except:
            logger.critical("r.text: {}".format(r.text))
            sys.exit(r.text)

        if r.ok and (r.json()['name'][0] != "node with this name already exists."):
            logger.debug(r.json())
            # print("r.json():", r.json())
            logger.info('Created new {} Orpheus node for {} {}'.format(self.name_status, self.type, self.name))
            new_node_record = r.json()
            new_node_id = new_node_record['id']
            logger.debug('new_node_id: {}'.format(new_node_id))
            if self.name_status == 'PRIMARY':
                self.node_record = new_node_record
                self.node_id = new_node_id
                logger.debug('self.node_id: {}'.format(self.node_id))
        elif force_creation:
            if r_msg and (r.json()['name'][0] == "node with this name already exists."):
                logger.debug(r.json())
            elif 'duplicate key value violates unique constraint "node_name_index"' in r.text:
                logger.debug(r.text)
            self.name = '{} [{}]'.format(self.name, random.randint(1000, 9998))
            # self.node_id, self.node_record = self.create_node(force_creation=True)
            new_node_id, new_node_record = self.create_node(force_creation=True)
        else:
            # print("r.json()['name'][0]:", r.json()['name'][0])
            logger.error('Failed to create node: {}'.format(r.text))
        # print("new_node_id, new_node_record:", new_node_id, new_node_record)

        # check if we should also create an unaccented representation of name as a synonym
        try:
            self.name.encode('ascii')
        except UnicodeEncodeError:
            ascii_name = unidecode(self.name)
            logger.debug('The node I just created ({}) contained non-ascii characters. Lets create a ascii '
                         'representation ({}) as a synonym'.format(self.name, ascii_name))
            if self.synonym_of:
                u_syn_of = self.synonym_of
            else:
                u_syn_of = new_node_id
            u_parser = NodeParser(ascii_name, name_status='SYNONYM', issn=self.issn, eissn=self.eissn,
                                  publisher=self.publisher, romeo_id=self.romeo_id, synonym_of=u_syn_of,
                                  source=self.source, type=self.type, url=self.url)
            logger.debug('Ascii representation is synonym of Orpheus node {}'.format(u_syn_of))
            u_id, u_record, match_type = u_parser.match2node()
            u_id, u_record = act_on_orpheus_match(u_parser, u_id, u_record, match_type)

        return new_node_id, new_node_record

    def match_or_create_node(self, match_to_preferred=False, restrict_type=True, force_creation=False):
        '''
        WARNING: THIS FUNCTION SHOULD PROBABLY NO LONGER BE USED. LEAVING IT HERE FOR NOW JUST IN CASE. USE
            NodeParser.match2node() followed by generic_parser.act_on_orpheus_match() INSTEAD

        :param match_to_preferred: if True, if match is a SYNONYM, return node of preferred name instead
        :param restrict_type: if True, only matches of expected node type are considered as matches. That is,
                if self is a PUBLISHER, than only PUBLISHER nodes will be considered as matches
        :param force_creation: if True, a new node will be created in Orpheus even if a node matching this
                self.name already exists. The new node will be generated with a random integer in square brackets
                after the name
        :return: Orpheus node id of matched or newly created node
        '''
        orpheus_id, orpheus_record, match_type = self.match2node()
        logger.debug('orpheus_id: {}'.format(orpheus_id))
        logger.debug('orpheus_record: {}'.format(orpheus_record))
        if orpheus_id and restrict_type and (orpheus_record['type'] != self.type):
            logger.debug('Matched {} to {}, so considering it a false match'.format(self.type, orpheus_record['type']))
            orpheus_id, orpheus_record, match_type = None, None, None
        if orpheus_id and not force_creation:
            logger.debug('Matched {} {} to Orpheus node {}'.format(self.type, self.name, orpheus_id))
            if (orpheus_record['name_status'] not in ['PRIMARY']) and match_to_preferred:
                logger.debug('Match is a synonym; returning preferred Orpheus node {} instead'.format(
                                                                                        orpheus_record['synonym_of']))
                self.node_id = orpheus_record['synonym_of']
                self.node_record = orpheus_client.get_node4node_id(self.node_id)
            else:
                logger.debug('Returning {} Orpheus node {} as match'.format(orpheus_record['name_status'], orpheus_id))
                self.node_id = orpheus_id
                self.node_record = orpheus_record
        else:
            logger.debug('Orpheus match not found for {}; creating new node'.format(self.name))
            self.node_id, self.node_record = self.create_node(force_creation=force_creation)
        return self.node_id, self.node_record

    def match_publisher2node(self):
        if self.publisher:
            self.publisher_node_record = orpheus_client.node_name2record(self.publisher)
            if self.publisher_node_record:
                self.publisher_node_id = self.publisher_node_record['id']
            return (self.publisher_node_id, self.publisher_node_record)
        else:
            sys.exit('match_publisher2node requires instance of parser to contain publisher name')

    def publisher_equal_check(self):
        '''
        Function to check that the publisher set in Orpheus for node
        corresponds to the value of publisher passed on to the parser.

        NOT CURRENTLY USED ANYWHERE; PROBABLY NOT USEFUL

        :return:
        '''
        if self.node_record and self.publisher_node_record:
            node_publisher_id = self.node_record['parent']
            publisher_node_id = self.publisher_node_record['id']
            if node_publisher_id == publisher_node_id:
                return True
            else:
                return False
        else:
            return None

    def server_data_match_node(self, force_update=False, **kwargs):
        '''
        A function to check, for each field of kwarg, existing data in matching Orpheus node.
        If data does not exist yet on the server side, it is added to the node record.
        If journal/publisher name does not match, a synonym is added to Orpheus.
        If issn/eissn fields do not match, an error is issued because this reveals a problem in
        the node match.
        If other fields do not match, server data is maintained, unless force_update is set to True.

        PROBLEM: There is quite a bit of overlap between this function and act_on_orpheus_match()

        :return a dictionary containing a boolean 'synonym_created' and a dictionary 'updated_data' listing
            all data that was updated
        '''

        response = {
            'synonym_created': False,
            'updated_data': {}
        }

        data_to_update = {}
        for key, client_data in kwargs.items():
            server_data = self.node_record[key]
            if client_data:
                if not server_data:
                    data_to_update.update({key: client_data})
                else:
                    if server_data != client_data:
                        if key in ['issn', 'eissn']:
                            sys.exit(
                                'ERROR: value of {} in Orpheus ({}) does not match value in external dataset ({}) for journal {}.'.format(
                                    key, server_data, client_data, kwargs['name']))
                        elif key in ['name']:  # add a new synonym
                            dict = {'synonym_of': self.node_record['id']}
                            dict.update(**kwargs)
                            r = orpheus_client.create_node(client_data, 'SYNONYM', self.type, self.source, **dict)
                            if not r.ok:
                                sys.exit('ERROR trying to create node for {}:\n{}'.format(client_data, r.text))
                            else:
                                response['synonym_created'] = True
                        else:
                            if force_update == True:
                                data_to_update.update({key: client_data})
                            else:
                                logger.warning(
                                    'value of {} in Orpheus ({}) does not match value in external dataset ({}). '
                                    'External value was ignored. Rerun with force_update=True if you want this external '
                                    'data to override the value in Orpheus'.format(
                                        key, server_data, client_data))
        if data_to_update:
            r = orpheus_client.update_node(self.node_record['id'], **data_to_update)
            if not r.ok:
                sys.exit('ERROR trying to update node {}:\n{}'.format(self.node_record['id'], r.text))
            else:
                response['updated_data'].update(data_to_update)
        return response
    # endregion

    class PolicyMatcher:
        '''
        A generic class to check if the policy represented by kwargs already exists in Orpheus.
        If it does not, a new policy should be created.
        If it already exists, it should be updated.

        :param link_to_preferred_name: if True (default), attach policy to preferred name
        :param policy_type: string indicating the type of policy that will be dealt with. Options are: 'oa_status',
            'green', 'gold'
        :return a dictionary containing a boolean 'new_policy_created' and a dictionary 'updated_data' listing
            all data that was updated
        '''
        def __init__(self, outer, policy_type=None):
            self.outer = outer
            self.policy_type = policy_type

        def match(self, link_to_preferred_name=True, force_update=False, **kwargs):
            response = {
                'new_policy_created': False,
                'updated_data': {}
            }

            logger.debug('link_to_preferred_name: {}'.format(link_to_preferred_name))
            logger.debug('self.outer.name_status: {}'.format(self.outer.name_status))
            if link_to_preferred_name:
                if self.outer.node_record['name_status'] not in ['PRIMARY']:
                    if not self.outer.node_record['synonym_of']:
                        sys.exit('{} is not a preferred name but "synonym of" field '
                                 'is not set'.format(self.outer.node_record['name']))
                    target_node = self.outer.node_record['synonym_of']
                    logger.debug('NodeParser instance is not a preferred name. '
                                 'Setting target node to preferred name instead.')
                else:
                    logger.debug('NodeParser instance is a preferred name. Setting target node to its node_id.')
                    target_node = self.outer.node_record['id']
                # if self.outer.name_status not in ['PRIMARY']:
                #     if not self.outer.synonym_of:
                #         sys.exit('{} is not a preferred name but "synonym of" field is not set'.format(self.outer.name))
                #     target_node = self.outer.synonym_of
                #     logger.debug('NodeParser instance is not a preferred name. '
                #                  'Setting target node to preferred name instead.')
                # else:
                #     logger.debug('NodeParser instance is a preferred name. Setting target node to its node_id.')
                #     target_node = self.outer.node_id
            else:
                target_node = self.outer.node_record['id']
                # target_node = self.outer.node_id
            logger.debug('target_node: {}'.format(target_node))
            # if 'node' in kwargs.keys():
            #     kwargs['node'] = target_node

            if self.policy_type == 'oa_status':
                get_function = orpheus_client.get_oastatus4node_id
                create_function = orpheus_client.create_oastatus
                update_function = orpheus_client.update_oastatus
            elif self.policy_type == 'green':
                get_function = orpheus_client.get_green_policies4node_id
                create_function = orpheus_client.create_green_policy
                update_function = orpheus_client.update_green_policy
            elif self.policy_type == 'gold':
                get_function = orpheus_client.get_gold_policies4node_id
                create_function = orpheus_client.create_gold_policy
                update_function = orpheus_client.update_gold_policy
            else:
                sys.exit('ERROR: {} is not a recognised policy_type'.format(self.policy_type))
            server_policies = get_function(target_node)
            matching_server_policy = None
            if server_policies.ok:
                for policy in server_policies.json()['results']:
                    # logger.debug('policy: {}'.format(policy))
                    if self.policy_type in ['oa_status', 'gold']:
                        if policy['source'] == self.outer.source:
                            matching_server_policy = policy
                    elif self.policy_type == 'green':
                        # logger.debug('kwargs: {}'.format(kwargs))
                        if (policy['source'] == kwargs['source']) \
                                and (sorted(policy['version']) == sorted(kwargs['version'])) \
                                and (sorted(policy['outlet']) == sorted(kwargs['outlet'])):
                            matching_server_policy = policy
            logger.debug('matching_server_policy: {}'.format(matching_server_policy))

            if not matching_server_policy:
                logger.debug('Calling create_function of orpheus_client')
                if self.policy_type == 'oa_status':
                    resp = create_function(target_node, self.outer.oa_status, self.outer.source, **kwargs)
                elif self.policy_type == 'green':
                    resp = create_function(target_node, kwargs['outlet'], kwargs['version'],
                                                              **kwargs)
                elif self.policy_type == 'gold':
                    resp = create_function(target_node, **kwargs)
                logger.debug('resp.text: {}'.format(resp.text))
                response['new_policy_created'] = True
            else:
                data_to_update = {}
                for key, client_data in kwargs.items():
                    server_data = matching_server_policy[key]
                    if client_data:
                        if not server_data:
                            data_to_update.update({key: client_data})
                        else:
                            if key in ['apc_value_min', 'apc_value_max']:
                                server_data = float(server_data)
                                client_data = float(client_data)
                            if key in ['outlet']:
                                server_data.sort()
                                client_data.sort()
                            if key in ['version_embargo_months']:
                                server_data = str(server_data)
                                client_data = str(client_data)
                            if server_data != client_data:
                                if force_update == True:
                                    data_to_update.update({key: client_data})
                                else:
                                    logger.warning(
                                        'value of {} in Orpheus ({} [{}]) does not match value in external dataset ({} [{}]). '
                                        'External value was ignored. Rerun with force_update=True if you want this '
                                        'external data to override the value in Orpheus'.format(
                                            key, server_data, type(server_data), client_data, type(client_data)))
                if data_to_update:
                    r = update_function(matching_server_policy['id'], **data_to_update)
                    if not r.ok:
                        sys.exit(
                            'ERROR trying to update OA status {}:\n{}'.format(matching_server_policy['id'], r.text))
                    else:
                        response['updated_data'].update(data_to_update)
            logger.debug('response: {}'.format(response))
            return response

