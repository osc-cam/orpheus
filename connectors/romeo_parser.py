'''
This connector imports data from SHERPA/RoMEO into Orpheus, via APIs
'''

import logging
import logging.config
import os
import urllib.request
from bs4 import BeautifulSoup

import generic_parser
import orpheus_client
import romeo_client

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

def get_journals4id(romeo_id, save_offline=True):
    url = 'http://www.sherpa.ac.uk/romeo/journals.php?id={}&fIDnum=|&mode=simple&letter=ALL&la=en'.format(romeo_id)
    r = urllib.request.urlopen(url).read()
    s = BeautifulSoup(r, 'html.parser')
    if save_offline:
        romeo_folder = 'romeo_offline'
        if not os.path.exists(romeo_folder):
            os.mkdir(romeo_folder)
        filename = os.path.join(romeo_folder, romeo_id + '.html')
        with open(filename, 'w') as f:
            f.write(s.prettify())
    journals = []
    for tr in s.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) == 4:
            logger.debug('tds: {}'.format(tds))
            anchors = tds[0].find_all('a')
            info = tds[0].find_all('i')
            name = anchors[-1].string
            if info:
                if info[0].string == 'Now published elsewhere':
                    logger.debug('Skiping journal {} (Now published elsewhere)'.format(name))
                    continue
                else:
                    logger.warning('Unrecognised string in <i></i> block: {}'.format(info))
            issn = tds[1].string
            if issn == '-':
                issn = None
            eissn = tds[2].string
            if eissn == '-':
                eissn = None
            # if tds[3] and (tds[3].string not in ['-']):
            #     anchors = tds[3].find_all('a')
            #     other = anchors[-1].string.strip()
            # else:
            #     other = None
            # this_journal = [name, issn, eissn, other]
            this_journal = [name, issn, eissn]
            logger.debug(this_journal)
            journals.append(this_journal)
    return journals

