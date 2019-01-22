'''
This connector parses Elsevier APC information from https://www.elsevier.com/__data/promis_misc/j.custom97.pdf
retrieved 11/07/2018 (PDF indicates prices were last revised on 07/07/2018).

Tabula (https://tabula.technology) was used to extract the CSV file parsed by this script from the original PDF
'''

import csv
import logging
import logging.config
import os
import string
import sys
import generic_parser
import orpheus_client

from orpheus_constants import CCBY_ID, CCBYNCND_ID, CUSTOM_ID

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

TEST_MODE = False
if TEST_MODE:
    logger.warning('Running in test mode!')

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    source_parser = generic_parser.SourceParser('Elsevier Open Access Price List',
                                                url='https://www.elsevier.com/__data/promis_misc/j.custom97.pdf')
    ELSEVIER_SOURCE_ID = source_parser.match_or_create_source()
    elsevier_website_parser = generic_parser.SourceParser('Elsevier website: Open access licenses',
                                                          url='https://www.elsevier.com/about/policies/open-access-licenses')
    ELSEVIER_WEBSITE_ID = elsevier_website_parser.match_or_create_source()

    p_parser = generic_parser.NodeParser(name='Elsevier', type='PUBLISHER', source=ELSEVIER_WEBSITE_ID)
    p_node_id, p_node_record, p_match_type = p_parser.match2node()
    p_parser.node_id, p_parser.node_record = generic_parser.act_on_orpheus_match(p_parser, p_node_id, p_node_record,
                                                                                 p_match_type)

    # gold policy
    gp = generic_parser.GoldPolicyInstance()
    gp.licence_options = [CCBY_ID, CCBYNCND_ID, CUSTOM_ID]

    inputfile = os.path.join(BASE_DIR, 'datasets', 'tabula-j.custom97.csv')

    with open(inputfile, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        row_counter = 0
        for row in reader:
            row_counter += 1
            issn = row['ISSN'].strip()
            jname = row['Journal title'].replace('\n', ' ').replace('  ', ' ').strip()
            oastatus = row['OA model'].strip()
            currency = row['Currency'].strip()
            price = row['Price'].strip()

            logger.info('-------({}) Working on {}; oastatus: {}; '
                         'issn: {}; price: {} {}'.format(row_counter, jname, oastatus, issn, currency, price))
            j_parser = generic_parser.NodeParser(name=jname, publisher='Elsevier', source=ELSEVIER_SOURCE_ID,
                                                 publisher_node_id=p_parser.node_id)
            j_parser.issn = issn
            j_parser.oa_status = oastatus.replace('Open Access', 'FULLY_OA').upper()

            # # identify romeo_publisher and its node in Orpheus
            # j_parser.match2romeo_publisher(test_mode=TEST_MODE)

            # Attempt to find a match in Orpheus
            node_id, node_record, match_type = j_parser.match2node()
            j_parser.node_id, j_parser.node_record = generic_parser.act_on_orpheus_match(j_parser, node_id,
                                                                                         node_record, match_type)
            logger.debug('j_parser.node_record: {}'.format(j_parser.node_record))
            #determine Orpheus id of preferred name
            if j_parser.node_record['name_status'] not in ['PRIMARY']:
                preferred_node_id = j_parser.node_record['synonym_of']
            else:
                preferred_node_id = j_parser.node_id

            logger.debug('preferred_node_id: {}'.format(preferred_node_id))
            logger.debug('j_parser: {}'.format(vars(j_parser)))

            # parsing gold policy
            gp.node = preferred_node_id
            gp.apc_currency = currency
            gp.apc_value_min = price
            gp.apc_value_max = price
            gp.source = ELSEVIER_SOURCE_ID

            # Attach policies to preferred name node
            logger.debug('Calling j_parser.PolicyMatcher(j_parser, policy_type=oa_status).match()')
            j_parser.PolicyMatcher(j_parser, policy_type='oa_status').match()
            logger.debug('Calling j_parser.PolicyMatcher(j_parser, policy_type=gold).match()')
            j_parser.PolicyMatcher(j_parser, policy_type='gold').match(**gp.as_dict())

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf', defaults={'logfilename':'elsevier_apc_parser.log'})
    logger = logging.getLogger('elsevier_apc_parser')
    main()