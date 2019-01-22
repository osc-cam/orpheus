'''
This connector parses journal info from files in the clarivate_analytics dataset folder,
downloaded from http://mjl.clarivate.com/#journal_lists

The version currently used here was downloaded on 25 Feb 2018
'''

import os
import sys
import csv
import logging
import logging.config

import generic_parser

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

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(BASE_DIR, 'datasets', 'clarivate_analytics')
    source_parser = generic_parser.SourceParser('Clarivate Analytics Master Journal List',
                                                url='http://mjl.clarivate.com/#journal_lists')
    WOS_SOURCE_ID = source_parser.match_or_create_source()

    journal_counter = 0
    for f in os.listdir(input_folder):
        if f.endswith('.csv'):
            logger.info('------------- Working on file {}'.format(f))
            with open(os.path.join(input_folder, f), encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    journal_counter += 1
                    jname = row['Journal Title'].strip().replace('\n', '').title()
                    publisher = row['Publisher'].strip().replace('\n', '').title()
                    issn = row['ISSN'].strip()
                    eissn = row['E-ISSN'].strip()
                    if jname == 'Journal Title':
                        pass
                    else:
                        logger.info('-------------- ({}) Working on journal: {}'.format(journal_counter, jname))

                        j_parser = generic_parser.NodeParser(name=jname, issn=issn, eissn=eissn, publisher=publisher,
                                                         source=WOS_SOURCE_ID)

                        j_parser.match2romeo_publisher()

                        # Attempt to find a match in Orpheus
                        node_id, node_record, match_type = j_parser.match2node()
                        j_parser.node_id, j_parser.node_record = generic_parser.act_on_orpheus_match(j_parser, node_id,
                                                                                           node_record, match_type)


if __name__ == '__main__':
    logging.config.fileConfig('logging.conf', defaults={'logfilename':'wos_parser.log'})
    logger = logging.getLogger('wos_parser')
    main()