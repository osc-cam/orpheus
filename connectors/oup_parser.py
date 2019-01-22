import logging
import logging.config
import os
import sys
import urllib.request
from bs4 import BeautifulSoup

import generic_parser

from orpheus_constants import CCBY_ID, CCBYNC_ID, CCBYNCSA_ID, CCBYNCND_ID, CUSTOM_ID, PREPRINT_ID, AM_ID, VOR_ID, \
    INST_REPO_ID, SUBJ_REPO_ID, WEBSITE_ID, COMMERCIAL_ID, PUBMED_ID, SOCIAL_ID

ALL_OUTLETS = [INST_REPO_ID, SUBJ_REPO_ID, WEBSITE_ID, COMMERCIAL_ID, PUBMED_ID, SOCIAL_ID]

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

preprint_verbatim = '''The Author’s Original Version (AOV) is the un-refereed author version of an article as submitted for publication in an Oxford University Press journal. This is sometimes known as the “preprint” version. The author accepts full responsibility for this version of the article, and the content and layout is set out by the author.

Authors may make their AOV available anywhere at any time. This includes posting on their own personal websites, institutional or non-commercial or subject based repositories, commercial websites or repositories, or social media, provided that, upon acceptance, they acknowledge that the article has been accepted for publication as follows:

This article has been accepted for publication in [Journal Title] Published by Oxford University Press.

After publication we would also ask authors to update their AOV with the Digital Object Identifier (DOI), and include a link to the Version of Record.'''

am_verbatim = '''Authors may also immediately upload their AM to their institutional or other non-commercial subject based repositories (on the proviso that it is not made publicly available until after the specified embargo period)
After embargo
Authors may upload their AM to an institutional repository or other non-commercial repositories, and make it publicly available. Accepted Manuscripts may not be uploaded or shared oncommercial websites or repositories, unless the website or repository has signed an agreement with OUP permitting such uploading or sharing.
Embargo periods may vary between journals. For details of a journal’s specific embargo period, please see the information for each individual title in our Accepted Manuscript embargo period list.

When making an accepted manuscript available, authors should include the following acknowledgment as well as a link to the version of record. This will guarantee that the version of record is readily available to those accessing the article from public repositories, and means that the article is more likely to be cited correctly.

This is a pre-copyedited, author-produced version of an article accepted for publication in [insert journal title] following peer review. The version of record [insert complete citation information here] is available online at: xxxxxxx [insert URL and DOI of the article on the OUP website].'''

