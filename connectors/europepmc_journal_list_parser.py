'''
This connector parses Europe PMC information from
https://europepmc.org/journalList?format=csv
retrieved 12/02/2019
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

PROMPT_RESPONSES = {
    'Evolutionary Applications': '3',
    'Health Psychology Research': '3',
    'Iranian Journal of Neurology': '3', # results in WARNING - At least one of the ISSN fields of Orpheus record 121398 (issn: 2322-2565; eissn: None) was overwritten by new values (issn: 2008-384X; eissn: 2252-0058); this is fine; ISSNs in new dataset are correct
    'Iranian Red Crescent Medical Journal': '3', # manually edit existing publisher node to "Kowsar" ; WARNING - At least one of the ISSN fields of Orpheus record 106844 (issn: 1561-4395; eissn: None) was overwritten by new values (issn: 2074-1804; eissn: 2074-1812) [this is fine; ISSNs are correct]
    'Open Medicine': '1',
}

def main():

    epmc_embargo2months = {
        "": None,
        "Immediate": 0,
        "0 months or more": 0,
        "1 month": 1,
        "2 months": 2,
        "2 months or less": 2,
        "3 months": 3,
        "3 months or more": 3,
        "6 months": 6,
        "6 months or less": 6,
        "12 months": 12,
        "12 months or less": 12,
        "24 months": 24,
        "24 months or less": 24,
        "36 months": 36,
        "36 months or less": 36,
    }

    participation_level2orpheus = {
        " Full ": "FULL",
        " NIH Portfolio ": "NIH"
    }

    open_licence2orpheus = {
        "All": "ALL",
        "No": "NO",
        "Some": "SOME"
    }

    deposit_status2orpheus = {
        " ": None,
        " No New Content ": "NO_NEW",
        " Now Select ": "NOW_SELECT",
        " Predecessor ": "PRE"
    }


    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    source_parser = generic_parser.SourceParser('PMC Journal List',
                                                url='https://europepmc.org/journalList')
    SOURCE_ID = source_parser.match_or_create_source()

    inputfile = os.path.join(BASE_DIR, 'datasets', 'jlist.csv')

    with open(inputfile, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        row_counter = 0
        for row in reader:
            row_counter += 1
            # if row_counter < 1439: # Don't forget to remove this after testing
            #     continue
            issn = row['pISSN'].strip()
            eissn = row['eISSN'].strip()
            jname = row['Journal title'].replace('\n', ' ').replace('  ', ' ').strip()
            jsynonym = row['NLM TA'].replace('\n', ' ').replace('  ', ' ').strip()
            jpublisher = row['Publisher'].replace('\n', ' ').replace('  ', ' ').strip()
            embargo = row['Free access']
            open_licence = row['Open access']
            participation_level = row['Participation level']
            deposit_status = row[' Deposit status']
            epmc_url = row[' Journal URL']

            logger.info('-------({}) Working on {}; '
                         'issn: {}; eissn: {}'.format(row_counter, jname, issn, eissn))

            if deposit_status == " Predecessor ":
                logger.info('Skipped {} (title no longer in publication)'.format(jname))
                continue

            logger.info('--- Parsing publisher info')
            p_parser = generic_parser.NodeParser(name=jpublisher, type='PUBLISHER')
            p_node_id, p_node_record, p_match_type = p_parser.match2node()
            p_parser.node_id, p_parser.node_record = generic_parser.act_on_orpheus_match(p_parser, p_node_id,
                                                                                         p_node_record, p_match_type)
            if p_parser.node_record['name_status'] not in ['PRIMARY']:
                p_preferred_node_id = p_parser.node_record['synonym_of']
            else:
                p_preferred_node_id = p_parser.node_id

            logger.info('--- Parsing journal info')
            j_parser = generic_parser.NodeParser(name=jname, issn=issn, eissn=eissn, publisher=jpublisher,
                                                 source=SOURCE_ID, publisher_node_id=p_preferred_node_id, epmc_url=epmc_url)
            # Attempt to find a match in Orpheus
            node_id, node_record, match_type = j_parser.match2node()

            j_parser.node_id, j_parser.node_record = generic_parser.act_on_orpheus_match(j_parser, node_id,
                                                                                     node_record, match_type,
                                                                                     prompt_responses=PROMPT_RESPONSES)
            logger.debug('j_parser.node_record: {}'.format(j_parser.node_record))
            #determine Orpheus id of preferred name
            if j_parser.node_record['name_status'] not in ['PRIMARY']:
                preferred_node_id = j_parser.node_record['synonym_of']
            else:
                preferred_node_id = j_parser.node_id

            # Parsing abbreviation as a synonym
            if jsynonym:
                logger.debug('--- Processing alternative title "{}"'.format(jsynonym))
                syn_parser = generic_parser.NodeParser(name=jsynonym, issn=issn, eissn=eissn,
                                                       publisher=j_parser.publisher,
                                                       publisher_node_record=j_parser.publisher_node_record,
                                                       publisher_node_id=j_parser.publisher_node_id,
                                                       source=SOURCE_ID)
                syn_parser.name_status = 'SYNONYM'
                syn_parser.synonym_of = preferred_node_id
                syn_id, syn_record, match_type = syn_parser.match2node()
                generic_parser.act_on_orpheus_match(syn_parser, syn_id, syn_record, match_type)

            logger.debug('preferred_node_id: {}'.format(preferred_node_id))
            logger.debug('j_parser: {}'.format(vars(j_parser)))

            # Attach policies to preferred name node
            logger.debug('--- Calling j_parser.PolicyMatcher(j_parser, policy_type=epmc).match()')
            j_parser.PolicyMatcher(j_parser, policy_type='epmc').match(supersede_existing=False,
                                                                       **{'participation_level': participation_level2orpheus[participation_level],
                                                                          'embargo_months': epmc_embargo2months[embargo],
                                                                          'open_licence': open_licence2orpheus[open_licence],
                                                                          'deposit_status': deposit_status2orpheus[deposit_status],
                                                                          })

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf', defaults={'logfilename':'europepmc_journal_list_parser.log'})
    logger = logging.getLogger('europepmc_journal_list_parser')
    main()