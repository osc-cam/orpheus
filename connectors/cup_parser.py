'''
This connector parses Cambridge University Press' embargo 
and APC information from the spreadsheet they make available
on their website at 
https://www.cambridge.org/core/services/aop-file-manager/file/5783738dbd8dfd4e3283c3f2/Cambridge_Journals_APC_price_list.3.5.2.xls

The version currently used here was downloaded on 13 Aug 2018 
'''

import csv
import logging
import logging.config
import os
import re
import sys
from pprint import pprint

import generic_parser
import orpheus_client

from orpheus_constants import CCBY_ID, CCBYNC_ID, CCBYNCSA_ID, CCBYNCND_ID, CUSTOM_ID, PREPRINT_ID, AM_ID, VOR_ID, \
    INST_REPO_ID, SUBJ_REPO_ID, WEBSITE_ID, COMMERCIAL_ID, PUBMED_ID, SOCIAL_ID

ALL_OUTLETS = [INST_REPO_ID, SUBJ_REPO_ID, WEBSITE_ID, COMMERCIAL_ID, PUBMED_ID, SOCIAL_ID]

CUP_GREEN_VERBATIM = '''We require repositories to include:

- If an article has not yet been published, a clear statement that the material has been accepted for publication in a revised form, with a link to the journal’s site on cambridge.org.
- For all published articles, a link to the article’s Version of Record in cambridge.org – for example, via a DOI-based link.
- A clear statement that end-users may view and download the material for private research and study only.

An example statement to accompany the article is:

This article has been published in a revised form in [Journal] [http://doi.org/XXX]. This version is free to view and download for private research and study only. Not for re-distribution, re-sale or use in derivative works. © copyright holder.'''

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

