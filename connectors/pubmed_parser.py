import os
import re
import generic_parser
import orpheus_client

'''
This connector parses journal info from file J_Entrez.txt, which corresponds to the dataset 
"PubMed and NCBI Molecular Biology Database Journals", downloaded from 
https://www.ncbi.nlm.nih.gov/books/NBK3827/table/pubmedhelp.T.journal_lists/


The version currently used here was downloaded on 19 Feb 2018 
'''

ID_FOR_DATASET_IN_ORPHEUS_SOURCES_TABLE = 4

t_jname = re.compile('JournalTitle: .+')
t_issn = re.compile('ISSN \(Print\): .+')
t_eissn = re.compile('ISSN \(Online\): .+')
sep = '--------------------------------------------------------'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
inputfile = os.path.join(BASE_DIR, 'datasets', 'J_Entrez.txt')
with open(inputfile) as f:
    input_data = f.read()
journals = input_data.split(sep)
j_counter = 0
created = []
skipped = []
errors = []
for j in journals:
    if j.strip():
        j_counter += 1
        issn = ''
        eissn = ''
        m_jname = t_jname.search(j)
        m_issn = t_issn.search(j)
        m_eissn = t_eissn.search(j)
        jname = m_jname.group().replace('JournalTitle:', '').strip()
        if m_issn:
            issn = m_issn.group().replace('ISSN (Print):', '').strip()
        if m_eissn:
            eissn = m_eissn.group().replace('ISSN (Online):', '').strip()
        j_parser = generic_parser.parser(jname=jname, issn=issn, eissn=eissn)
        node_id, node_record, match_type = j_parser.match2node()
        print('Processing:', j_counter, jname, issn, eissn, node_id)
        if not node_id:
            r = orpheus_client.create_node(jname, 'PRIMARY', 'JOURNAL', ID_FOR_DATASET_IN_ORPHEUS_SOURCES_TABLE,
                                           **{'issn': issn, 'eissn': eissn})
            if r.ok:
                created.append(jname)
            else:
                errors.append([jname, r.text])
        else:
            skipped.append(jname)
    else:
        pass

print('Finished processing dataset.')
print(len(created), 'new Orpheus nodes were created.')
print(len(skipped), 'journals matched existing nodes in Orpheus. They were skipped.')
print(len(errors), 'entries resulted in errors. They are:')
for e in errors:
    print(e[0], e[1])