'''
This connector parses Srpinger Compact information from
https://resource-cms.springernature.com/springer-cms/rest/v1/content/829308/data/v3
retrieved 10/02/2019 (PDF reads "Status July 2018").

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
    source_parser = generic_parser.SourceParser('Springer Journals List 2019',
                                                url='https://resource-cms.springernature.com/springer-cms/rest/v1/content/829308/data/v3')
    SOURCE_ID = source_parser.match_or_create_source()

    p_parser = generic_parser.NodeParser(name='Springer', type='PUBLISHER')
    p_node_id, p_node_record, p_match_type = p_parser.match2node()
    p_parser.node_id, p_parser.node_record = generic_parser.act_on_orpheus_match(p_parser, p_node_id, p_node_record,
                                                                                 p_match_type)

    inputfile = os.path.join(BASE_DIR, 'datasets', 'tabula-Eligible Open Choice Journals CCBY.csv')

    with open(inputfile, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        row_counter = 0
        for row in reader:
            row_counter += 1
            issn = row['ISSN print'].strip()
            eissn = row['ISSN electronic'].strip()
            jname = row['Title'].replace('\n', ' ').replace('  ', ' ').strip()
            oastatus = row['Open Access'].strip()

            logger.info('-------({}) Working on {}; oastatus: {}; '
                         'issn: {}; eissn: {}'.format(row_counter, jname, oastatus, issn, eissn))
            j_parser = generic_parser.NodeParser(name=jname, issn=issn, eissn=eissn, publisher='Springer',
                                                 source=SOURCE_ID, publisher_node_id=p_parser.node_id)
            j_parser.oa_status = oastatus.replace('Fully Open Access',
                                                  'FULLY_OA').replace('Hybrid (Open Choice)',
                                                                      'HYBRID').upper()

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

            # Attach policies to preferred name node
            logger.debug('Calling j_parser.PolicyMatcher(j_parser, policy_type=oa_status).match()')
            j_parser.PolicyMatcher(j_parser, policy_type='oa_status').match()
            logger.debug('Calling j_parser.PolicyMatcher(j_parser, policy_type=deal).match()')
            j_parser.PolicyMatcher(j_parser, policy_type='deal').match(supersede_existing=False,
                                                                       **{'applies_to': 'INSTITUTIONS',
                                                                          'type': 'SPRINGER COMPACT'})

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf', defaults={'logfilename':'springer_compact_parser.log'})
    logger = logging.getLogger('springer_compact_parser')
    main()