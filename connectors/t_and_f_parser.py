import csv
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

preprint_verbatim = '''Author’s Original Manuscript (AOM)
The AOM is your original manuscript (often called a “preprint”). You can share this as much as you like. If you do decide to post it anywhere, including on a scholarly collaboration network, we would recommend you use an amended version of the wording below to encourage usage and citation of your final, published article (the Version of Record).'''

am_verbatim = '''Accepted Manuscript (AM)
As a Taylor & Francis author, you can post your Accepted Manuscript (AM) on your personal website at any point after publication of your article (this includes posting to Facebook, Google groups, and LinkedIn plus linking from Twitter). To encourage citation of your work (and be able to monitor and understand who is reading it using article metrics), we recommend that you insert a link from your posted AM to the published article on Taylor & Francis Online with the following text:

“This is an Accepted Manuscript of an article published by Taylor & Francis in [JOURNAL TITLE] on [date of publication], available online: http://www.tandfonline.com/[Article DOI].”

For example: “This is an Accepted Manuscript of an article published by Taylor & Francis Group in Africa Review on 17/04/2014, available online: http://www.tandfonline.com/10.1080/12345678.1234.123456.

N.B. Using a DOI will form a link to the Version of Record on Taylor & Francis Online.

The AM is defined by the National Information Standards Organization as:
“The version of a journal article that has been accepted for publication in a journal.”

This means the version that has been through peer review and been accepted by a journal editor. When you receive the acceptance email from the Editorial Office, keep a copy of your AM for any future posting.

Embargoes apply if you are posting the AM to an institutional or subject repository, or to a scholarly collaboration network such as Mendeley.'''

vor_verbatim = '''Version of Record (VoR)
This is your final, published article. We recommend that you include a link to the VoR from anywhere you have posted your AOM or AM using the text above. Please do not post the PDF of the VoR unless you have chosen to publish your article open access. This applies to any author who has published in a Taylor & Francis or Routledge journal.'''

