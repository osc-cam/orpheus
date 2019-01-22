import csv
import logging
import logging.config
import os
import sys
import urllib.request
from bs4 import BeautifulSoup

# import generic_parser
# import orpheus_client

# setup django API
os.environ['PYTHONPATH'] = "/home/asartori/orpheus"
sys.path.append("/home/asartori/orpheus")
os.environ['DJANGO_SETTINGS_MODULE'] = 'orpheus.settings'
# import django
# from django.db.models import Q, Avg, Count
# django.setup()
#
# import policies.models as models

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# create logger
logging.config.fileConfig('logging.conf', defaults={'logfilename':'test.log'})
logger = logging.getLogger('test')
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

get_journals4id(409)


def diff_imported_dataset_and_node_table():
    '''
    Compares and outputs differences between an external dataset and a node table csv exported from Orpheus
    :return:
    '''
    inputfile1 = '/home/asartori/orpheus/connectors/db_snapshots/t_and_f_journal_list.csv' # external dataset (csv)
    inputfile2 = '/home/asartori/orpheus/connectors/psql_dev_scripts/node_table.csv' # Orpheus node table
    outputfile = '/home/asartori/Desktop/Doaj_parser_logs/t_and_f_node_diff.csv'
    outputfile1 = '/home/asartori/Desktop/Doaj_parser_logs/publisher_diff.csv'
    column_label_journal_name = 'Journal title'
    column_label_journal_name = 'Journal Name'
    column_label_journal_name = 'Journal name'
    column_label_publisher_name = 'Publisher'
    column_label_publisher_name = None
    with open(inputfile1, encoding='utf-8') as csvfile1, open(inputfile2, encoding='utf-8') as csvfile2, \
            open(outputfile, 'w') as output, open(outputfile1, 'w') as output1:
        reader1 = csv.DictReader(csvfile1)
        reader2 = csv.DictReader(csvfile2)
        node_names_1 = []
        publisher_names_1 = []
        node_names_2 = []
        publisher_names_2 = []
        for row in reader2:
            if row['name_status'] == 'PRIMARY':
                if row['type'] == 'JOURNAL':
                    node_names_2.append(row['name'].lower().strip())
            if row['type'] == 'PUBLISHER':
                publisher_names_2.append(row['name'].lower().strip())
        writer = csv.writer(output)
        writer.writerow(['The following journals are only present in {}'.format(inputfile1)])
        writer1 = csv.writer(output1)
        writer1.writerow(['The following publishers are only present in {}'.format(inputfile1)])
        for row in reader1:
            j_title = row[column_label_journal_name].lower().strip()
            node_names_1.append(j_title)
            if column_label_publisher_name:
                publisher = row[column_label_publisher_name].lower().strip()
            else:
                publisher = None
            if publisher and (publisher not in publisher_names_1):
                publisher_names_1.append(publisher)
                if (publisher not in publisher_names_2) and ('{} (publisher)'.format(publisher) not in publisher_names_2):
                    writer1.writerow([publisher])
            if (j_title not in node_names_2):# and ('{} ({})'.format(j_title, publisher) not in node_names_2):
                print(j_title)
                writer.writerow([j_title])
        print('DOAJ dataset contains {} unique names in column `Journal title`'.format(len(node_names_1)))
        print('DOAJ dataset contains {} unique names in column `Publisher`'.format(len(publisher_names_1)))
        # for n in node_names_1:
        #     if n not in node_names_2:
        #         writer.writerow([n])
        # writer.writerow(['The following preferred names are only present in {}'.format(inputfile2)])
        # for n in node_names_2:
        #     if n not in node_names_1:
        #         writer.writerow([n])

def diff_node_tables():
    inputfile1 = '/home/asartori/Desktop/Doaj_parser_logs/2018-08-02/node_table_latest.csv'
    inputfile2 = '/home/asartori/Desktop/Doaj_parser_logs/not_all_currencies_supported/node_table.csv'
    outputfile = 'node_diff.csv'
    with open(inputfile1, encoding='utf-8') as csvfile1, open(inputfile2, encoding='utf-8') as csvfile2,\
                    open(outputfile, 'w') as output:
        reader1 = csv.DictReader(csvfile1)
        reader2 = csv.DictReader(csvfile2)
        node_names_1 = []
        node_names_2 = []
        for row in reader1:
            node_names_1.append(row['name'].lower())
        for row in reader2:
            node_names_2.append(row['name'].lower())
        writer = csv.writer(output)
        writer.writerow(['The following nodes are only present in {}'.format(inputfile1)])
        for n in node_names_1:
            if n not in node_names_2:
                writer.writerow([n])
        writer.writerow(['The following nodes are only present in {}'.format(inputfile2)])
        for n in node_names_2:
            if n not in node_names_1:
                writer.writerow([n])

def check_issns():
    nodes = models.Node.objects.all()
    o_issn = []
    for n in nodes:
        if n.issn and (n.issn not in o_issn):
            o_issn.append(n.issn)
        if n.eissn and (n.eissn not in o_issn):
            o_issn.append(n.eissn)

    doaj_issn = []
    inputfile = os.path.join(BASE_DIR, 'datasets', 'doaj_20180719_1330_utf8.csv')
    with open(inputfile, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            issn = row['Journal ISSN (print version)'].strip()
            eissn = row['Journal EISSN (online version)'].strip()

            if issn and (issn not in doaj_issn):
                doaj_issn.append(issn)
            if eissn and (eissn not in doaj_issn):
                doaj_issn.append(eissn)

    missing_issn = []
    for i in doaj_issn:
        if i not in o_issn:
            missing_issn.append(i)

    with open('doaj_missing_issns.log', 'w') as f:
        for m in missing_issn:
            f.write('{}\n'.format(m))

# diff_imported_dataset_and_node_table()

# q = models.Node.objects.filter(parent=155998)
# print(len(q))
# for n in q:
#     print(n.name, n.id)

# # A few gold policies were linked to publisher nodes; print a list of those nodes
# publisher_gold = models.Node.objects.filter(type='PUBLISHER').annotate(gold_count=Count(
#         'gold_policies')).filter(gold_count__gte=1)
# for p in publisher_gold:
#     print(p.name, p.id)


# No issns are missing

# 2 preferred names (rows in doaj csv) appear to be missing; check what ISSNs are missing
# check_issns()

# p = generic_parser.NodeParser(name='Abant Izzet Baysal University')
# #p = generic_parser.NodeParser(name='Krause & Pachernegg GmbH')
# #p = generic_parser.NodeParser(name='Chinese Anti-Cancer Association; Chinese Antituberculosis Association')
# p.match_or_create_node()


# # Problem at database level
# INSERT INTO policies_node (name, name_status, type, created, updated, vetted) VALUES ('Abant Izzet Baysal University', 'PRIMARY', 'PUBLISHER', '2018-07-24 00:20:25.627218+01', '2018-07-24 00:20:25.627218+01', 'TRUE');
# ERROR:  duplicate key value violates unique constraint "node_name_index"
# DETAIL:  Key (lower(name::text))=(abant izzet baysal university) already exists.

# # Yet, strangely, the database reports 0 rows containing that name
# orpheus_staging=# SELECT * from policies_node WHERE name = 'Abant Izzet Baysal University'; id | name | name_status | type | url | issn | created | updated | parent_id | source_id | synonym_of_id | vetted | vetted_date | eissn | romeo_id
# ----+------+-------------+------+-----+------+---------+---------+-----------+-----------+---------------+--------+-------------+-------+----------
# (0 rows)