def optimal_green_policies(combination):
    '''
    Returns a list of Orpheus green policies representing the minimum number of policies necessary to accurately
    represent the combination of 8 CUP green policies for any given journal
    :param combination: list of embargo periods for each combination of outlets and versions in CUP's dataset
    :return:
    '''

    # [webpage_AAM, webpage_VoR, inst_repo_AAM, inst_repo_VoR, pmc_AAM, pmc_VoR, social_AAM, social_VoR]
    comb1 = [0, 999, 6, 999, 6, 999, 999, 999]
    comb2 = [0, 999, 0, 999, 0, 999, 999, 999]
    comb3 = [0, 0, 0, 12, 0, 12, 999, 999]
    comb4 = [0, 0, 0, 0, 0, 0, 0, 0]
    comb5 = [0, 0, 0, 0, 0, 12, 999, 999]
    comb6 = [0, 0, 0, 0, 0, 999, 999, 999]
    comb7 = [0, 999, 12, 999, 12, 999, 999, 999]
    comb8 = [0, 0, 0, 999, 0, 999, 999, 999]
    comb9 = [0, 999, 0, 999, 0, 999, 0, 999]
    comb10 = [0, 999, 0, 12, 0, 12, 999, 999]
    comb11 = [0, 999, 6, 999, 5, 999, 999, 999]
    comb12 = [0, 0, 6, 6, 6, 6, 999, 999]
    comb13 = [0, 12, 0, 999, 0, 999, 999, 999] #NEW!

    if combination == comb1:
        policy1 = [999, ALL_OUTLETS, [VOR_ID]]
        policy2 = [6, [INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID], [AM_ID]]
        policy3 = [0, [WEBSITE_ID], [AM_ID]]
        policy4 = [999, [COMMERCIAL_ID, SOCIAL_ID], [AM_ID]]
        array = [policy1, policy2, policy3, policy4]
    elif combination == comb2:
        policy1 = [999, ALL_OUTLETS, [VOR_ID]]
        policy2 = [999, [COMMERCIAL_ID, SOCIAL_ID], [AM_ID]]
        policy3 = [0, [WEBSITE_ID, INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID], [AM_ID]]
        array = [policy1, policy2, policy3]
    elif combination == comb3:
        policy1 = [999, [COMMERCIAL_ID, SOCIAL_ID], [AM_ID, VOR_ID]]
        policy2 = [12, [INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID], [VOR_ID]]
        policy3 = [0, [WEBSITE_ID, INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID], [AM_ID]]
        policy4 = [0, [WEBSITE_ID], [VOR_ID]]
        array = [policy1, policy2, policy3, policy4]
    elif combination == comb4:
        policy1 = [0, ALL_OUTLETS, [AM_ID, VOR_ID]]
        array = [policy1]
    elif combination == comb5:
        policy1 = [0, [WEBSITE_ID, INST_REPO_ID], [AM_ID, VOR_ID]]
        policy2 = [0, [SUBJ_REPO_ID, PUBMED_ID], [AM_ID]]
        policy3 = [12, [SUBJ_REPO_ID, PUBMED_ID], [VOR_ID]]
        policy4 = [999, [COMMERCIAL_ID, SOCIAL_ID], [AM_ID, VOR_ID]]
        array = [policy1, policy2, policy3, policy4]
    elif combination == comb6:
        policy1 = [0, [WEBSITE_ID, INST_REPO_ID], [AM_ID, VOR_ID]]
        policy2 = [0, [SUBJ_REPO_ID, PUBMED_ID], [AM_ID]]
        policy3 = [999, [SUBJ_REPO_ID, PUBMED_ID], [VOR_ID]]
        policy4 = [999, [COMMERCIAL_ID, SOCIAL_ID], [AM_ID, VOR_ID]]
        array = [policy1, policy2, policy3, policy4]
    elif combination == comb7:
        policy1 = [999, ALL_OUTLETS, [VOR_ID]]
        policy2 = [12, [INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID], [AM_ID]]
        policy3 = [0, [WEBSITE_ID], [AM_ID]]
        array = [policy1, policy2, policy3]
    elif combination == comb8:
        #comb8 = [0, 0, 0, 999, 0, 999, 999, 999]
        policy1 = [999, [INST_REPO_ID, SUBJ_REPO_ID, COMMERCIAL_ID, PUBMED_ID, SOCIAL_ID], [VOR_ID]]
        policy2 = [999, [COMMERCIAL_ID, SOCIAL_ID], [AM_ID]]
        policy3 = [0, [WEBSITE_ID, INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID], [AM_ID]]
        policy4 = [0, [WEBSITE_ID], [VOR_ID]]
        array = [policy1, policy2, policy3, policy4]
    elif combination == comb9:
        policy1 = [999, ALL_OUTLETS, [VOR_ID]]
        policy2 = [0, ALL_OUTLETS, [AM_ID]]
        array = [policy1, policy2]
    elif combination == comb10:
        policy1 = [999, [COMMERCIAL_ID, SOCIAL_ID], [AM_ID, VOR_ID]]
        policy2 = [12, [INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID], [VOR_ID]]
        policy3 = [0, [WEBSITE_ID, INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID], [AM_ID]]
        policy4 = [999, [WEBSITE_ID], [VOR_ID]]
        array = [policy1, policy2, policy3, policy4]
    elif combination == comb11:
        policy1 = [999, ALL_OUTLETS, [VOR_ID]]
        policy2 = [6, [INST_REPO_ID], [AM_ID]]
        policy3 = [0, [WEBSITE_ID], [AM_ID]]
        policy4 = [5, [SUBJ_REPO_ID, PUBMED_ID], [AM_ID]]
        policy5 = [999, [COMMERCIAL_ID, SOCIAL_ID], [AM_ID]]
        array = [policy1, policy2, policy3, policy4, policy5]
    elif combination == comb12:
        policy1 = [999, [COMMERCIAL_ID, SOCIAL_ID], [AM_ID, VOR_ID]]
        policy2 = [0, [WEBSITE_ID], [AM_ID, VOR_ID]]
        policy3 = [6, [INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID], [AM_ID, VOR_ID]]
        array = [policy1, policy2, policy3]
    elif combination == comb13:
        #comb13 = [0, 12, 0, 999, 0, 999, 999, 999] #NEW!
        policy1 = [999, [INST_REPO_ID, SUBJ_REPO_ID, COMMERCIAL_ID, PUBMED_ID, SOCIAL_ID], [VOR_ID]]
        policy2 = [999, [COMMERCIAL_ID, SOCIAL_ID], [AM_ID]]
        policy3 = [0, [WEBSITE_ID, INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID], [AM_ID]]
        policy4 = [12, [WEBSITE_ID], [VOR_ID]]
        array = [policy1, policy2, policy3, policy4]

    else:
        error_message = 'Combination {} not supported'.format(combination)
        logger.critical(error_message)
        sys.exit(error_message)
    return array



