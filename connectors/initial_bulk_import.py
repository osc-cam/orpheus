'''
Note on how to load fixtures saved with django-admin dumpdata:

export PYTHONPATH=/home/asartori/orpheus
export DJANGO_SETTINGS_MODULE=orpheus.settings
django-admin loaddata /home/asartori/Dropbox/OSC/orpheus-backups/romeo.json
'''

import cup_parser
import doaj_parser
import elsevier_apc_parser
import elsevier_embargos_parser
import oup_parser
import t_and_f_parser
import romeo_parser
import wiley_parser
import wos_parser
import logging

def main():
    t_and_f_parser.main()
    elsevier_embargos_parser.main() # OK. Updated 09/08/2018
    elsevier_apc_parser.main()
    wiley_parser.main()
    cup_parser.main()
    oup_parser.main()
    doaj_parser.main()
    romeo_parser.main()
    # wos_parser.main()

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf', defaults={'logfilename':'initial_bulk_import.log'})
    logger = logging.getLogger('initial_bulk_import')
    main()