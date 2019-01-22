'''
This connector parses Elsevier embargo information from Andrew Gray's
"Elsevier embargo periods, 2013-2018" dataset, available at
https://doi.org/10.6084/m9.figshare.1554748.v14
under a CC BY licence
'''

import csv
import logging
import logging.config
import os
import sys
import generic_parser
import orpheus_client

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

TEST_MODE = False
if TEST_MODE:
    logger.warning('Running in test mode!')

preprint_verbatim = '''Authors can share their preprint anywhere at any time.
If accepted for publication, we encourage authors to link from the preprint to their formal publication via its Digital Object Identifier (DOI). Millions of researchers have access to the formal publications on ScienceDirect, and so links will help your users to find, access, cite, and use the best available version.
Authors can update their preprints on arXiv or RePEc with their accepted manuscript .
Please note:

Some society-owned titles and journals that operate double-blind peer review have different preprint policies. Please check the journals Guide for Authors for further information.
Preprints should not be added to or enhanced in any way in order to appear more like, or to substitute for, the final versions of articles.'''

am_verbatim = '''Authors can share their accepted manuscript:

Immediately

via their non-commercial personal homepage or blog
by updating a preprint in arXiv or RePEc with the accepted manuscript
via their research institute or institutional repository for internal institutional uses or as part of an invitation-only research collaboration work-group
directly by providing copies to their students or to research collaborators for their personal use
for private scholarly sharing as part of an invitation-only work group on commercial sites with which Elsevier has an agreement
After the embargo period

via non-commercial hosting platforms such as their institutional repository
via commercial sites with which Elsevier has an agreement
In all cases accepted manuscripts should:

link to the formal publication via its DOI
bear a CC-BY-NC-ND license – this is easy to do, click here to find out how
if aggregated with other manuscripts, for example in a repository or other site, be shared in alignment with our hosting policy
not be added to or enhanced in any way to appear more like, or to substitute for, the published journal article'''

vor_verbatim = '''If you are an author, please share a link to your article rather than the full-text. Millions of researchers have access to the formal publications on ScienceDirect, and so links will help your users to find, access, cite, and use the best available version
If you are an author, you may also share your Published Journal Article privately with known students or colleagues for their personal use
Theses and dissertations which contain embedded PJAs as part of the formal submission can be posted publicly by the awarding institution with DOI links back to the formal publications on ScienceDirect
If you are affiliated with a library that subscribes to ScienceDirect you have additional private sharing rights for others’ research accessed under that agreement. This includes use for classroom teaching and internal training at the institution (including use in course packs and courseware programs), and inclusion of the article for grant funding purposes
Otherwise sharing is by agreement only
The Published Journal Article cannot be shared publicly, for example on ResearchGate or Academia.edu, to ensure the sustainability of peer-reviewed research in journal publications.'''

