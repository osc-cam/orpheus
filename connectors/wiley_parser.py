'''
Parser for Wiley's "Author Compliance tool": https://authorservices.wiley.com/author-resources/Journal-Authors/open-access/author-compliance-tool.html

Compliance tool journal variables (javascript):

JOAP: Does the journal offer an OA option ('Offers OnlineOpen','No OA option', 'Fully Open Access') --- Map to Orpheus OA status

JOAPL: URL of journals Gold policy ('<a target="_blank" href="http://onlinelibrary.wiley.com/journal/0077-8923/homepage/FundedAccess.html">View policy</a>') --- Map to Orpheus source?

JL: Gold policy choice of licences ('--','Choice of CC BY, CC BY-NC, or CC BY-NC-ND<br />CC BY for mandated authors') --- Map to Orpheus available licences

JAPC: APC value ('$2,500','$4,300','--') --- Map to Orpheus APC currency and value

JAPCL: APC link ('--','<a target="_blank" href="http://onlinelibrary.wiley.com/journal/13652427/homepage/FundedAccess.html">More info</a>') --- Map to Orpheus source?

JSAP: Standard or non-standard self-archiving policy ('Standard Policy','Non-Standard Policy') --- Ignore?

JSAPL: Self-archiving policy link ('<a target="_blank" href="https://onlinelibrary.wiley.com/page/journal/15222640/homepage/2004_onlineopen.html">View policy</a>') --- Map to Orpheus source?

JSV: Submitted version embargo ('On publication','On submission') --- Map to Orpheus embargo months for submitted version

JAV: Accepted version embargo ('Refer to copyright or contact managing editor','12mo embargo') --- Map to Orpheus embargo months for accepted version

JDP: Data sharing policy ('Encouraged', 'Expected', 'Own Policy', 'No Policy') --- Ignore?

JDPL: Data sharing policy link --- Ignore?

JAWPP: Preprint policy ('Accepts Preprints','Does Not Accept Preprints') --- Ignore?

JAWPPL: Preprint policy link --- Ignore?

JOIDP: ORCID policy ('Required','Encouraged','No policy') --- Ignore?
'''

import logging
import logging.config
import os
import re
import sys
import generic_parser

from pprint import pprint

from orpheus_constants import CCBY_ID, CCBYNC_ID, CCBYNCND_ID, CUSTOM_ID, PREPRINT_ID, AM_ID, VOR_ID, INST_REPO_ID, \
    SUBJ_REPO_ID, WEBSITE_ID

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

class javascript_variable():
    def __init__(self, abv):
        self.abbreviation = abv
        self.values = None
    def __str__(self):
        return self.abbreviation
    def parse_values(self, data):
        pattern = r'''<script type=text/javascript> var ABBREVIATION = \[(.*) ]; function changeTextABBREVIATION\(elemid\) {var ind = document.getElementById\(elemid\).selectedIndex; document.getElementById\("displayABBREVIATION"\).innerHTML=ABBREVIATION\[ind\];} </script>'''.replace('ABBREVIATION', self.abbreviation)
        t = re.compile(pattern, re.DOTALL)
        m = t.search(data)
        s = m.group(1).strip("'")
        self.values = re.split("',\n?'", s)
        return self.values

def print_possible_values_of_wiley_variables():
    counter = 1
    values_oa_status = []
    values_gold = []
    values_apc = []
    values_pre_embargo = []
    values_am_embargo = []
    for j in journals[1:]:
        if oa_stata.values[counter] not in values_oa_status:
            values_oa_status.append(oa_stata.values[counter])
        if gold_licences.values[counter] not in values_gold:
            values_gold.append(gold_licences.values[counter])
        if apcs.values[counter] not in values_apc:
            values_apc.append(apcs.values[counter])
        if preprint_embargos.values[counter] not in values_pre_embargo:
            values_pre_embargo.append(preprint_embargos.values[counter])
        if am_embargos.values[counter] not in values_am_embargo:
            values_am_embargo.append(am_embargos.values[counter])
        counter += 1
    print('values_oa_status:', values_oa_status)
    print('values_gold:', values_gold)
    print('values_apc', values_apc)
    print('values_pre_embargo', values_pre_embargo)
    print('values_am_embargo', values_am_embargo)

