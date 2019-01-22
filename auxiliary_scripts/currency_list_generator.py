import logging
import pycountry

# USD = 'USD'
# GBP = 'GBP'
# EUR = 'EUR'
# CHF = 'CHF'
#
# (GBP, 'GBP - British Pound (£)'),
# (EUR, 'EUR - Euro (€)'),
# (USD, 'USD - United States Dollar ($)'),
# (CHF, 'CHF - Swiss Franc (SFr.)')

list_1 = ''
list_2 = ''
for i in iter(pycountry.countries):
    try:
        currency = pycountry.currencies.get(numeric=i.numeric)
        list_1 += "{} = '{}'\n".format(currency.alpha_3, currency.alpha_3)
        list_2 += "    ({}, '{} - {}'),\n".format(currency.alpha_3, currency.alpha_3, currency.name)
    except KeyError:
        logging.warning('Currency for "{}" not in database'.format(i.name))

with open('currency_list.txt', 'w') as f:
    f.write(list_1)
    f.write(list_2)