def main():

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    source_parser = generic_parser.SourceParser('Gray, A. 2018. Elsevier embargo periods, 2013-2018',
                                                url='https://doi.org/10.6084/m9.figshare.1554748.v14')
    ELSEVIER_SOURCE_ID = source_parser.match_or_create_source()
    elsevier_website_parser = generic_parser.SourceParser('Elsevier website: Article Sharing',
                                                url='https://www.elsevier.com/about/policies/sharing')
    ELSEVIER_WEBSITE_ID = elsevier_website_parser.match_or_create_source()

    p_parser = generic_parser.NodeParser(name='Elsevier', type='PUBLISHER', source=ELSEVIER_WEBSITE_ID)
    p_node_id, p_node_record, p_match_type = p_parser.match2node()
    p_parser.node_id, p_parser.node_record = generic_parser.act_on_orpheus_match(p_parser, p_node_id, p_node_record,
                                                                                 p_match_type)

    # preprint policy
    preprint_policy = generic_parser.GreenPolicyInstance()
    preprint_policy.outlet = [INST_REPO_ID, SUBJ_REPO_ID, WEBSITE_ID, COMMERCIAL_ID, PUBMED_ID, SOCIAL_ID]
    preprint_policy.version = [PREPRINT_ID]
    preprint_policy.version_embargo_months = 0
    preprint_policy.version_green_licence = CCBYNCND_ID
    preprint_policy.source = ELSEVIER_WEBSITE_ID
    preprint_policy.verbatim = preprint_verbatim

    # AM policy for personal websites
    am_policy1 = generic_parser.GreenPolicyInstance()
    am_policy1.outlet = [WEBSITE_ID]
    am_policy1.version = [AM_ID]
    am_policy1.version_embargo_months = 0
    am_policy1.version_green_licence = CCBYNCND_ID
    am_policy1.source = ELSEVIER_WEBSITE_ID
    am_policy1.verbatim = am_verbatim

    # AM policy for non-commencial hosting platforms
    am_policy2 = generic_parser.GreenPolicyInstance()
    am_policy2.outlet = [INST_REPO_ID, SUBJ_REPO_ID, PUBMED_ID]
    am_policy2.version = [AM_ID]
    am_policy2.version_green_licence = CCBYNCND_ID
    am_policy2.source = ELSEVIER_SOURCE_ID
    am_policy2.verbatim = am_verbatim

    vor_policy = generic_parser.GreenPolicyInstance()
    vor_policy.outlet = ALL_OUTLETS
    vor_policy.deposit_allowed = False
    vor_policy.version = [VOR_ID]
    vor_policy.source = ELSEVIER_WEBSITE_ID
    vor_policy.verbatim = vor_verbatim

    inputfile = os.path.join(BASE_DIR, 'datasets', 'Elsevier_embargo_periods_by_journal_2013-2018_v_1.14_sheet_UK-2018.csv')

    with open(inputfile, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        row_counter = 0
        for row in reader:
            row_counter += 1
            oastatus = 'HYBRID'
            issn = row['ISSN'].strip()
            jname = row['Journal Name'].strip()
            aam_embargo = row['Embargo Period (months)'].strip()
            if aam_embargo in ['0 / 12', '0 / 24']: # 0/12 month titles are now OA (no embargo) but 12 months for pre-OA papers
                aam_embargo = '0'
            if aam_embargo == '0':
                oastatus = 'FULLY_OA'

            logger.info('-------({}) Working on journal {}; oastatus: {}; issn: {}; '
                         'AM embargo: {}'.format(row_counter, jname, oastatus, issn, aam_embargo))
            j_parser = generic_parser.NodeParser(name=jname, publisher='Elsevier', source=ELSEVIER_SOURCE_ID,
                                                 publisher_node_id=p_parser.node_id)
            j_parser.issn = issn
            j_parser.oa_status = oastatus

            # # identify romeo_publisher and its node in Orpheus # No need to do this for big publisher datasets
            #j_parser.match2romeo_publisher(test_mode=TEST_MODE)

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

            # parsing green policies
            preprint_policy.node = preferred_node_id
            am_policy1.node = preferred_node_id
            am_policy2.node = preferred_node_id
            am_policy2.version_embargo_months = aam_embargo

            # Attach policies to preferred name node
            logger.debug('Calling j_parser.PolicyMatcher(j_parser, policy_type=oa_status).match()')
            j_parser.PolicyMatcher(j_parser, policy_type='oa_status').match()
            logger.debug('Calling j_parser.server_data_match_green_policy(**preprint_policy.as_dict())')
            # logger.debug('preprint_policy.as_dict():')
            # logger.debug(preprint_policy.as_dict())
            j_parser.PolicyMatcher(j_parser, policy_type='green').match(**preprint_policy.as_dict())
            logger.debug('Calling j_parser.server_data_match_green_policy(**am_policy1.as_dict())')
            j_parser.PolicyMatcher(j_parser, policy_type='green').match(**am_policy1.as_dict())
            logger.debug('Calling j_parser.server_data_match_green_policy(**am_policy2.as_dict())')
            j_parser.PolicyMatcher(j_parser, policy_type='green').match(**am_policy2.as_dict())
            if j_parser.oa_status != 'FULLY_OA':
                vor_policy.node = preferred_node_id
                logger.debug('Calling j_parser.server_data_match_green_policy(**vor_policy.as_dict())')
                j_parser.PolicyMatcher(j_parser, policy_type='green').match(**vor_policy.as_dict())

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf', defaults={'logfilename':'elsevier_embargos_parser.log'})
    logger = logging.getLogger('elsevier_embargos_parser')
    main()