def convert_dataset_to_csv(bs_instance, filename):
    '''
    Helper function to convert T&F data into a csv file
    :param bs_instance: instance of bs4.BeautifulSoup containing the website data
    :param filename: name of output csv file
    :return:
    '''
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Journal name'])
        for tr in bs_instance.find_all('tr'):
            td_counter = 0
            for td in tr.find_all('td'):
                td_counter += 1
                if td.string:
                    if td_counter == 1:
                        jname = td.string.strip()
                        writer.writerow([jname])

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    tf_url = 'https://authorservices.taylorandfrancis.com/journal-list/'
    source_parser = generic_parser.SourceParser('T&F website: Open Access Options', url=tf_url)
    SOURCE_ID = source_parser.match_or_create_source()

    website_parser = generic_parser.SourceParser('T&F website: Sharing Your Work',
                            url='https://authorservices.taylorandfrancis.com/sharing-your-work/')
    TF_WEBSITE_ID = website_parser.match_or_create_source()

    p_parser = generic_parser.NodeParser(name='Taylor & Francis', type='PUBLISHER', source=SOURCE_ID)
    p_node_id, p_node_record, p_match_type = p_parser.match2node()
    p_parser.node_id, p_parser.node_record = generic_parser.act_on_orpheus_match(p_parser, p_node_id, p_node_record,
                                                                                 p_match_type)

    req = urllib.request.Request(tf_url, headers={'User-Agent': 'Mozilla/5.0'})
    r = urllib.request.urlopen(req).read()
    s = BeautifulSoup(r, 'html.parser')

    oa_status_dict = {
        'Fully Open': 'FULLY_OA',
        'No Gold OA Option Available': 'SUBSCRIPTION',
        'Yes': 'HYBRID'
    }

    licence_dict = {
        'CC BY': CCBY_ID,
        'CC BY-NC': CCBYNC_ID,
        'CC BY-NC-ND': CCBYNCND_ID,
        'N/A': None,
        '© The Royal Society of New Zealand': CUSTOM_ID
    }

    # logger.debug(s)

    # convert_dataset_to_csv(s, 't_and_f_journal_list.csv')

    journal_counter = 0
    embargo_data_values = [] #['0 months', '12 months', '18 months', '6 months']
    oa_status_values = [] #['Fully Open', 'No Gold OA Option Available', 'Yes']
    licence_choices_values = [] #['CC BY', 'CC BY-NC', 'CC BY-NC-ND', 'N/A', '© The Royal Society of New Zealand']
    for tr in s.find_all('tr'):
        j_parser = generic_parser.NodeParser(publisher='Taylor & Francis', source=SOURCE_ID,
                                             publisher_node_id=p_parser.node_id)
        preferred_node_id = None
        licence_options = []
        website_embargo = None
        repo_embargo = None
        td_counter = 0
        for td in tr.find_all('td'):
            td_counter += 1
            # logger.debug(td.string)
            if td.string:
                if td_counter == 1:
                    j_parser.name = td.string.strip()
                    # logger.debug('j_parser.name: {}'.format(j_parser.name))
                elif td_counter == 2:
                    j_parser.issn = td.string.strip()
                    # logger.debug('j_parser.issn: {}'.format(j_parser.issn))

                elif td_counter == 3:
                    j_parser.eissn = td.string.strip()
                    # logger.debug('j_parser.eissn: {}'.format(j_parser.eissn))

                elif td_counter == 4:
                    oa_status = td.string.strip()
                    if oa_status not in oa_status_values:
                        oa_status_values.append(oa_status)
                    j_parser.oa_status = oa_status_dict[oa_status]
                    # logger.debug('j_parser.oa_status: {}'.format(j_parser.oa_status))

                elif td_counter == 5:
                    embargo_data = td.string.strip()
                    if embargo_data not in embargo_data_values:
                        embargo_data_values.append(embargo_data)
                    website_embargo = embargo_data.replace('months', '').strip()

                elif td_counter == 6:
                    embargo_data = td.string.strip()
                    if embargo_data not in embargo_data_values:
                        embargo_data_values.append(embargo_data)
                    repo_embargo = embargo_data.replace('months', '').strip()

                elif td_counter in [7, 8]:
                    licence_choices = td.string.strip()
                    if licence_choices not in licence_choices_values:
                        licence_choices_values.append(licence_choices)
                    if licence_dict[licence_choices]:
                        licence_options.append(licence_dict[licence_choices])

                else:
                    pass
            else:
                pass

        if j_parser.name: # needed because header of table is a tr, but has no td (only th)
            journal_counter += 1
            logger.info('------------({}) Working on journal {}'.format(journal_counter, j_parser.name))

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

            # Parse Oa status
            logger.debug('Calling j_parser.PolicyMatcher(j_parser, policy_type=oa_status).match()')
            j_parser.PolicyMatcher(j_parser, policy_type='oa_status').match()

            # Gold Oa policy
            if j_parser.oa_status != 'SUBSCRIPTION':
                gold = generic_parser.GoldPolicyInstance()
                gold.licence_options = licence_options
                gold.apc_currency = 'GBP'
                gold.node = preferred_node_id
                gold.source = SOURCE_ID
                logger.debug('Calling j_parser.PolicyMatcher(j_parser, policy_type=gold).match(**gold.as_dict())')
                j_parser.PolicyMatcher(j_parser, policy_type='gold').match(**gold.as_dict())

            # Green policies
            website_policy = generic_parser.GreenPolicyInstance()
            website_policy.node = preferred_node_id
            website_policy.outlet = [WEBSITE_ID]
            website_policy.version = [AM_ID]
            website_policy.version_embargo_months = website_embargo
            website_policy.version_green_licence = CUSTOM_ID
            website_policy.source = SOURCE_ID
            website_policy.verbatim = am_verbatim

            if website_embargo == repo_embargo:
                website_policy.outlet += [INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID, SOCIAL_ID]
            else:
                repo_policy = generic_parser.GreenPolicyInstance()
                repo_policy.node = preferred_node_id
                repo_policy.outlet = [INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID, SOCIAL_ID]
                repo_policy.version = [AM_ID]
                repo_policy.version_embargo_months = repo_embargo
                repo_policy.version_green_licence = CUSTOM_ID
                repo_policy.source = SOURCE_ID
                repo_policy.verbatim = am_verbatim
                logger.debug('Calling j_parser.server_data_match_green_policy(**repo_policy.as_dict())')
                j_parser.PolicyMatcher(j_parser, policy_type='green').match(**repo_policy.as_dict())

            logger.debug('Calling j_parser.server_data_match_green_policy(**website_policy.as_dict())')
            j_parser.PolicyMatcher(j_parser, policy_type='green').match(**website_policy.as_dict())

            if j_parser.oa_status != 'FULLY_OA':
                vor_policy = generic_parser.GreenPolicyInstance()
                vor_policy.node = preferred_node_id
                vor_policy.outlet = ALL_OUTLETS
                vor_policy.deposit_allowed = False
                vor_policy.version = [VOR_ID]
                vor_policy.source = TF_WEBSITE_ID
                vor_policy.verbatim = vor_verbatim
                logger.debug('Calling j_parser.server_data_match_green_policy(**vor_policy.as_dict())')
                j_parser.PolicyMatcher(j_parser, policy_type='green').match(**vor_policy.as_dict())
        else:
            logger.error('Could not find or parse journal name in table row {}'.format(tr))

    logger.info('embargo_data_values: {}'.format(sorted(embargo_data_values)))
    logger.info('oa_status_values: {}'.format(sorted(oa_status_values)))
    logger.info('licence_choices_values: {}'.format(sorted(licence_choices_values)))

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf', defaults={'logfilename':'t_and_f_parser.log'})
    logger = logging.getLogger('t_and_f_parser')
    main()

