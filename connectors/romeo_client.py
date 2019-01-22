# CLIENT FOR SHERPA/ROMEO API

# not ready yet

import urllib.request
from pprint import pprint
import xml.etree.ElementTree as ET
import re
import sys
import logging
import math

try:
    from keys_local import KEY
except ImportError:
    sys.exit('keys_local.py file could not be found')

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

ROMEO_URL = 'http://www.sherpa.ac.uk/romeo/api29.php'
ROMEO_IDS_TO_EXCLUDE = [] # policies matching these IDs must be excluded from parsing because they contain errors at the source. They will need to be added to Orpheus manually.

# A list of restrictions that translate to disallowed deposit
DISALLOWED_STRINGS = [
                            "Author must complete and submit publisher's Fair Use form".upper(),
                            'Authors must contact publisher for permission'.upper(),
                            'Author must seek permission from publisher'.upper(),
                            'Author or institution must ask editor for permission'.upper(),
                            'Contact publisher for permission to archive pre-prints'.upper(),
                            'Must be removed upon publication'.upper(),
                            'Must be removed while under peer-review'.upper(),
                            'Must obtain written permission from Editor'.upper(),
                            'Permission from publisher must be obtained'.upper(),
                            'Permission must be obtained from publisher'.upper(),
                            'Permission must be obtained from publisher or author, depending on who owns copyright'.upper(),
                            'Permission must be obtained from the publisher'.upper(),
                            'Permission must be sought to post in institutional repositories'.upper(),
                            'Permission to deposit articles must be sought from the publisher'.upper(),
                            'Permission to deposit articles must be sought from the publisher, if required by funding agency'.upper(),
                            'Permission to post articles must be sought from the publisher'.upper(),
                            'Permission to reuse articles must be sought from the publisher'.upper(),
                            'Permission to reuse articles must be sought from the publisher directly'.upper(),
                            'Permission to reuse articles must be sought from the publisher, but will not be unreasonably refused'.upper(),
                            'Post-print must be removed upon publication'.upper(),
                            'Prior to publication only (once in print, must be removed)'.upper(),
                            'Written permission from the copyright owner'.upper(),
                            'Written permission must be obtained from the publisher'.upper(),
                            'Written permission required'.upper(),
]


string2embargo = {
    '6 months after online publication': 6,
    '9 months': 9,
    '<num>6</num> <period units="">months</period> embargo': 6,
    'After publication of article': 0,
    'Authors post-print after media embargo has expired': 0,
    '''Publisher's version/PDF may be used after <num>12</num> <period units="month">months</period> embargo''': 12,
}

embargo_regex = re.compile('^<num>(?P<embargo_int>\d{1,2})</num> <period units="(?P<time_unit>(day|week|weeks|month|year))">(?P=time_unit)s?</period>')

