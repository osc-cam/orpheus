import generic_parser

# Common sources
doaj_source_parser = generic_parser.SourceParser('DOAJ', url='https://doaj.org/')
DOAJ_SOURCE_ID = doaj_source_parser.match_or_create_source()

# Licence ids in Orpheus
cc0_parser = generic_parser.LicenceParser(short_name='CC0', long_name='Public domain',
                                          url='https://creativecommons.org/publicdomain/zero/1.0/')
ccbynd_parser = generic_parser.LicenceParser(short_name='CC BY-ND',
                                             long_name='Creative Commons Attribution-NoDerivatives',
                                             url='https://creativecommons.org/licenses/by-nd/4.0/')
ccbysa_parser = generic_parser.LicenceParser(short_name='CC BY-SA',
                                             long_name='Creative Commons Attribution-ShareAlike',
                                             url='https://creativecommons.org/licenses/by-sa/4.0/')
ccby_parser = generic_parser.LicenceParser(short_name='CC BY')
ccbync_parser = generic_parser.LicenceParser(short_name='CC BY-NC')
ccbyncnd_parser = generic_parser.LicenceParser(short_name='CC BY-NC-ND')
ccbyncsa_parser = generic_parser.LicenceParser(short_name='CC BY-NC-SA')
custom_parser = generic_parser.LicenceParser(short_name='Custom')
CC0_ID = cc0_parser.match_or_create_licence()
CCBYND_ID = ccbynd_parser.match_or_create_licence()
CCBYSA_ID = ccbysa_parser.match_or_create_licence()
CCBY_ID = ccby_parser.match_licence()
CCBYNC_ID = ccbync_parser.match_licence()
CCBYNCND_ID = ccbyncnd_parser.match_licence()
CCBYNCSA_ID = ccbyncsa_parser.match_licence()
CUSTOM_ID = custom_parser.match_licence()

# Version ids in Orpheus
preprint_parser = generic_parser.VersionParser(short_name='Preprint')
am_parser = generic_parser.VersionParser(short_name='AM')
vor_parser = generic_parser.VersionParser(short_name='VoR')
PREPRINT_ID = preprint_parser.match_version()
AM_ID = am_parser.match_version()
VOR_ID = vor_parser.match_version()

# Outlet ids in Orpheus
commercial_parser = generic_parser.OutletParser(name='Commercial repository')
inst_repo_parser = generic_parser.OutletParser(name='Non-commercial institutional repository')
pubmed_parser = generic_parser.OutletParser(name='PubMed Central')
social_parser = generic_parser.OutletParser(name='Social platforms (Research Gate, etc)')
subj_repo_parser = generic_parser.OutletParser(name='Non-commercial subject repository')
website_parser = generic_parser.OutletParser(name='Personal website')
COMMERCIAL_ID = commercial_parser.match_outlet()
INST_REPO_ID = inst_repo_parser.match_outlet()
PUBMED_ID = pubmed_parser.match_outlet()
SOCIAL_ID = social_parser.match_outlet()
SUBJ_REPO_ID = subj_repo_parser.match_outlet()
WEBSITE_ID = website_parser.match_outlet()