vor_verbatim = '''The Version of Record (VOR) is defined here as the final typeset and edited version of the journal article that has been made available by OUP formally and exclusively declaring the article “published”. This includes any ‘advanced access’ article even before the compilation of a volume issue.

The VOR as it appears in the journal following copyediting and proof correction may not be deposited by authors in institutional repositories or posted to third party websites and made publicly available unless the article is published on an Open Access model licence that allows for such posting. Authors may share their VOR with private groups within their institution or through private groups on non-commercial repositories that are signatories to the STM Voluntary principles for article sharing on Scholarly Collaboration Networks (SCN). The VOR may not be uploaded or shared on commercial websites or repositories, unless the website or repository has signed an agreement with OUP permitting such uploading or sharing.'''

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    oup_url = 'https://academic.oup.com/journals/pages/access_purchase/rights_and_permissions/embargo_periods'
    source_parser = generic_parser.SourceParser('OUP website: Accepted Manuscript Embargo Periods', url=oup_url)
    SOURCE_ID = source_parser.match_or_create_source()

    website_parser = generic_parser.SourceParser('OUP website: Author self-archiving policy',
                            url='https://academic.oup.com/journals/pages/access_purchase/rights_and_permissions/'
                                'author_self_archiving_policy')
    OUP_WEBSITE_ID = website_parser.match_or_create_source()

    p_parser = generic_parser.NodeParser(name='Oxford University Press', type='PUBLISHER', source=SOURCE_ID)
    p_node_id, p_node_record, p_match_type = p_parser.match2node()
    p_parser.node_id, p_parser.node_record = generic_parser.act_on_orpheus_match(p_parser, p_node_id, p_node_record,
                                                                                 p_match_type)

    r = urllib.request.urlopen(oup_url).read()
    s = BeautifulSoup(r, 'html.parser')

    journal_counter = 0
    embargo_data_values = []
    for tr in s.find_all('tr'):
        j_parser = generic_parser.NodeParser(publisher='Oxford University Press', source=SOURCE_ID,
                                             publisher_node_id=p_parser.node_id)
        preferred_node_id = None
        td_counter = 0
        for td in tr.find_all('td'):
            td_counter += 1
            if td.string:
                jname = td.string.replace('\n', '').strip()
            if td.a:
                if ('\n' in td.a.string) or ('Custom' in td.a.string):
                    embargo_data = ' '.join(td.a.string.replace('months', '').split()) #https://stackoverflow.com/a/1546251
                else:
                    jname = td.a.string.replace('\n', '').strip()

            if td_counter % 2 == 0: #Even (This td contains AM embargo_data)
                if embargo_data in ['Full Open Access', 'Fully Open Access']:
                    j_parser.oa_status = 'FULLY_OA'
                    logger.debug('{} is an open access journal. Calling j_parser.PolicyMatcher(j_parser, '
                                 'policy_type=oa_status).match()'.format(j_parser.name))
                    j_parser.PolicyMatcher(j_parser, policy_type='oa_status').match()
                elif embargo_data in 'Custom':
                    logger.debug('Skipping custom AM self-archiving policy ({})'.format(j_parser.name))
                else:
                    if not preferred_node_id:
                        sys.exit('preferred_node_id not set for {}'.format(j_parser.name))
                    am_policy = generic_parser.GreenPolicyInstance()
                    am_policy.node = preferred_node_id
                    am_policy.outlet = [INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID]
                    am_policy.version = [AM_ID]
                    am_policy.version_embargo_months = int(embargo_data)
                    am_policy.version_green_licence = CUSTOM_ID
                    am_policy.source = SOURCE_ID
                    am_policy.verbatim = am_verbatim
                    logger.debug('Calling j_parser.server_data_match_green_policy(**am_policy.as_dict())')
                    j_parser.PolicyMatcher(j_parser, policy_type='green').match(**am_policy.as_dict())

                preprint_policy = generic_parser.GreenPolicyInstance()
                preprint_policy.node = preferred_node_id
                preprint_policy.outlet = ALL_OUTLETS
                preprint_policy.version = [PREPRINT_ID]
                preprint_policy.version_embargo_months = 0
                preprint_policy.version_green_licence = CUSTOM_ID
                preprint_policy.source = OUP_WEBSITE_ID
                preprint_policy.verbatim = preprint_verbatim
                logger.debug('Calling j_parser.server_data_match_green_policy(**preprint_policy.as_dict())')
                j_parser.PolicyMatcher(j_parser, policy_type='green').match(**preprint_policy.as_dict())

                website_policy = generic_parser.GreenPolicyInstance()
                website_policy.node = preferred_node_id
                website_policy.outlet = [WEBSITE_ID]
                website_policy.version = [AM_ID]
                website_policy.version_embargo_months = 0
                website_policy.version_green_licence = CUSTOM_ID
                website_policy.source = OUP_WEBSITE_ID
                website_policy.verbatim = 'Authors may make their AM available on their non-commercial homepage or blog. They may also privately share their work within their institution for the purposes of research or education, and make copies available to colleagues or students for their personal use providing that the AM is not made publicly available until after the embargo period.'
                logger.debug('Calling j_parser.server_data_match_green_policy(**website_policy.as_dict())')
                j_parser.PolicyMatcher(j_parser, policy_type='green').match(**website_policy.as_dict())
                
                if j_parser.oa_status != 'FULLY_OA':
                    vor_policy = generic_parser.GreenPolicyInstance()
                    vor_policy.node = preferred_node_id
                    vor_policy.outlet = ALL_OUTLETS
                    vor_policy.deposit_allowed = False
                    vor_policy.version = [VOR_ID]
                    vor_policy.source = OUP_WEBSITE_ID
                    vor_policy.verbatim = vor_verbatim
                    logger.debug('Calling j_parser.server_data_match_green_policy(**vor_policy.as_dict())')
                    j_parser.PolicyMatcher(j_parser, policy_type='green').match(**vor_policy.as_dict())

            else: # Odd (This td contains the journal name)
                journal_counter += 1
                logger.info('------------({}) Working on journal {}'.format(journal_counter, jname))
                j_parser.name = jname
                j_parser.get_issn_from_romeo()

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

    logger.info('embargo_data_values: {}'.format(sorted(embargo_data_values)))

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf', defaults={'logfilename':'oup_parser.log'})
    logger = logging.getLogger('oup_parser')
    main()