class parser:

    def __init__(self, query='', offline_dataset=None, save_dataset=None):
        '''
        :param query: RoMEO API query
        :param offline_dataset: use offline_dataset file instead of querying the RoMEO API
        :param save_dataset: save RoMEO API response to save_dataset file
        '''
        self.output_dict = {}
        if not offline_dataset:
            q = query + '&ak={}'.format(KEY)
            print(ROMEO_URL + q)
            response = urllib.request.urlopen(ROMEO_URL + q)
            romeo_data = response.read().decode('ISO-8859-1')
            if save_dataset:
                with open(save_dataset, 'w') as f:
                    f.write(romeo_data)
            self.r = ET.fromstring(romeo_data)
        else:
            with open(offline_dataset) as f:
                self.r = ET.fromstring(f.read())

    def parse_response(self):

        self.output_dict['apicontrol'] = self.r.find('header').find('apicontrol').text
        self.output_dict['outcome'] = self.r.find('header').find('outcome').text
        self.output_dict['romeo_issn_list'] = []
        self.output_dict['romeo_id_list'] = []
        self.output_dict['romeo_publisher_list'] = []
        self.output_dict['journals_dicts'] = []

        for j in self.r.iter('journal'):
            jtitle = j.find('jtitle').text
            romeo_issn = j.find('issn').text
            zetocpub = j.find('zetocpub').text
            romeopub = j.find('romeopub').text
            j_dict = {
                'name':jtitle,
                'issn':romeo_issn,
                'zetocpub':zetocpub,
                'romeopub':romeopub
            }
            self.output_dict['romeo_issn_list'].append(romeo_issn)
            if zetocpub and (zetocpub not in self.output_dict['romeo_publisher_list']):
                self.output_dict['romeo_publisher_list'].append(zetocpub)
            if romeopub and (romeopub not in self.output_dict['romeo_publisher_list']):
                self.output_dict['romeo_publisher_list'].append(romeopub)
            self.output_dict['journals_dicts'].append(j_dict)

        for p in self.r.iter('publisher'):
            p_dict = {}
            id = p.attrib
            p_dict['romeo_id'] = id['id']
            try:
                p_dict['romeo_parentid'] = id['parentid']
            except KeyError:
                p_dict['romeo_parentid'] = None
            for a in ['name', 'alias', 'homeurl', 'romeocolour', 'dateadded', 'dateupdated']:
                p_dict[a] = p.find(a).text
            for a in ['prearchiving', 'postarchiving', 'pdfarchiving', 'paidaccessurl', 'paidaccessname', 'paidaccessnotes']:
                counter = 0
                for b in p.iter(a):
                    counter += 1
                    p_dict[a] = b.text
                if counter > 1:
                    logging.warning('Found more than 1 value for "{}" in record with romeo id {}.'.format(a, id['id']))
            for a in ['prerestriction', 'postrestriction', 'pdfrestriction', 'condition']:
                values = []
                for b in p.iter(a):
                    values.append(b.text)
                p_dict[a] = values
            for a in ['copyrightlink']:
                values = []
                for b in p.iter(a):
                    copyright_dict = {}
                    for c in ['copyrightlinktext', 'copyrightlinkurl']:
                        copyright_dict[c] = b.find(c).text
                    values.append(copyright_dict)
                p_dict[a] = values
            self.output_dict[p_dict['romeo_id']] = p_dict
            self.output_dict['romeo_id_list'].append(p_dict['romeo_id'])

    def convert_restrictions(self):

        for k, v in self.output_dict.items():
            logger.debug('Key: {}; Value: {}'.format(k,v))
            if k in ROMEO_IDS_TO_EXCLUDE:
                logging.warning('Cannot parse romeo publisher id {}. Please add it manually to Orpheus.')
            elif k in ['apicontrol', 'outcome', 'romeo_id_list', 'romeo_issn_list',
                       'romeo_publisher_list', 'journals_dicts']:
                pass # apicontrol and outcome are for quality control only (API query might have failed, for example)
            else:
                # try: # dev
                for a in ['prerestriction', 'postrestriction', 'pdfrestriction']:
                    logger.debug('a: {}'.format(a))
                    list = v[a]
                    converted_list = []
                    for restriction in list:
                        embargo_match = embargo_regex.match(restriction)
                        if embargo_match:
                            time_unit = embargo_match.group('time_unit')
                            if time_unit == 'year':
                                multiplier = 12
                            elif time_unit == 'month':
                                multiplier = 1
                            elif time_unit == 'day':
                                multiplier = 0.03333333333
                            elif time_unit in ['week', 'weeks']:
                                multiplier = 0.230137
                            else:
                                logging.error(
                                    'Could not extract time unit from restriction {}'.format(
                                        restriction))
                            time_integer = int(embargo_match.group('embargo_int'))
                            embargo_months = math.ceil(multiplier * time_integer)
                            converted_list.append((str(embargo_months), restriction))
                        elif restriction in string2embargo.keys():
                            converted_list.append((str(string2embargo[restriction]), restriction))
                        elif restriction.upper().strip() in DISALLOWED_STRINGS:
                            converted_list.append(('DISALLOWED', restriction))
                        else:
                            converted_list.append(('UNCLEAR', restriction))
                    self.output_dict[k].update({a: converted_list})

        # '''
        # Finally, look for embargo information in the non-structured <conditions> tree
        # returned by the RoMEO API
        # '''
        # num_t = re.compile('[0-9]+')
        # for a in r.iter('condition'):
        #     fv = a.text.strip().lower()
        #     num_m = num_t.findall(fv)
        #     if num_m:
        #         # sort num_m in descending order to guarantee we pick largest embargo period if more than one is available
        #         num_m.sort(reverse=True, key=int)
        #         embargo = num_m[0]
        #
        #         versions = []
        #         if "Publisher's version/PDF".lower() in fv:
        #             versions.append('VoR')
        #         if ('post-print' in fv) or ('authors accepted version' in fv):
        #             versions.append('AAM')
        #
        #         outlets = []
        #         if 'personal website' in fv:
        #             outlets.append('website')
        #         if ('institutional repository' in fv) or ('open access repository' in fv) or \
        #                 ('non-commercial repository' in fv):
        #             outlets.append('apollo')

#
#
#
# def parse_restrictions(xml_tree, romeo_field, num_t=re.compile('<num>[0-9]+</num>')):
#     embargo_list = []
#     for a in xml_tree.iter(romeo_field):
#         field_value = a.text.strip()
#         if ('embargo' in field_value.lower()) and ('month' in field_value.lower()):
#             num_m = num_t.search(field_value)
#             if num_m:
#                 embargo_list.append(num_m.group())
#     return(embargo_list)
#
# def parse_conditions(xml_tree, num_t=re.compile('<num>[0-9]</num>')):
#     embargo_list = []
#

class journal_info:

    def __init__(self, name='', issn=''):
        '''
        Initiate the class by using one of the input parameters to query the RoMEO API
        :param name: Journal/Publisher name
        :param issn: Journal issn
        '''
        if issn:
            self.issn = issn
            self.query = '?issn=' + issn
        elif name:
            self.name = name
            self.query = '?jtitle=' + name.replace(' ', '%20')
        else:
            sys.exit('romeo_client.journal_info requires a name and/or issn parameter')

        response = urllib.request.urlopen(ROMEO_URL + self.query)
        romeo_data = response.read().decode('ISO-8859-1')
        self.r = ET.fromstring(romeo_data)

        self.output_dict = {}