'''
Parser of DOAJ csv files containing the entire DOAJ database (these csv files are updated every 30 minutes and
can be downloaded from https://doaj.org/csv )
'''

'''
DOAJ csv columns:
Journal title
Journal URL
Alternative title
Journal ISSN (print version)
Journal EISSN (online version)
Publisher
Society or institution
Platform, host or aggregator
Country of publisher
Journal article processing charges (APCs)
APC information URL
APC amount
Currency
Journal article submission fee
Submission fee URL
Submission fee amount
Submission fee currency
Number of articles publish in the last calendar year
Number of articles information URL
Journal waiver policy (for developing country authors etc)
Waiver policy information URL
Digital archiving policy or program(s)
Archiving: national library
Archiving: other
Archiving infomation URL
Journal full-text crawl permission
Permanent article identifiers
Journal provides download statistics
Download statistics information URL
First calendar year journal provided online Open Access content
Full text formats
Keywords
Full text language
URL for the Editorial Board page
Review process
Review process information URL
URL for journal's aims & scope
URL for journal's instructions for authors
Journal plagiarism screening policy
Plagiarism information URL
Average number of weeks between submission and publication
URL for journal's Open Access statement
Machine-readable CC licensing information embedded or displayed in articles
URL to an example page with embedded licensing information
Journal license
License attributes
URL for license terms
Does this journal allow unrestricted reuse in compliance with BOAI?
Deposit policy directory
Author holds copyright without restrictions
Copyright information URL
Author holds publishing rights without restrictions
Publishing rights information URL
DOAJ Seal
Tick: Accepted after March 2014
Added on Date
Subjects
'''


import csv
import logging
import logging.config
import os
import re
import sys
import time
import generic_parser
import orpheus_client

from pprint import pprint