def main():

    def process_policy(generic_parser_instance, version_list, deposit_allowed):
        generic_parser_instance.PolicyMatcher(generic_parser_instance, policy_type='green').match(**{
            'outlet': [
                PUBMED_ID,
                INST_REPO_ID,
                WEBSITE_ID
            ],
            'version': version_list,
            'deposit_allowed': deposit_allowed,
            'source': SOURCE_ID,
            'verbatim': restrictions_and_conditions,
            'problematic': True,
            'vetted': False,
        })

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    source_parser = generic_parser.SourceParser('SHERPA/RoMEO', url='http://www.sherpa.ac.uk/romeo/index.php')
    SOURCE_ID = source_parser.match_or_create_source()

    offline_file = os.path.join(BASE_DIR, 'romeo_all_publishers.xml')
    romeo = romeo_client.parser(offline_dataset=offline_file)
    # romeo = romeo_client.parser('?all=yes&showfunder=none&ak=', save_dataset=offline_file)
    romeo.parse_response()
    romeo.convert_restrictions()

    publisher_counter = 0
    for k, v in romeo.output_dict.items():
        publisher_counter += 1
        logger.info('-------------- ({}) Working on romeo_id {}'.format(publisher_counter, k))
        if not k in ['outcome', 'apicontrol', 'romeo_id_list', 'romeo_issn_list', 'romeo_publisher_list',
                     'journals_dicts']:
            if ('&#' in v['name']) and v['alias']:
                logging.info('romeo_parser: using {} instead of {} as name for romeo_id {}'.format(v['alias'],
                                                                                                   v['name'], k))
                name = v['alias']
            else:
                name = v['name']
            parser = generic_parser.NodeParser(name = name, romeo_id = k,
                                               source = SOURCE_ID, type ='PUBLISHER')
            node_id, node_record = parser.create_node(force_creation=True)
            if not node_id:
                logging.error('Failed to parse romeo id {}'.format(k))
            else:
                restrictions_and_conditions = ''
                if v['prerestriction']:
                    for r in v['prerestriction']:
                        restrictions_and_conditions += 'Restriction on preprint deposit: ' + str(r) + '\n'
                if v['postrestriction']:
                    for r in v['postrestriction']:
                        restrictions_and_conditions += 'Restriction on AAM deposit: ' + str(r) + '\n'
                if v['pdfrestriction']:
                    for r in v['pdfrestriction']:
                        restrictions_and_conditions += 'Restriction on VoR deposit: ' + str(r) + '\n'

                if v['condition']:
                    restrictions_and_conditions += 'Conditions:\n'
                    for c in v['condition']:
                        restrictions_and_conditions += c + '\n'

                if v['prearchiving'].lower() in ['can', 'restricted']:
                    allowed = True
                elif v['prearchiving'].lower() in ['cannot', 'unclear', 'unknown']:
                    allowed = False
                else:
                    logging.error('Value of romeo prearchiving field unrecognised: {}'.format(v['prearchiving']))
                    allowed = False

                if v['prearchiving'] == v['postarchiving'] == v['pdfarchiving']:
                    process_policy(parser, [AM_ID, PREPRINT_ID,
                                            VOR_ID], allowed)

                elif (v['prearchiving'] == v['postarchiving']):
                    process_policy(parser, [AM_ID, PREPRINT_ID], allowed)
                    if v['pdfarchiving'].lower() in ['can', 'restricted']:
                        allowed = True
                    elif v['pdfarchiving'].lower() in ['cannot', 'unclear', 'unknown']:
                        allowed = False
                    else:
                        logging.error('Value of romeo pdfarchiving field unrecognised: {}'.format(v['pdfarchiving']))
                        allowed = False
                    process_policy(parser, [VOR_ID], allowed)
                elif (v['prearchiving'] == v['pdfarchiving']):
                    process_policy(parser, [PREPRINT_ID, VOR_ID], allowed)
                    if v['postarchiving'].lower() in ['can', 'restricted']:
                        allowed = True
                    elif v['postarchiving'].lower() in ['cannot', 'unclear', 'unknown']:
                        allowed = False
                    else:
                        logging.error('Value of romeo postarchiving field unrecognised: {}'.format(v['postarchiving']))
                        allowed = False
                    process_policy(parser, [AM_ID], allowed)
                elif (v['pdfarchiving'] == v['postarchiving']):
                    process_policy(parser, [PREPRINT_ID], allowed)
                    if v['postarchiving'].lower() in ['can', 'restricted']:
                        allowed = True
                    elif v['postarchiving'].lower() in ['cannot', 'unclear', 'unknown']:
                        allowed = False
                    else:
                        logging.error('Value of romeo postarchiving field unrecognised: {}'.format(v['postarchiving']))
                        allowed = False
                    process_policy(parser, [AM_ID, VOR_ID], allowed)
                else:
                    for archiving, version_id in [('prearchiving', PREPRINT_ID),
                                                  ('postarchiving', AM_ID),
                                                  ('pdfarchiving', VOR_ID)]:
                        if v[archiving].lower() in ['can', 'restricted']:
                            allowed = True
                        elif v[archiving].lower() in ['cannot', 'unclear', 'unknown']:
                            allowed = False
                        else:
                            logging.error('Value of romeo {} field unrecognised: {}'.format(archiving, v[archiving]))
                            allowed = False
                        process_policy(parser, [version_id], allowed)

            # now process each journal
            k_journals = get_journals4id(k)
            journal_counter = 0
            for j in k_journals:
                logger.debug('j: {}'.format(j))
                j_parser = generic_parser.NodeParser(name=j[0], issn=j[1], eissn=j[2], publisher_node_id=node_id,
                                                     source=SOURCE_ID)
                journal_counter += 1
                logger.info('------------({} {}) Working on journal {}'.format(name, journal_counter, j[0]))
                # Attempt to find a match in Orpheus
                j_node_id, j_node_record, match_type = j_parser.match2node()
                j_parser.node_id, j_parser.node_record = generic_parser.act_on_orpheus_match(j_parser, j_node_id,
                                                                                             j_node_record, match_type)

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf', defaults={'logfilename':'romeo_parser.log'})
    logger = logging.getLogger('romeo_parser')
    main()