# TEST_MODE set to True means that this script will not attempt to:
# - query the RoMEO API to determine publisher romeo_id
# - find a matching publisher in Orpheus for romeo_id obtained from RoMEO API

TEST_MODE = False
if TEST_MODE:
    logger.warning('Running in test mode!')

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    source_parser = generic_parser.SourceParser('Wiley Author Compliance Tool',
                                                url='https://authorservices.wiley.com/author-resources/Journal-Authors/licensing-open-access/open-access/author-compliance-tool.html')
    WILEY_SOURCE_ID = source_parser.match_or_create_source()

    p_parser = generic_parser.NodeParser(name='Wiley', type='PUBLISHER', source=WILEY_SOURCE_ID)
    p_node_id, p_node_record, p_match_type = p_parser.match2node()
    p_parser.node_id, p_parser.node_record = generic_parser.act_on_orpheus_match(p_parser, p_node_id, p_node_record,
                                                                                 p_match_type)

    f = open(os.path.join(BASE_DIR, 'datasets', 'wiley_compliance_tool.html'))
    data = f.read()
    f.close()

    # translation dicts
    oa_status_dict = {
        'Offers OnlineOpen' : 'HYBRID',
        'No OA option' : 'SUBSCRIPTION',
        'Fully Open Access' : 'FULLY_OA'
    }

    default_licence_options = [CCBY_ID, CCBYNC_ID, CCBYNCND_ID]

    licence_choices_dict = {
        'Choice of CC BY, CC BY-NC, or CC BY-NC-ND<br />CC BY for mandated authors' : default_licence_options,
        '--' : [],
        'Choice of CC BY-NC or CC BY-NC-ND<br />CC BY for mandated authors' : default_licence_options,
        'No CC license offered' : [CUSTOM_ID],
        'CC BY' : [CCBY_ID],
        'CC BY for mandated authors' : [CCBY_ID],
        'CC-BY' : [CCBY_ID],
        'CC BY-NC-ND<br />CC BY for mandated authors' : [CCBY_ID, CCBYNCND_ID],
        'Choice of CC BY, CC BY-NC, or CC BY-NC-ND': default_licence_options,
        'Choice of CC BY, CC BY-NC or CC BY-NC-ND': default_licence_options,
        'Choice of CC BY-NC or CC BY-ND-ND<br />CC-BY mandate only': default_licence_options,
        'CC BY, CC BY-NC, or CC BY-NC-ND<br />CC BY for mandated authors': default_licence_options,
        'CC BY-NC-ND': [CCBYNCND_ID],
        'CC BY, CC BY-NC, CC BY-NC-ND ': default_licence_options,
        'CC BY (mandated only), CC BY NC, CC BY NC ND': default_licence_options,
        'CC BY-NC<br />CC BY for mandated authors': [CCBY_ID, CCBYNC_ID],
        'CC BY NC ND': [CCBYNCND_ID]
    }

    # journal_block
    t = re.compile(r'''<select class="journal" id="journal"(.*)</select>\n</form>''', re.DOTALL)
    m = t.search(data)
    journal_block = m.group(1).replace('''"<option value='1132'>Journal of World Intellectual Property - The\n</option>"''', "<option value='1132'>Journal of World Intellectual Property - The</option>")
    journals = []
    t = re.compile(r'''^<option value=['"]([0-9]+)['"]>(.+)</option>$''', re.MULTILINE)
    m = t.findall(journal_block)
    for id, journal_name in m:
        journals.append(journal_name)

    # attributes
    oa_stata = javascript_variable('JOAP')
    oa_stata.parse_values(data)

    gold_licences = javascript_variable('JL')
    gold_licences.parse_values(data)

    apcs = javascript_variable('JAPC')
    apcs.parse_values(data)

    preprint_embargos = javascript_variable('JSV')
    preprint_embargos.parse_values(data)

    am_embargos = javascript_variable('JAV')
    am_embargos.parse_values(data)

    # check that the number of values of each attribute matches the number of journals
    for a in [oa_stata.values, gold_licences.values, apcs.values, preprint_embargos.values, am_embargos.values]:
        if len(a) != len(journals):
            error_msg = 'Number of values of variable ({}) does not match number of journals ({}). This could be because ' \
                        '`Journal of World Intellectual Property` spans more than 1 line in input dataset. Check and, ' \
                        'if so, edit the input to fix that. First 5 values of variable: {}'.format(len(a),
                                                                                                   len(journals), a[0:5])
            sys.exit(error_msg)

    # # print list of values for each variable in input file
    # print_possible_values_of_wiley_variables()


    t_apc_value = re.compile(r'[0-9,]+')
    # parse information for each journal and add to Orpheus

    counter = 0
    for j in journals[1:]:
        counter += 1
        logger.info('---------{} Working on journal {}'.format(counter, j))
        j_parser = generic_parser.NodeParser(name=j, publisher='Wiley', source=WILEY_SOURCE_ID,
                                             publisher_node_id=p_parser.node_id)
        j_parser.oa_status = oa_status_dict[oa_stata.values[counter]]
        logger.debug('OA status: {}'.format(j_parser.oa_status))

        # obtain issn from romeo; identify romeo_publisher and its node in Orpheus
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

        # Parsing gold policy info
        licence_options_raw = gold_licences.values[counter]
        logger.debug('licence_options_raw: {}'.format(licence_options_raw))
        apc_raw_str = apcs.values[counter]
        logger.debug('apc_raw_str: {}'.format(apc_raw_str))
        if (j_parser.oa_status == 'SUBSCRIPTION') and (licence_options_raw == '--') and (apc_raw_str == '--'):
            has_gold_policy = False
        else:
            has_gold_policy = True
            logger.debug('has_gold_policy: {}'.format(has_gold_policy))
            gp = generic_parser.GoldPolicyInstance()
            gp.node = preferred_node_id
            gp.source = WILEY_SOURCE_ID
            gp.licence_options = licence_choices_dict[licence_options_raw]
            logger.debug('gp.licence_options: {}'.format(gp.licence_options))
            if apc_raw_str in ['', '--']:
                pass
            elif apc_raw_str in ['No APC', 'Inquire Directly ', 'Contact journal', '$50 per PU', 'waived 2016-18',
                                 '$1,800 for research article $900 for technical report']:
                gp.apc_note = apc_raw_str
                gp.apc_value_min = 900
                gp.apc_value_max = 1800
            elif apc_raw_str.strip() == '3500':
                gp.apc_currency = 'USD'
                gp.apc_value_min = 3500
                gp.apc_value_max = 3500
            else:
                m_apc_value = t_apc_value.search(apc_raw_str)
                gp.apc_value_min = int(m_apc_value.group().replace(',',''))
                gp.apc_value_max = gp.apc_value_min
                if '$' in apc_raw_str:
                    gp.apc_currency = 'USD'
                elif '€' in apc_raw_str:
                    gp.apc_currency = 'EUR'
                else:
                    logger.warning('Currency of APC {} could not be recognised. Journal {}'.format(apc_raw_str, j))
            logger.debug('gp.apc_currency: {}'.format(gp.apc_currency))
            logger.debug('gp.apc_value_min: {}'.format(gp.apc_value_min))
            logger.debug('gp.apc_value_max: {}'.format(gp.apc_value_max))

        # parsing preprint policy
        preprint_embargo_raw = preprint_embargos.values[counter]
        if preprint_embargo_raw in ['Refer to copyright or contact managing editor', '--']:
            has_preprint_policy = False
        else:
            has_preprint_policy = True
            preprint_policy = generic_parser.GreenPolicyInstance()
            preprint_policy.node = preferred_node_id
            preprint_policy.outlet = [WEBSITE_ID, INST_REPO_ID, SUBJ_REPO_ID]
            preprint_policy.version = [PREPRINT_ID]
            preprint_policy.version_embargo_months = 0
            preprint_policy.version_green_licence = CUSTOM_ID
            preprint_policy.source = WILEY_SOURCE_ID
            preprint_policy.verbatim = preprint_embargo_raw
            logger.debug('has_preprint_policy: {}'.format(has_preprint_policy))
            logger.debug('preprint_policy.verbatim: {}'.format(preprint_policy.verbatim))

        # parsing AM policy
        am_embargo_raw = am_embargos.values[counter]
        logger.debug('am_embargo_raw: {}'.format(am_embargo_raw))
        if am_embargo_raw.strip() in ['Refer to copyright or contact managing editor', '--', 'Refer to copyright',
                                      'Does not publish unsolicited manuscripts']:
            has_am_policy = False
        else:
            has_am_policy = True
            am_policy = generic_parser.GreenPolicyInstance()
            am_policy.node = preferred_node_id
            am_policy.outlet = [WEBSITE_ID, INST_REPO_ID, SUBJ_REPO_ID]
            am_policy.version = [AM_ID]
            am_policy.version_green_licence = CUSTOM_ID
            am_policy.source = WILEY_SOURCE_ID
            am_policy.verbatim = am_embargo_raw.strip()
            if am_embargo_raw.strip() in ['Final version on publication']:
                am_policy.version = [VOR_ID]
                am_policy.version_embargo_months = 0
            elif am_embargo_raw.strip() in ['On submission']:
                am_policy.version_embargo_months = 0
            elif am_embargo_raw.strip() in ['6mo embargo']:
                am_policy.version_embargo_months = 6
            elif am_embargo_raw.strip() in ['Institutional repository after 6 month embargo']:
                am_policy.outlet = [INST_REPO_ID]
                am_policy.version_embargo_months = 6
            elif am_embargo_raw.strip() in ['12mo embargo', '12 months', '12-24mo embargo']:
                am_policy.version_embargo_months = 12
            elif am_embargo_raw.strip() in ['18mo embargo']:
                am_policy.version_embargo_months = 18
            elif am_embargo_raw.strip() in ['24mo embargo']:
                am_policy.version_embargo_months = 24
            elif am_embargo_raw.strip() in ['Not permitted', 'Fully Open Access']:
                am_policy.deposit_allowed = False
            else:
                logger.error('Failed to parse embargo info ({}) for journal {}'.format(am_embargo_raw, j))
            logger.debug('has_am_policy: {}'.format(has_am_policy))
            logger.debug('am_policy.verbatim: {}'.format(am_policy.verbatim))
            logger.debug('am_policy.version_embargo_months: {}'.format(am_policy.version_embargo_months))

        # Attach policies to preferred name node
        logger.debug('Calling j_parser.PolicyMatcher(j_parser, policy_type=oa_status).match()')
        j_parser.PolicyMatcher(j_parser, policy_type='oa_status').match()
        if has_gold_policy:
            logger.debug("Calling j_parser.PolicyMatcher(j_parser, policy_type='gold').match(**gp.as_dict())")
            j_parser.PolicyMatcher(j_parser, policy_type='gold').match(**gp.as_dict())
        if has_preprint_policy:
            logger.debug('Calling j_parser.server_data_match_green_policy(**preprint_policy.as_dict())')
            j_parser.PolicyMatcher(j_parser, policy_type='green').match(**preprint_policy.as_dict())
        if has_am_policy:
            logger.debug('Calling j_parser.server_data_match_green_policy(**am_policy.as_dict())')
            j_parser.PolicyMatcher(j_parser, policy_type='green').match(**am_policy.as_dict())

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf', defaults={'logfilename':'wiley_parser.log'})
    logger = logging.getLogger('wiley_parser')
    main()