from orpheus_constants import CC0_ID, CCBY_ID, CCBYNC_ID, CCBYND_ID, CCBYSA_ID, CCBYNCND_ID, CCBYNCSA_ID, CUSTOM_ID

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
    currency_dict = {
                    '': '',
                    'EUR - Euro': 'EUR',
                    'CZK - Czech Koruna': 'CZK',
                    'BRL - Brazilian Real': 'BRL',
                    'USD - US Dollar': 'USD',
                    'GBP - Pound Sterling': 'GBP',
                    'ZAR - Rand': 'ZAR',
                    'ARS - Argentine Peso': 'ARS',
                    'JPY - Yen': 'JPY',
                    'PKR - Pakistan Rupee': 'PKR',
                    'PLN - Zloty': 'PLN',
                    'CHF - Swiss Franc': 'CHF',
                    'EGP - Egyptian Pound': 'EGP',
                    'COP - Colombian Peso': 'COP',
                    'IDR - Rupiah': 'IDR',
                    'MXN - Mexican Peso': 'MXN',
                    'RSD - Serbian Dinar': 'RSD',
                    'RUB - Russian Ruble': 'RUB',
                    'SAR - Saudi Riyal': 'SAR',
                    'CNY - Yuan Renminbi': 'CNY',
                    'NOK - Norwegian Krone': 'NOK',
                    'CAD - Canadian Dollar': 'CAD',
                    'INR - Indian Rupee': 'INR',
                    'IRR - Iranian Rial': 'IRR',
                    'TWD - New Taiwan Dollar': 'TWD',
                    'KRW - Won': 'KRW',
                    'TRY - Turkish Lira': 'TRY',
                    'RON - New Romanian Leu': 'RON',
                    'KZT - Tenge': 'KZT',
                    'IQD - Iraqi Dinar': 'IQD',
                    'UAH - Hryvnia': 'UAH',
                    'XAF - CFA Franc BEAC': 'XAF',
                    'THB - Baht': 'THB',
                    'BDT - Taka': 'BDT',
                    'MDL - Moldovan Leu': 'MDL',
                    'MYR - Malaysian Ringgit': 'MYR',
                    'AUD - Australian Dollar': 'AUD',
                    'NGN - Naira': 'NGN',
                    'VEF - Bolivar': 'VEF',
                }
    licence_dict = {
                    '' : '',
                    'CC BY' : CCBY_ID,
                    'CC BY-NC-ND' : CCBYNCND_ID,
                    'CC BY-NC' : CCBYNC_ID,
                    'CC BY-ND' : CCBYND_ID,
                    "Publisher's own license" : CUSTOM_ID,
                    'CC BY-SA' : CCBYSA_ID,
                    'CC BY-NC-SA' : CCBYNCSA_ID,
                    'public domain' : CC0_ID,
                }

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    source_parser = generic_parser.SourceParser('DOAJ',
                                                url='https://doaj.org')
    SOURCE_ID = source_parser.match_or_create_source()

    inputfile = os.path.join(BASE_DIR, 'datasets', 'doaj_20180802_2230_utf8.csv')
    # inputfile = os.path.join(BASE_DIR, 'datasets', 'doaj_20180719_1330_utf8.csv')
    # inputfile = os.path.join(BASE_DIR, 'datasets', 'doaj_test.csv')
    with open(inputfile, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        counter = 0
        for row in reader:
            counter += 1
            jname = row['Journal title'].strip().replace('  ', ' ').replace('  ', ' ')
            jurl = row['Journal URL'].strip()
            jsynonym = row['Alternative title'].strip()
            issn = row['Journal ISSN (print version)'].strip()
            eissn = row['Journal EISSN (online version)'].strip()
            jpublisher = row['Publisher'].strip().replace('  ', ' ').replace('  ', ' ')
            charges_apc = row['Journal article processing charges (APCs)'].strip()
            apc_amount = row['APC amount'].strip()
            apc_currency = currency_dict[row['Currency'].strip()]
            jlicence = licence_dict[row['Journal license'].strip()]

            # publisher_country = row['Country of publisher'].strip()
            # deposit_policy = row['Digital archiving policy or program(s)'].strip()
            # keywords = row['Keywords'].strip()
            # peer_review = row['Review process'].strip()
            # publication_delay_weeks = row['Average number of weeks between submission and publication'].strip()
            # subjects = row['Subjects'].strip()

            logger.info('------------ ({}) Working on journal {}'.format(counter, jname))

            j_parser = generic_parser.NodeParser(name=jname, issn=issn, eissn=eissn, publisher=jpublisher,
                                                 source=SOURCE_ID, url=jurl)
            j_parser.oa_status = 'FULLY_OA'

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

            # Parsing alternative title
            if jsynonym:
                logger.debug('Processing alternative title "{}"'.format(jsynonym))
                syn_parser = generic_parser.NodeParser(name=jsynonym, issn=issn, eissn=eissn,
                                                       publisher=j_parser.publisher,
                                                       publisher_node_record=j_parser.publisher_node_record,
                                                       publisher_node_id=j_parser.publisher_node_id,
                                                       source=SOURCE_ID, url=jurl)
                syn_parser.name_status = 'SYNONYM'
                syn_parser.synonym_of = preferred_node_id
                syn_id, syn_record, match_type = syn_parser.match2node()
                generic_parser.act_on_orpheus_match(syn_parser, syn_id, syn_record, match_type)

            # Attach OA status policy to preferred name node
            logger.debug('Calling j_parser.PolicyMatcher(j_parser, policy_type=oa_status).match(); '
                         'j_parser.node_id {}'.format(j_parser.node_id))
            j_parser.PolicyMatcher(j_parser, policy_type='oa_status').match()

            # Parsing gold policy info if available
            if jlicence or apc_currency or apc_amount:
                gp = generic_parser.GoldPolicyInstance()
                # gp.node = preferred_node_id
                gp.source = SOURCE_ID
                gp.default_licence = jlicence
                if apc_currency:
                   gp.apc_currency = apc_currency
                if charges_apc == 'No':
                   gp.apc_value_min = 0
                   gp.apc_value_max = 0
                else:
                   if apc_amount:
                       gp.apc_value_min = int(apc_amount)
                       gp.apc_value_max = int(apc_amount)

                logger.debug("Calling j_parser.PolicyMatcher(j_parser, policy_type='gold').match(**gp.as_dict())")
                j_parser.PolicyMatcher(j_parser, policy_type='gold').match(**gp.as_dict())
            else:
                logger.debug("DOAJ does not have information on the gold policy of {}".format(jname))


if __name__ == '__main__':
    logging.config.fileConfig('logging.conf', defaults={'logfilename':'doaj_parser.log'})
    logger = logging.getLogger('doaj_parser')
    main()