def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    source_parser = generic_parser.SourceParser('CUP APC Price List 2019.04 24.i.2019',
              url=None)
    SOURCE_ID = source_parser.match_or_create_source()

    cup_website_parser = generic_parser.SourceParser('CUP website: Green Open Access Policy for Journals',
              url='https://www.cambridge.org/core/services/open-access-policies/open-access-journals/'
                  'green-open-access-policy-for-journals')
    CUP_WEBSITE_ID = cup_website_parser.match_or_create_source()

    p_parser = generic_parser.NodeParser(name='Cambridge University Press', type='PUBLISHER', source=SOURCE_ID)
    p_node_id, p_node_record, p_match_type = p_parser.match2node()
    p_parser.node_id, p_parser.node_record = generic_parser.act_on_orpheus_match(p_parser, p_node_id, p_node_record,
                                                                                 p_match_type)

    inputfile = os.path.join(BASE_DIR, 'datasets', 'Cambridge-Journals-APC-price-list-2019.04.csv')

    cup2orpheus_status = {
        '': 'SUBSCRIPTION',
        'Hybrid OA': 'HYBRID',
        'No OA': 'SUBSCRIPTION',
        'Full OA': 'FULLY_OA'
    }

    cup_embargo2months = {
        'On acceptance': 0,
        'On Acceptance': 0,
        'On acceptance (SSRN deposit permitted)': 0,
        'On publication': 0,
        "Publisher's version pdf, no sooner than first publication of the article": 0,
        '5 months after publication': 5,
        '6 months after publication': 6,
        '6months after publication': 6,
        "Publisher's version pdf, no sooner than six months after first publication of the article": 6,
        '12 months after acceptance': 12,
        '12 months after publication': 12,
        '13 months after publication': 13,
        'Abstract only plus link to Cambridge site': 999, # DISALLOWED
        'Abstract only in PDF or HTML, no sooner than publication of full article': 999 # DISALLOWED
    }

    cup_licences2orpheus_ids = {
        'CC-BY': CCBY_ID,
        'CC-BY-NC': CCBYNC_ID,
        'CC-BY-NC-SA': CCBYNCSA_ID,
        'CC-BY-NC-ND': CCBYNCND_ID
    }
    tpounds = re.compile('£[0-9,]+')
    tdollars = re.compile('\$[0-9,]+')

    green_combinations = []
    embargo_strings = []
    with open(inputfile, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        row_counter = 0
        for row in reader:
            row_counter += 1
            # if row_counter < 282:
            #     logger.warning('Skipped; remember to delete or comment out this line later')
            #     continue
            jname = row['Journal'].replace('  ', ' ').strip()
            logger.info('-------({}) Working on journal {}'.format(row_counter, jname))
            jurl = row['URL'].strip()
            issn = row['ISSN'].strip()
            eissn = row['eISSN'].strip()
            oastatus = cup2orpheus_status[row['Open Access status'].strip()]
            apc_data = row['Gold OA APC (plus tax, where applied)'].strip()
            mpounds = tpounds.findall(apc_data)
            mdollars = tdollars.findall(apc_data)
            licence_data = row['Gold OA CC licence options '].strip().split(' / ')

            webpage_AAM = [
                cup_embargo2months[row["Author's personal web page Accepted Manuscript"].strip()],
                [WEBSITE_ID],
                [AM_ID]
                ]
            webpage_VoR = [
                cup_embargo2months[row["Author's personal web page Version of Record"].strip()],
                [WEBSITE_ID],
                [VOR_ID]
                ]

            inst_repo_AAM = [
                cup_embargo2months[row['Departmental web page / Institutional Repository Accepted Manuscript'].strip()],
                [INST_REPO_ID],
                [AM_ID]
                ]
            inst_repo_VoR = [
                cup_embargo2months[row['Departmental web page / Institutional Repository Version of Record'].strip()],
                [INST_REPO_ID],
                [VOR_ID]
                ]

            pmc_AAM = [
                cup_embargo2months[row['Non-commercial Repository / Subject Repository Accepted Manuscript'].strip()],
                [SUBJ_REPO_ID, PUBMED_ID],
                [AM_ID]
                ]
            pmc_VoR = [
                cup_embargo2months[row['Non-commercial Repository / Subject Repository Version of Record'].strip()],
                [SUBJ_REPO_ID, PUBMED_ID],
                [VOR_ID]
                ]

            social_AAM = [
                cup_embargo2months[row['Commercial Repository / Social Media Site Accepted Manuscript'].strip()],
                [SOCIAL_ID],
                [AM_ID]
                ]
            social_VoR = [
                cup_embargo2months[row['Commercial Repository / Social Media Site Version of Record'].strip()],
                [SOCIAL_ID],
                [VOR_ID]
                ]

            # collect all green policy combinations that appear in the dataset
            green_comb = [webpage_AAM[0], webpage_VoR[0], inst_repo_AAM[0], inst_repo_VoR[0],
                                     pmc_AAM[0], pmc_VoR[0], social_AAM[0], social_VoR[0]]
            if green_comb not in green_combinations:
                green_combinations.append(green_comb)

            # continue # uncomment this to produce spreadsheet of all green policy combinations in dataset

            policies_array = optimal_green_policies(green_comb)

            # policies_array = sorted([webpage_AAM, webpage_VoR, inst_repo_AAM, inst_repo_VoR,
            #                          pmc_AAM, pmc_VoR, social_AAM, social_VoR])
            # for e in policies_array[:-1]:
            #     next_e = policies_array[policies_array.index(e)+1] # next item in array
            #     if (e[0] == next_e[0]):
            #     # if (e[0] == next_e[0]) and (e[2] == next_e[2]): # if embargo and version identical to those of next_e
            #         policies_array[policies_array.index(e) + 1][1] += e[1] # add this outlet to next item
            #         policies_array[policies_array.index(e) + 1][2] += e[2] # add this version to next item
            #         policies_array.remove(e) # remove this list item

            # region apc data parsing
            apc_list = []
            apc_currency = None
            apc_value_min = None
            apc_value_max = None
            if mpounds:
                apc_currency = 'GBP'
                for apc in mpounds:
                    apc_list.append(int(apc.replace(',','').replace('£','').strip()))
            elif mdollars:
                apc_currency = 'USD'
                apc_list = []
                for apc in mdollars:
                    apc_list.append(int(apc.replace(',', '').replace('$','').strip()))
            apc_list.sort()
            if apc_list:
                apc_value_min = apc_list[0]
                apc_value_max = apc_list[-1]
            # endregion

            licence_options = []
            for l in licence_data:
                if l:
                    licence_options.append(cup_licences2orpheus_ids[l])


            j_parser = generic_parser.NodeParser(name=jname, publisher='Cambridge University Press', source=SOURCE_ID,
                                                 issn=issn, eissn=eissn, url=jurl, publisher_node_id=p_parser.node_id)
            j_parser.oa_status = oastatus

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

            # parsing OA status
            logger.debug('Calling j_parser.PolicyMatcher(j_parser, policy_type=oa_status).match()')
            j_parser.PolicyMatcher(j_parser, policy_type='oa_status').match()

            # parsing green policies
            preprint = generic_parser.GreenPolicyInstance()
            preprint.outlet = ALL_OUTLETS
            preprint.version = [PREPRINT_ID]
            preprint.version_embargo_months = 0
            preprint.version_green_licence = CUSTOM_ID
            preprint.source = CUP_WEBSITE_ID
            preprint.verbatim = CUP_GREEN_VERBATIM
            preprint.node = preferred_node_id

            logger.debug('Calling j_parser.server_data_match_green_policy(**preprint.as_dict())')
            j_parser.PolicyMatcher(j_parser, policy_type='green').match(**preprint.as_dict())

            for gp in policies_array:
                green = generic_parser.GreenPolicyInstance()

                green.outlet = gp[1]
                green.version = gp[2]
                if gp[0] == 999: # if deposit disallowed
                    green.deposit_allowed = False
                else:
                    green.version_embargo_months = gp[0]
                    green.version_green_licence = CUSTOM_ID
                    green.verbatim = CUP_GREEN_VERBATIM
                green.source = SOURCE_ID
                green.node = preferred_node_id

                logger.debug('Calling j_parser.server_data_match_green_policy(**green.as_dict())')
                j_parser.PolicyMatcher(j_parser, policy_type='green').match(**green.as_dict())

            # parsing gold policy
            if apc_list or licence_data:
                gold = generic_parser.GoldPolicyInstance()

                gold.apc_currency = apc_currency
                gold.apc_value_min = apc_value_min
                gold.apc_value_max = apc_value_max
                gold.source = SOURCE_ID
                gold.licence_options = licence_options
                gold.apc_note = apc_data
                gold.node = preferred_node_id
                logger.debug('Calling j_parser.PolicyMatcher(j_parser, policy_type=gold).match(**gold.as_dict())')
                j_parser.PolicyMatcher(j_parser, policy_type='gold').match(**gold.as_dict())

    pprint(embargo_strings)

    with open('cup_green_combinations.csv', 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['webpage_AAM', 'webpage_VoR', 'inst_repo_AAM', 'inst_repo_VoR',
                                     'pmc_AAM', 'pmc_VoR', 'social_AAM', 'social_VoR'])
        for c in green_combinations:
            writer.writerow(c)

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf', defaults={'logfilename':'cup_parser.log'})
    logger = logging.getLogger('cup_parser')
    main()