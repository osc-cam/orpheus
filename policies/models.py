from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, EmailValidator
from django.utils.translation import ugettext_lazy
from django.urls import reverse  # Used to generate URLs by reversing the URL patterns
from django.core import serializers
import pytz
import re
import sys
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from itertools import chain

EXPIRY_DATE = date.today() + relativedelta(months=-6)
EXPIRY_TIME = pytz.UTC.localize(datetime.now() + relativedelta(months=-6))

# region currency codes
AWG = 'AWG'
ALL = 'ALL'
AED = 'AED'
ARS = 'ARS'
AMD = 'AMD'
AUD = 'AUD'
BIF = 'BIF'
BDT = 'BDT'
BHD = 'BHD'
BSD = 'BSD'
BZD = 'BZD'
BMD = 'BMD'
BOB = 'BOB'
BBD = 'BBD'
BND = 'BND'
BRL = 'BRL'
BTN = 'BTN'
BWP = 'BWP'
CAD = 'CAD'
CHF = 'CHF'
CLP = 'CLP'
CNY = 'CNY'
COP = 'COP'
KMF = 'KMF'
CVE = 'CVE'
CRC = 'CRC'
CUP = 'CUP'
KYD = 'KYD'
CZK = 'CZK'
DJF = 'DJF'
DKK = 'DKK'
DOP = 'DOP'
DZD = 'DZD'
EGP = 'EGP'
ERN = 'ERN'
EUR = 'EUR'
FJD = 'FJD'
FKP = 'FKP'
GBP = 'GBP'
GIP = 'GIP'
GNF = 'GNF'
GMD = 'GMD'
GTQ = 'GTQ'
GYD = 'GYD'
HKD = 'HKD'
HNL = 'HNL'
HRK = 'HRK'
HTG = 'HTG'
HUF = 'HUF'
IDR = 'IDR'
INR = 'INR'
IRR = 'IRR'
IQD = 'IQD'
ISK = 'ISK'
ILS = 'ILS'
JMD = 'JMD'
JOD = 'JOD'
JPY = 'JPY'
KZT = 'KZT'
KES = 'KES'
KGS = 'KGS'
KHR = 'KHR'
KRW = 'KRW'
KWD = 'KWD'
LAK = 'LAK'
LBP = 'LBP'
LRD = 'LRD'
LYD = 'LYD'
LKR = 'LKR'
LSL = 'LSL'
MOP = 'MOP'
MAD = 'MAD'
MDL = 'MDL'
MVR = 'MVR'
MXN = 'MXN'
MKD = 'MKD'
MMK = 'MMK'
MNT = 'MNT'
MRO = 'MRO'
MUR = 'MUR'
MWK = 'MWK'
MYR = 'MYR'
NAD = 'NAD'
NGN = 'NGN'
NIO = 'NIO'
NOK = 'NOK'
NPR = 'NPR'
NZD = 'NZD'
OMR = 'OMR'
PKR = 'PKR'
PLN = 'PLN'
PEN = 'PEN'
PHP = 'PHP'
PGK = 'PGK'
KPW = 'KPW'
PYG = 'PYG'
QAR = 'QAR'
RON = 'RON'
RSD = 'RSD'
RUB = 'RUB'
RWF = 'RWF'
SAR = 'SAR'
SGD = 'SGD'
SHP = 'SHP'
SBD = 'SBD'
SLL = 'SLL'
SVC = 'SVC'
SOS = 'SOS'
SSP = 'SSP'
STD = 'STD'
SEK = 'SEK'
SZL = 'SZL'
SCR = 'SCR'
SYP = 'SYP'
THB = 'THB'
TOP = 'TOP'
TTD = 'TTD'
TND = 'TND'
TRY = 'TRY'
TWD = 'TWD'
TZS = 'TZS'
UAH = 'UAH'
UGX = 'UGX'
UYU = 'UYU'
USD = 'USD'
UZS = 'UZS'
VEF = 'VEF'
VND = 'VND'
VUV = 'VUV'
XAF = 'XAF'
WST = 'WST'
ZAR = 'ZAR'
# endregion

APC_CURRENCY_CHOICES = (
    (GBP, 'GBP - British Pound (£)'),
    (EUR, 'EUR - Euro (€)'),
    (USD, 'USD - United States Dollar ($)'),
    (CHF, 'CHF - Swiss Franc (SFr.)'),

    (AWG, 'AWG - Aruban Florin'),
    (ALL, 'ALL - Lek'),
    (AED, 'AED - UAE Dirham'),
    (ARS, 'ARS - Argentine Peso'),
    (AMD, 'AMD - Armenian Dram'),
    (AUD, 'AUD - Australian Dollar'),
    (BIF, 'BIF - Burundi Franc'),
    (BDT, 'BDT - Taka'),
    (BHD, 'BHD - Bahraini Dinar'),
    (BRL, 'BRL - Brazilian Real'),
    (BSD, 'BSD - Bahamian Dollar'),
    (BZD, 'BZD - Belize Dollar'),
    (BMD, 'BMD - Bermudian Dollar'),
    (BOB, 'BOB - Boliviano'),
    (BBD, 'BBD - Barbados Dollar'),
    (BND, 'BND - Brunei Dollar'),
    (BTN, 'BTN - Ngultrum'),
    (BWP, 'BWP - Pula'),
    (CAD, 'CAD - Canadian Dollar'),
    (CLP, 'CLP - Chilean Peso'),
    (CNY, 'CNY - Yuan Renminbi'),
    (COP, 'COP - Colombian Peso'),
    (KMF, 'KMF - Comoro Franc'),
    (CVE, 'CVE - Cabo Verde Escudo'),
    (CRC, 'CRC - Costa Rican Colon'),
    (CUP, 'CUP - Cuban Peso'),
    (KYD, 'KYD - Cayman Islands Dollar'),
    (CZK, 'CZK - Czech Koruna'),
    (DJF, 'DJF - Djibouti Franc'),
    (DKK, 'DKK - Danish Krone'),
    (DOP, 'DOP - Dominican Peso'),
    (DZD, 'DZD - Algerian Dinar'),
    (EGP, 'EGP - Egyptian Pound'),
    (ERN, 'ERN - Nakfa'),
    (FJD, 'FJD - Fiji Dollar'),
    (FKP, 'FKP - Falkland Islands Pound'),
    (GIP, 'GIP - Gibraltar Pound'),
    (GNF, 'GNF - Guinea Franc'),
    (GMD, 'GMD - Dalasi'),
    (GTQ, 'GTQ - Quetzal'),
    (GYD, 'GYD - Guyana Dollar'),
    (HKD, 'HKD - Hong Kong Dollar'),
    (HNL, 'HNL - Lempira'),
    (HRK, 'HRK - Kuna'),
    (HTG, 'HTG - Gourde'),
    (HUF, 'HUF - Forint'),
    (IDR, 'IDR - Rupiah'),
    (INR, 'INR - Indian Rupee'),
    (IRR, 'IRR - Iranian Rial'),
    (IQD, 'IQD - Iraqi Dinar'),
    (ISK, 'ISK - Iceland Krona'),
    (ILS, 'ILS - New Israeli Sheqel'),
    (JMD, 'JMD - Jamaican Dollar'),
    (JOD, 'JOD - Jordanian Dinar'),
    (JPY, 'JPY - Yen'),
    (KZT, 'KZT - Tenge'),
    (KES, 'KES - Kenyan Shilling'),
    (KGS, 'KGS - Som'),
    (KHR, 'KHR - Riel'),
    (KRW, 'KRW - Won'),
    (KWD, 'KWD - Kuwaiti Dinar'),
    (LAK, 'LAK - Kip'),
    (LBP, 'LBP - Lebanese Pound'),
    (LRD, 'LRD - Liberian Dollar'),
    (LYD, 'LYD - Libyan Dinar'),
    (LKR, 'LKR - Sri Lanka Rupee'),
    (LSL, 'LSL - Loti'),
    (MOP, 'MOP - Pataca'),
    (MAD, 'MAD - Moroccan Dirham'),
    (MDL, 'MDL - Moldovan Leu'),
    (MVR, 'MVR - Rufiyaa'),
    (MXN, 'MXN - Mexican Peso'),
    (MKD, 'MKD - Denar'),
    (MMK, 'MMK - Kyat'),
    (MNT, 'MNT - Tugrik'),
    (MRO, 'MRO - Ouguiya'),
    (MUR, 'MUR - Mauritius Rupee'),
    (MWK, 'MWK - Malawi Kwacha'),
    (MYR, 'MYR - Malaysian Ringgit'),
    (NAD, 'NAD - Namibia Dollar'),
    (NGN, 'NGN - Naira'),
    (NIO, 'NIO - Cordoba Oro'),
    (NOK, 'NOK - Norwegian Krone'),
    (NPR, 'NPR - Nepalese Rupee'),
    (NZD, 'NZD - New Zealand Dollar'),
    (OMR, 'OMR - Rial Omani'),
    (PKR, 'PKR - Pakistan Rupee'),
    (PLN, 'PLN - Polish złoty'),
    (PEN, 'PEN - Sol'),
    (PHP, 'PHP - Philippine Peso'),
    (PGK, 'PGK - Kina'),
    (KPW, 'KPW - North Korean Won'),
    (PYG, 'PYG - Guarani'),
    (QAR, 'QAR - Qatari Rial'),
    (RON, 'RON - Romanian Leu'),
    (RSD, 'RSD - Serbian dinar'),
    (RUB, 'RUB - Russian Ruble'),
    (RWF, 'RWF - Rwanda Franc'),
    (SAR, 'SAR - Saudi Riyal'),
    (SGD, 'SGD - Singapore Dollar'),
    (SHP, 'SHP - Saint Helena Pound'),
    (SBD, 'SBD - Solomon Islands Dollar'),
    (SLL, 'SLL - Leone'),
    (SVC, 'SVC - El Salvador Colon'),
    (SOS, 'SOS - Somali Shilling'),
    (SSP, 'SSP - South Sudanese Pound'),
    (STD, 'STD - Dobra'),
    (SEK, 'SEK - Swedish Krona'),
    (SZL, 'SZL - Lilangeni'),
    (SCR, 'SCR - Seychelles Rupee'),
    (SYP, 'SYP - Syrian Pound'),
    (THB, 'THB - Baht'),
    (TOP, 'TOP - Pa’anga'),
    (TTD, 'TTD - Trinidad and Tobago Dollar'),
    (TND, 'TND - Tunisian Dinar'),
    (TRY, 'TRY - Turkish Lira'),
    (TWD, 'TWD - Taiwan New Dollar'),
    (TZS, 'TZS - Tanzanian Shilling'),
    (UAH, 'UAH - Hryvnia'),
    (UGX, 'UGX - Uganda Shilling'),
    (UYU, 'UYU - Peso Uruguayo'),
    (UZS, 'UZS - Uzbekistan Sum'),
    (VEF, 'VEF - Venezuelan Bolívar'),
    (VND, 'VND - Dong'),
    (VUV, 'VUV - Vatu'),
    (XAF, 'XAF - Central African CFA Franc'),
    (WST, 'WST - Tala'),
    (ZAR, 'ZAR - Rand'),
)

# region custom validators
##This custom validate_issn validator is no longer used.
# Left here for now only to keep migrations working
def validate_issn(value):
    t = re.compile('[0-9]{4,4}-[0-9]{3,3}[0-9X]')
    m = t.match(value)
    if not m:
        raise ValidationError(
            ugettext_lazy('%(value)s is not a issn in the format 0000-0000'),
            params={'value': value},
        )

def node_name_validator(value):
    if '  ' in value:
        raise ValidationError(
            ugettext_lazy('Please remove double spaces from %(value)s'),
            params={'value': value},
        )
# endregion

class Node(models.Model):
    '''
    A node can be a Publisher, Conference or Journal depending on the value of node_type
    '''
    name = models.CharField(max_length=200, unique=True, validators=[node_name_validator])
    # Case-insensitive uniqueness of the name field was enforced in the database backend,
    # via a unique index; the index was created by migration 0003, using migrations.RunSQL, as
    # shown below (see https://stackoverflow.com/questions/7773341/case-insensitive-unique-model-fields-in-django and
    # http://django.readthedocs.io/en/1.11.x/ref/migration-operations.html#django.db.migrations.operations.RunSQL for details):
    # migrations.RunSQL("CREATE UNIQUE INDEX node_name_index ON policies_node(lower(name));")

    ACCEPTED = 'PRIMARY'
    UNACCEPTED = 'SYNONYM'
    UNCERTAIN = 'UNCERTAIN'
    NODE_NAME_STATUS_CHOICES = (
        (ACCEPTED, 'Preferred name'),
        (UNACCEPTED, 'Synonym'),
        (UNCERTAIN, 'Uncertain'),
    )
    name_status = models.CharField(max_length=20, choices=NODE_NAME_STATUS_CHOICES, blank=False, default=ACCEPTED)

    CONFERENCE = 'CONFERENCE'
    IMPRINT = 'IMPRINT'
    JOURNAL = 'JOURNAL'
    PUBLISHER = 'PUBLISHER'
    NODE_TYPE_CHOICES = (
        (CONFERENCE, 'Conference'),
        (JOURNAL, 'Journal'),
        (PUBLISHER, 'Publisher'),
    )
    type = models.CharField(max_length=20, choices=NODE_TYPE_CHOICES,
                            default=JOURNAL
                            )
    url = models.URLField(max_length=600, blank=True, null=True)
    issn = models.CharField(max_length=10, blank=True, null=True,
                            # unique=True, #Decided not to use unique here because that would prevent an issn to be repeated in the synonyms
                            help_text="Please use the format: <em>0000-0000</em>.",
                            validators=[
                                RegexValidator('[0-9]{4,4}-[0-9]{3,3}[0-9X]', 'Please enter a issn in the format 0000-0000')])

    eissn = models.CharField(max_length=10, blank=True, null=True,
                            help_text="Please use the format: <em>0000-0000</em>.",
                            verbose_name='e-issn',
                            validators=[
                                RegexValidator('[0-9]{4,4}-[0-9]{3,3}[0-9X]', 'Please enter a issn in the format 0000-0000')])

    epmc_url = models.URLField(blank=True, null=True)
    romeo_id = models.IntegerField(blank=True, null=True)
    synonym_of = models.ForeignKey('self', on_delete=models.PROTECT, related_name='synonyms', blank=True, null=True,
                                   limit_choices_to={
                                       # 'type': 'self'.type, #https://stackoverflow.com/questions/232435/how-do-i-restrict-foreign-keys-choices-to-related-objects-only-in-django
                                       'name_status': ACCEPTED}
                                   )
    parent = models.ForeignKey('self', on_delete=models.PROTECT, related_name='children', blank=True, null=True,
                               help_text="Please select publisher of journal, imprint or conference",
                               verbose_name="Publisher",
                               limit_choices_to={
                                   'type': PUBLISHER,
                                   'name_status': ACCEPTED}
                               )
    source = models.ForeignKey('Source', on_delete=models.PROTECT, blank=True, null=True)
    vetted = models.BooleanField(default=True)
    vetted_date = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (self.name)

        # Below is an example from
        # https://stackoverflow.com/questions/15422606/django-model-email-field-unique-if-not-null-blank
        # showing how to redefine the model's save method to enable unique=True only when not-blank
        # See also: https://docs.djangoproject.com/en/1.8/topics/db/models/#overriding-model-methods

        # def save(self, *args, **kwargs):
        #     self.issn = self.issn.lower().strip()  # Hopefully reduces junk to ""
        #     if self.issn == "":
        #         self.issn = None
        #     super(Node, self).save(*args, **kwargs) # Call the "real" save() method.

    def clean(self):
        # get rid of tabs, newlines, etc
        t = re.compile('[\t\n\r\f\v]')
        for c in t.findall(self.name):
            self.name.replace(c, ' ')
        # get rid of double spaces
        t = re.compile(' {2}')
        for c in t.findall(self.name):
            self.name.replace(c, ' ')
        # get rid of leading or trailing spaces
        self.name.strip()
        if (self.name_status == 'SYNONYM') and not self.synonym_of:
            raise ValidationError('"Synonym of" field must not be blank when "Name status" is "Alternate representation"')
        elif (self.name_status == 'PRIMARY') and self.synonym_of:
            raise ValidationError('"Synonym of" field must be blank for preferred names')

        # if (self.name_status == 'SYNONYM'):
        #     if not self.type == self.synonym_of.type:
        #         raise ValidationError()

    def save(self, *args, **kwargs):
        self.clean()
        if (self.name_status == 'SYNONYM') and not self.synonym_of:
            raise ValidationError('"Synonym of" field must not be blank "Name status" is "Alternate representation"')
        elif (self.name_status == 'PRIMARY') and self.synonym_of:
            raise ValidationError('"Synonym of" field must be blank for preferred names')
        else:
            super(Node, self).save(*args, **kwargs)  # Call the "real" save() method.

    def get_absolute_url(self):
        """
        Returns the url to access a particular node instance.
        """
        return reverse('policies:detail', args=[str(self.id)])

    def get_deletion_requests(self):
        '''
        Fetch related deletion requests
        '''
        return Note.objects.filter(node=self.id).filter(deletion_request=True)

    def get_invalid_policies(self):
        '''
        Fetches superseded policies related to this node and concatenates them into a list
        '''
        oastata = OaStatus.objects.filter(node=self.id).filter(superseded=True)
        gold = GoldPolicy.objects.filter(node=self.id).filter(superseded=True)
        green = GreenPolicy.objects.filter(node=self.id).filter(superseded=True)
        retro = RetrospectiveOaPolicy.objects.filter(node=self.id).filter(superseded=True)
        return list(chain(oastata, gold, green, retro))

    def get_romeo_url(self):
        """
        Returns the url of this node in Sherpa RoMEO.
        """
        romeo_url = None
        if self.type == 'PUBLISHER':
            if self.romeo_id:
                romeo_url = 'http://www.sherpa.ac.uk/romeo/search.php?id={}&la=en&fIDnum=' \
                            '|&mode=simple&format=full'.format(self.romeo_id)
        else:
            if self.issn:
                romeo_url = 'http://www.sherpa.ac.uk/romeo/issn/{}/'.format(self.issn)
            elif self.eissn:
                romeo_url = 'http://www.sherpa.ac.uk/romeo/issn/{}/'.format(self.eissn)
            else:
                romeo_url = 'http://www.sherpa.ac.uk/romeo/search.php?qtype=EXACT&jtitle={}&la=en&fIDnum=' \
                            '|&mode=simple'.format(self.name)

        return romeo_url

    def get_doaj_url(self):
        """
        Returns the url of this node in DOAJ.
        """
        doaj_url = None
        if self.type == 'JOURNAL':
            if self.issn:
                doaj_url = 'https://doaj.org/toc/{}/'.format(self.issn)
            elif self.eissn:
                doaj_url = 'https://doaj.org/toc/{}/'.format(self.eissn)

        return doaj_url



    def get_synonyms(self):
        if self.name_status == 'PRIMARY':
            return Node.objects.filter(synonym_of=self.id)
        elif self.synonym_of:
            return Node.objects.filter(synonym_of=self.synonym_of.id)
        else:
            sys.exit('{} is not a preferred name or a synonym'.format(self))

    def get_parent_oa_stata(self):
        '''
        Fetches OA stata associated with the parent node.
        '''
        if self.parent:
            return OaStatus.objects.filter(node=self.parent.id)
        else:
            return OaStatus.objects.none()

    def get_parent_gold_policies(self):
        '''
        Fetches gold policies associated with the parent node.
        '''
        if self.parent:
            return GoldPolicy.objects.filter(node=self.parent.id)
        else:
            return GoldPolicy.objects.none()

    def get_parent_green_policies(self):
        '''
        Fetches green policies associated with the parent node.
        '''
        if self.parent:
            return GreenPolicy.objects.filter(node=self.parent.id)
        else:
            return GreenPolicy.objects.none()

    def get_parent_epmc_policies(self):
        '''
        Fetches epmc policies associated with the parent node.
        '''
        if self.parent:
            return Epmc.objects.filter(node=self.parent.id)
        else:
            return Epmc.objects.none()

    def get_parent_deal_policies(self):
        '''
        Fetches deals and discounts associated with the parent node.
        '''
        if self.parent:
            return Deal.objects.filter(node=self.parent.id)
        else:
            return Deal.objects.none()

    def get_parent_contacts(self):
        '''
        Fetches contacts associated with the parent node.
        '''
        if self.parent:
            return Contact.objects.filter(node=self.parent.id)
        else:
            return Contact.objects.none()

    def get_synonyms_parents_oa_stata(self):
        '''
        Fetches OA stata associated with the parents of all synonyms.
        '''
        oa_stata = []
        for s in self.get_synonyms():
            oa_stata.append(OaStatus.objects.filter(node=s.parent.id))
        return oa_stata

    def get_synonyms_parents_green_policies(self):
        '''
        Fetches green policies associated with the parents of all synonyms.
        '''
        policies = []
        for s in self.get_synonyms():
            policies.append(GreenPolicy.objects.filter(node=s.parent.id))
        return policies

    def get_synonyms_parents_gold_policy(self):
        '''
        Fetches gold policies associated with the parents of all synonyms.
        '''
        policies = []
        for s in self.get_synonyms():
            policies.append(GoldPolicy.objects.filter(node=s.parent.id))
        return policies

    def get_synonyms_oa_stata(self):
        '''
        Fetches OA stata associated with synonyms. Returns a list of querysets, one for each synonym.
        '''
        oa_stata = []
        for s in self.get_synonyms():
            oa_stata.append(OaStatus.objects.filter(node=s.id))
        return oa_stata

    def get_synonyms_green_policies(self):
        '''
        Fetches green policies associated with synonyms. Returns a list of querysets, one for each synonym.
        '''
        green_policies = []
        for s in self.get_synonyms():
            green_policies.append(GreenPolicy.objects.filter(node=s.id))
        return green_policies

    def get_synonyms_gold_policy(self):
        '''
        Fetches gold policies associated with synonyms. Returns a list of querysets, one for each synonym.
        '''
        policies = []
        for s in self.get_synonyms():
            policies.append(GoldPolicy.objects.filter(node=s.id))
        return policies

    def get_preferred_name_oa_status(self):
        '''
        Fetches oa status associated with the preferred name
        :return: queryset
        '''
        if self.name_status == 'PRIMARY':
            return OaStatus.objects.filter(node=self.id)
        elif self.synonym_of:
            return OaStatus.objects.filter(node=self.synonym_of.id)
        else:
            sys.exit('{} is not a preferred name or a synonym'.format(self))

    def get_preferred_name_publisher(self):
        '''
        Fetches publisher name associated with the preferred name
        :return: queryset
        '''
        if self.name_status == 'PRIMARY':
            return self.parent.name
        elif self.synonym_of:
            return self.synonym_of.parent.name
        else:
            sys.exit('{} is not a preferred name or a synonym'.format(self))

    def get_preferred_name_green_policies(self):
        '''
        Fetches green policies associated with the preferred name
        :return: A queryset of policies
        '''
        if self.name_status == 'PRIMARY':
            return GreenPolicy.objects.filter(node=self.id)
        elif self.synonym_of:
            return GreenPolicy.objects.filter(node=self.synonym_of.id)
        else:
            sys.exit('{} is not a preferred name or a synonym'.format(self))

    def get_preferred_name_gold_policy(self):
        '''
        Fetches gold policies associated with the preferred name
        :return: A queryset of policies
        '''
        if self.name_status == 'PRIMARY':
            return GoldPolicy.objects.filter(node=self.id)
        elif self.synonym_of:
            return GoldPolicy.objects.filter(node=self.synonym_of.id)
        else:
            sys.exit('{} is not a preferred name or a synonym'.format(self))

    # region Cambridge
    @property
    def apollo_am_embargo_months(self):
        '''
        Used by the API. Embargo period Apollo should set on AMs
        :return: 'indefinite', 'unknown' or an integer converted to string (e.g. '6', '12') specifying the number
            of months.
        '''
        if self.most_reliable_oa_status:
            oa = self.most_reliable_oa_status['oa_status']
            if oa == 'FULLY_OA':
                return 'indefinite'
        gp = self.most_reliable_green_policies_for_ir
        if gp['AM']:
            if gp['AM']['deposit_allowed']:
                if gp['AM']['version_embargo_months'] != None:
                    return '{}'.format(gp['AM']['version_embargo_months'])
            else:
                return 'indefinite'

        return 'unknown'

    @property
    def apollo_vor_embargo_months(self):
        '''
        Used by the API. Embargo period Apollo should set on VoRs
        :return: 'disallowed', 'unknown' or an integer converted to string (e.g. '6', '12') specifying the number
            of months.
        '''
        if self.most_reliable_oa_status:
            oa = self.most_reliable_oa_status['oa_status']
            if oa == 'FULLY_OA':
                return '0'
        gp = self.most_reliable_green_policies_for_ir
        if gp['VoR']:
            if gp['VoR']['deposit_allowed']:
                if gp['VoR']['version_embargo_months'] != None:
                    return '{}'.format(gp['VoR']['version_embargo_months'])
            else:
                return 'disallowed'

        return 'unknown'

    @property
    def zd_publisher(self):
        '''
        Used by the API. Human-friendly publisher name
        :return:
        '''
        return re.sub('\[\d+\]', '', self.get_preferred_name_publisher().replace('(Publisher)', '')).strip()

    @property
    def zd_green_allowed_version(self):
        '''
        Used by the API. Value for Zendesk green allowed version field
        :return: Zendesk tag 'oa_journal_conference', 'version_of_record', 'aam', 'pre_print' or 'no_version_allowed'
        '''
        if self.most_reliable_oa_status:
            oa = self.most_reliable_oa_status['oa_status']
            if oa == 'FULLY_OA':
                return oa.replace('FULLY_OA', 'oa_journal_conference')
        gp = self.most_reliable_green_policies_for_ir
        if gp['VoR'] or gp['AM'] or gp['Preprint']:
            if gp['VoR'] and gp['VoR']['deposit_allowed']:
                return 'version_of_record'
            elif gp['AM'] and gp['AM']['deposit_allowed']:
                return 'aam'
            elif gp['Preprint'] and gp['Preprint']['deposit_allowed']:
                return 'pre_print'
            else:
                return 'no_version_allowed'
        return None

    @property
    def zd_embargo_duration(self):
        '''
        Used by the API. Value for Zendesk embargo duration field
        :return: None/null value for OA journals or unknown; otherwise, Zendesk tag that represents the closest match
                to the integer embargo_months in Orpheus (possible values: '0_months', '2_months', '3_months',
                '6_months', '12_months', '18_months', '24_months', '36_months', '48_months', '5_years')
        '''
        def zd_embargo_tag(embargo_int):
            zd_embargo_options = [0,2,3,6,9,12,18,24,36,48,60]
            closest_zd_option = min(zd_embargo_options, key=lambda x:abs(x-embargo_int))
            if closest_zd_option == 60:
                return '5_years'
            else:
                return '{}_months'.format(closest_zd_option)

        if self.most_reliable_oa_status:
            oa = self.most_reliable_oa_status['oa_status']
            if oa == 'FULLY_OA':
                return None
        gp = self.most_reliable_green_policies_for_ir
        if gp['VoR'] or gp['AM'] or gp['Preprint']:
            if gp['VoR'] and gp['VoR']['deposit_allowed'] and (gp['VoR']['version_embargo_months'] != None):
                return zd_embargo_tag(gp['VoR']['version_embargo_months'])
            elif gp['AM'] and gp['AM']['deposit_allowed'] and (gp['AM']['version_embargo_months'] != None):
                return zd_embargo_tag(gp['AM']['version_embargo_months'])
            elif gp['Preprint'] and gp['Preprint']['deposit_allowed'] and gp['Preprint']['version_embargo_months']:
                return zd_embargo_tag(gp['Preprint']['version_embargo_months'])
            else:
                return None

    @property
    def zd_green_licence(self):
        '''
        Used by the API. Value for Zendesk green licence field
        :return: None/null value for OA journals or unknown; otherwise, Zendesk tag 'cc-by', 'custom_licence',
                'unclear_licence', 'cc_by_nc', 'cc_by_nc_nd', 'cc_by_nc_sa', 'cc_by_nd', 'cc_by_sa'
        '''
        def zd_licence_tag(licence):
            if licence in ["CC BY", "CC0"]:
                return 'cc-by'
            elif licence == "Custom":
                return 'custom_licence'
            elif licence == "Unclear":
                return 'unclear_licence'
            else:
                return re.sub('[ \-]', '_', licence.lower())

        if self.most_reliable_oa_status:
            oa = self.most_reliable_oa_status['oa_status']
            if oa == 'FULLY_OA':
                return None
        gp = self.most_reliable_green_policies_for_ir
        if gp['VoR'] or gp['AM'] or gp['Preprint']:
            if gp['VoR'] and gp['VoR']['deposit_allowed']:
                return zd_licence_tag(gp['VoR']['version_green_licence'])
            elif gp['AM'] and gp['AM']['deposit_allowed']:
                return zd_licence_tag(gp['AM']['version_green_licence'])
            elif gp['Preprint'] and gp['Preprint']['deposit_allowed']:
                return zd_licence_tag(gp['Preprint']['version_green_licence'])
            else:
                return None

    @property
    def zd_journal_oa_status(self):
        '''
        Used by the API. Value for Zendesk "#Journal OA status" field
        :return: 'journal_oa_status_hybrid', 'journal_oa_status_open_access', 'journal_oa_status_subscription'
        '''
        if self.most_reliable_oa_status:
            oa = self.most_reliable_oa_status['oa_status']
            if oa == 'FULLY_OA':
                return 'journal_oa_status_open_access'
            elif oa == 'HYBRID':
                return 'journal_oa_status_hybrid'
            elif oa == 'SUBSCRIPTION':
                return 'journal_oa_status_subscription'
        return None

    @property
    def zd_apc_range(self):
        '''
        Used by the API. Human-friendly APC range
        :return: A string representing a journal's range of article processing charges in the
        format '<currency> <minimum amount charged>[-<maximum amount charged if different from miminum>]'
        (examples '$ 2000', '£ 1000-2000', 'BRL 500')
        '''
        cur_symb = {
            'GBP': '£',
            'USD': '$',
            'EUR': '€',
        }

        gold = self.most_reliable_gold_policy
        if gold:
            try:
                currency = cur_symb[gold["apc_currency"]]
            except:
                currency = gold["apc_currency"]
            apc_min = gold["apc_value_min"]
            apc_max = gold["apc_value_max"]
            if currency and (apc_min or apc_max):
                if apc_min and apc_max and (apc_min != apc_max):
                    return '{}{}-{}'.format(currency, int(round(apc_min)), int(round(apc_max)))
                elif apc_min:
                    return '{}{}'.format(currency, int(round(apc_min)))
                else:
                    return '{}{}'.format(currency, int(round(apc_max)))
        return None

    def zd_commitment_guidance(self):
        '''
        Used by the API. Human-friendly financial commitment
        :return:
        '''

        cur_symb = {
            'GBP': '£',
            'USD': '$',
            'EUR': '€',
        }

        gold = self.most_reliable_gold_policy
        if gold:
            currency = gold["apc_currency"]
            if currency == 'GBP':
                rate = 1.2
            elif currency == 'USD':
                rate = 0.95
            elif currency == 'EUR':
                rate = 1.1
            else:
                rate = 1
            apc_min = gold["apc_value_min"]
            apc_max = gold["apc_value_max"]
            if currency and (apc_min or apc_max):
                if apc_max:
                    commit = int(round(float(apc_max) * rate))

                else:
                    commit = int(round(float(apc_min) * rate))
                return '{} ({})'.format(commit, commit / 2)
        return None



    @property
    def zd_gold_licence_options(self):
        '''
        Used by the API.
        :return: A list of ZD tags representing licences available to authors paying for immediate (gold) Open Access.
                Possible values are: 'gold_cc_by', 'gold_cc_by_nc', 'gold_cc_by_nc_nd', 'gold_cc_by_nc_sa',
                'gold_cc_by_nd', 'gold_cc_by_sa', 'gold_cc0', 'gold_custom', 'gold_unclear'
        '''
        def zd_gold_licence_tag(licence):
            return 'gold_{}'.format(re.sub('[ \-]', '_', licence.lower()))

        gold = self.most_reliable_gold_policy
        if gold:
            if gold['licence_options']:
                return [zd_gold_licence_tag(l) for l in gold['licence_options']]
        return None
    # endregion

    @property
    def most_reliable_oa_status(self):
        '''
        Used by the API. Calculated field containing the most reliable OA status of a journal
        '''

        def process_policy_queryset(queryset, output_dict, pass_counter, restrict_to_vetted=False):
            def pass_counter_str(int):
                if int in [1, 2]:
                    return 'preferred name'
                elif int in [3, 4]:
                    return 'synonym'
                elif int in [5, 6]:
                    return 'parent (publisher)'
                elif int in [7, 8]:
                    return 'synonym parent (publisher)'

            for q in queryset:
                if (q.problematic == False) and (q.superseded == False):
                    if (q.vetted == True) or (restrict_to_vetted == False):
                        if output_dict == None: # Avoid overwriting a more reliable policy
                            output_dict = {
                                    "id": q.id,
                                    "source": q.source.description,
                                    "oa_status": q.oa_status,
                                    "verbatim": q.verbatim,
                                    "problematic": q.problematic,
                                    "vetted": q.vetted,
                                    "vetted_date": q.vetted_date,
                                    "last_checked": q.last_checked,
                                    "superseded": q.superseded,
                                    "superseded_date": q.superseded_date,
                                    "created": q.created,
                                    "updated": q.updated,
                                    "node": q.node.id,
                                    "provenance": pass_counter_str(pass_counter)
                                    }

            return output_dict

        output_policy = None

        pol = self.get_preferred_name_oa_status()
        if pol:  # try first to obtain data from vetted policies directly linked to preferred name of node
            output_policy = process_policy_queryset(pol, output_policy, 1, restrict_to_vetted=True)
        if output_policy == None:  # if output_policy still null, try unvetted
            output_policy = process_policy_queryset(pol, output_policy, 2)
        if output_policy == None:  # if output_policy still null, try synonyms (vetted, then any)
            synonym_pol = self.get_synonyms_oa_stata()
            if synonym_pol:
                for queryset in synonym_pol: # vetted
                    output_policy = process_policy_queryset(queryset, output_policy, 3, restrict_to_vetted=True)
                if output_policy == None:
                    for queryset in synonym_pol: # any
                        output_policy = process_policy_queryset(queryset, output_policy, 4)
        if output_policy == None:  # if output_policy still null, try direct parent (vetted, then any)
            parent_pol = self.get_parent_oa_stata()
            if parent_pol: #vetted
                output_policy = process_policy_queryset(parent_pol, output_policy, 5, restrict_to_vetted=True)
                if output_policy == None: # any
                    output_policy = process_policy_queryset(parent_pol, output_policy, 6)
        ### PARENTS OF SYNONYMS BLOCK BELOW NOT WORKING; NOT SURE WHY; COMMENTING IT OUT FOR NOW
        # if output_policy == None:  # if output_policy still null, try parents of synonyms (vetted, then any)
        #     synonym_parent_pol = self.get_synonyms_parents_oa_stata()
        #     if synonym_parent_pol: #vetted
        #         output_policy = process_policy_queryset(synonym_parent_pol, output_policy, 7, restrict_to_vetted=True)
        #         print('Returning:', output_policy)
        #         if output_policy == None: # any
        #             output_policy = process_policy_queryset(synonym_parent_pol, output_policy, 8)

        return output_policy

    @property
    def most_reliable_gold_policy(self):
        '''
        Used by the API. Calculated field containing the most reliable gold policy of a journal
        '''

        def process_policy_queryset(queryset, output_dict, pass_counter, restrict_to_vetted=False):
            def pass_counter_str(int):
                if int in [1, 2]:
                    return 'preferred name'
                elif int in [3, 4]:
                    return 'synonym'
                elif int in [5, 6]:
                    return 'parent (publisher)'
                elif int in [7, 8]:
                    return 'synonym parent (publisher)'

            for q in queryset:
                if (q.problematic == False) and (q.superseded == False):
                    if (q.vetted == True) or (restrict_to_vetted == False):
                        if output_dict == None:  # Avoid overwriting a more reliable policy
                            default_licence_str = ''
                            if q.default_licence:
                                default_licence_str = q.default_licence.short_name
                            output_dict = {
                                "id": q.id,
                                "source": q.source.description,
                                "apc_currency": q.apc_currency,
                                "apc_value_min": q.apc_value_min,
                                "apc_value_max": q.apc_value_max,
                                "apc_note": q.apc_note,
                                "licence_options": [str(l) for l in q.licence_options.all()], # https://stackoverflow.com/a/34475243
                                "default_licence": default_licence_str,
                                "verbatim": q.verbatim,
                                "problematic": q.problematic,
                                "vetted": q.vetted,
                                "vetted_date": q.vetted_date,
                                "last_checked": q.last_checked,
                                "superseded": q.superseded,
                                "superseded_date": q.superseded_date,
                                "created": q.created,
                                "updated": q.updated,
                                "node": q.node.id,
                                "provenance": pass_counter_str(pass_counter)
                            }

            return output_dict

        output_policy = None

        pol = self.get_preferred_name_gold_policy()
        if pol:  # try first to obtain data from vetted policies directly linked to preferred name of node
            output_policy = process_policy_queryset(pol, output_policy, 1, restrict_to_vetted=True)
        if output_policy == None:  # if output_policy still null, try unvetted
            output_policy = process_policy_queryset(pol, output_policy, 2)
        if output_policy == None:  # if output_policy still null, try synonyms (vetted, then any)
            synonym_pol = self.get_synonyms_gold_policy()
            if synonym_pol:
                for queryset in synonym_pol:  # vetted
                    output_policy = process_policy_queryset(queryset, output_policy, 3, restrict_to_vetted=True)
                if output_policy == None:
                    for queryset in synonym_pol:  # any
                        output_policy = process_policy_queryset(queryset, output_policy, 4)
        if output_policy == None:  # if output_policy still null, try direct parent (vetted, then any)
            parent_pol = self.get_parent_gold_policies()
            if parent_pol:  # vetted
                output_policy = process_policy_queryset(parent_pol, output_policy, 5, restrict_to_vetted=True)
                if output_policy == None:  # any
                    output_policy = process_policy_queryset(parent_pol, output_policy, 6)
        ### PARENTS OF SYNONYMS BLOCK BELOW NOT WORKING; NOT SURE WHY; COMMENTING IT OUT FOR NOW
        # if output_policy == None:  # if output_policy still null, try parents of synonyms (vetted, then any)
        #     synonym_parent_pol = self.get_synonyms_parents_gold_policy()
        #     if synonym_parent_pol: #vetted
        #         output_policy = process_policy_queryset(synonym_parent_pol, output_policy, 7, restrict_to_vetted=True)
        #         print('Returning:', output_policy)
        #         if output_policy == None: # any
        #             output_policy = process_policy_queryset(synonym_parent_pol, output_policy, 8)

        return output_policy

    @property
    def most_reliable_green_policies_for_ir(self):
        '''
        Used by the API. Calculated field containing the most reliable embargo period for AAMs and VoRs
        self-archiving in non-commercial institutional repositories
        '''

        def process_policy_queryset(queryset, output_dict, pass_counter, restrict_to_vetted=False):
            def pass_counter_str(int):
                if int in [1, 2]:
                    return 'preferred name'
                elif int in [3, 4]:
                    return 'synonym'
                elif int in [5, 6]:
                    return 'parent (publisher)'
                elif int in [7, 8]:
                    return 'synonym parent (publisher)'

            for g in queryset:
                versions = g.get_versions()
                if 'Non-commercial institutional repository' in g.get_outlets():
                    if ('AM' in versions) or ('VoR' in versions):
                        if (g.problematic == False) and (g.superseded == False):
                            if (g.vetted == True) or (restrict_to_vetted == False):
                                for v in ['Preprint', 'AM', 'VoR']:
                                    if v in versions:
                                        if output_dict[v] == None: # Avoid overwriting more reliable embargos
                                            output_dict[v] = {
                                                "id": g.id,
                                                # "outlet": g.outlet,
                                                # "version": g.version,
                                                "version_green_licence": str(g.version_green_licence),
                                                "source": g.source.description,
                                                "deposit_allowed": g.deposit_allowed,
                                                "version_embargo_months": g.version_embargo_months,
                                                "version_note": g.version_note,
                                                "verbatim": g.verbatim,
                                                "problematic": g.problematic,
                                                "vetted": g.vetted,
                                                "vetted_date": g.vetted_date,
                                                "last_checked": g.last_checked,
                                                "superseded": g.superseded,
                                                "superseded_date": g.superseded_date,
                                                "created": g.created,
                                                "updated": g.updated,
                                                "node": g.node.id,
                                                "provenance": pass_counter_str(pass_counter)
                                                }

            return output_dict

        embargos = {
            'Preprint' : None,
            'AM' : None,
            'VoR' : None
        }

        green = self.get_preferred_name_green_policies()
        if green: # try first to obtain data from vetted policies directly linked to preferred name of node
            embargos = process_policy_queryset(green, embargos, 1, restrict_to_vetted=True)
        if (embargos['AM'] == None) or (embargos['VoR'] == None): # if AAM or VoR embargos still null, try unvetted
            embargos = process_policy_queryset(green, embargos, 2)
        if (embargos['AM'] == None) or (embargos['VoR'] == None): # if AAM or VoR embargos still null, try synonyms
            synonym_green = self.get_synonyms_green_policies()
            for queryset in synonym_green:
                embargos = process_policy_queryset(queryset, embargos, 3, restrict_to_vetted=True)
                if (embargos['AM'] == None) or (embargos['VoR'] == None):
                    embargos = process_policy_queryset(queryset, embargos, 4)
        if (embargos['AM'] == None) or (embargos['VoR'] == None): # if AAM or VoR embargos still null, try parent
            parent_green = self.get_parent_green_policies()
            if parent_green:
                embargos = process_policy_queryset(parent_green, embargos, 5, restrict_to_vetted=True)
            if (embargos['AM'] == None) or (embargos['VoR'] == None):
                embargos = process_policy_queryset(parent_green, embargos, 6)
        ### PARENTS OF SYNONYMS BLOCK BELOW NOT WORKING; NOT SURE WHY; COMMENTING IT OUT FOR NOW
        # if (embargos['AAM'] == None) or (embargos['VoR'] == None):  # if output_policy still null, try parents of synonyms (vetted, then any)
        #     synonym_parent_pol = self.get_synonyms_parents_green_policies()
        #     if synonym_parent_pol: #vetted
        #         embargos = process_policy_queryset(synonym_parent_pol, embargos, 7, restrict_to_vetted=True)
        #         if (embargos['AAM'] == None) or (embargos['VoR'] == None): # any
        #             embargos = process_policy_queryset(synonym_parent_pol, embargos, 8)

        return embargos

    @property
    def romeo_url(self):
        return self.get_romeo_url()

    class Meta:
        ordering = ('name',)


# region Tag classes
class Version(models.Model):
    '''
    Tag-like model to populate version field in GreenPolicy model:
    https://stackoverflow.com/questions/13318128/django-tag-model-design
    '''
    short_name = models.CharField(max_length=30)
    long_name = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return (self.short_name)

    class Meta:
        ordering = ('short_name',)

class Licence(models.Model):
    '''
    Tag-like model to populate licence options field in other models
    '''
    short_name = models.CharField(max_length=50)
    long_name = models.CharField(max_length=200, blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return (self.short_name)

    class Meta:
        ordering = ('short_name',)


class Outlet(models.Model):
    '''
    Tag-like model to populate self-archiving outlet type in policy models:
    '''
    name = models.CharField(max_length=50)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return (self.name)

    class Meta:
        ordering = ('name',)

# class Output(models.Model):
#     '''
#     Tag-like model to populate type of output (journals, books) policy applies to
#     '''
#     name = models.CharField(max_length=50)
#
#     def __str__(self):
#         return (self.name)
#
#     class Meta:
#         ordering = ('name',)

class Responsibility(models.Model):
    '''
    Tag-like model to populate contacts
    '''
    name = models.CharField(max_length=50)

    def __str__(self):
        return (self.name)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = "Responsibilities"
# endregion

class Contact(models.Model):
    '''
    Contacts (e-mail addresses) used in other tables
    '''
    email = models.CharField(max_length=100, unique=True, validators=[EmailValidator])
    name = models.CharField(max_length=200, blank=True, null=True)
    responsibilities = models.ManyToManyField(Responsibility, blank=True)
    active = models.BooleanField(default=True)

    node = models.ForeignKey(Node, on_delete=models.PROTECT, related_name='contacts')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return self.email

    def get_absolute_url(self):
        """
        Returns the url to access the particular node instance this policy is attached to.
        """
        return reverse('policies:detail', args=[str(self.node.id)])


class Source(models.Model):
    '''
    Sources of information entered in other tables
    '''
    description = models.TextField()
    url = models.URLField(max_length=600, blank=True, null=True, unique=True)

    PUBLICATION = 'PUBLICATION'
    DATASET = 'DATASET'
    WEBSITE = 'WEBSITE'
    SOURCE_TYPE_CHOICES = (
        (DATASET, 'Dataset'),
        (PUBLICATION, 'Publication'),
        (WEBSITE, 'Website'),
    )
    type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)

    file = models.FileField(upload_to='sources', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (self.description)

    def save(self, *args, **kwargs):
        if self.url:               #To avoid AttributeError: 'NoneType' object has no attribute 'lower'
            self.url = self.url.strip()  # Hopefully reduces junk to ""
        if self.url == "":
            self.url = None
        super(Source, self).save(*args, **kwargs)  # Call the "real" save() method.

    def get_absolute_url(self):
        """
        Returns the url to access a particular source instance.
        """
        return reverse('policies:source_detail', args=[str(self.id)])

class OaStatus(models.Model):
    '''
    Indicates if a journal/publisher is fully OA, hybrid or subscription-only.
    Can be used to link DOAJ data.
    '''
    node = models.ForeignKey(Node, on_delete=models.PROTECT, limit_choices_to={'name_status': 'PRIMARY'},
                             related_name='oa_stata')

    FULLY_OA = 'FULLY_OA'
    HYBRID = 'HYBRID'
    SUBSCRIPTION = 'SUBSCRIPTION'
    OA_STATUS_CHOICES = (
        (FULLY_OA, 'Open Access Journal/Publisher'),
        (HYBRID, 'Hybrid Journal/Publisher'),
        (SUBSCRIPTION, 'Subscription Journal/Publisher')
    )
    oa_status = models.CharField(max_length=20, choices=OA_STATUS_CHOICES)

    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    verbatim = models.TextField(blank=True, null=True,
                            help_text="Please copy and paste here the paragraph(s) from source containing the OA status statement",
                            )
    problematic = models.BooleanField(default=False,
                                      help_text="Use this field to mark ambiguous/unclear policies requiring discussion/revision"
                                      )
    vetted = models.BooleanField(default=True)
    vetted_date = models.DateField(blank=True, null=True)
    last_checked = models.DateField(blank=True, null=True)
    superseded = models.BooleanField(default=False)
    superseded_date = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        #return '%s (%s)' % (self.node, self.node.get_type_display())
        return '%s: %s (%s)' % (self.node, self.get_oa_status_display(), self.source)

    def get_absolute_url(self):
        """
        Returns the url to access the particular node instance this policy is attached to.
        """
        return reverse('policies:detail', args=[str(self.node.id)])

    def get_deletion_requests(self):
        '''
        Fetch related deletion requests
        '''
        return Note.objects.filter(oastatus=self.id).filter(deletion_request=True)

    def checked_recently(self):
        return self.last_checked > EXPIRY_DATE

    def updated_recently(self):
        return self.updated > EXPIRY_TIME

    def created_recently(self):
        return self.created > EXPIRY_TIME

    def vetted_recently(self):
        return self.vetted_date > EXPIRY_DATE

    class Meta:
        verbose_name_plural = "Oa status"


class GoldPolicy(models.Model):
    '''
    APC value and licence options of a node, as documented by a source.
    '''
    node = models.ForeignKey(Node, on_delete=models.PROTECT, limit_choices_to={'name_status': 'PRIMARY'},
                             related_name='gold_policies')

    apc_currency = models.CharField(max_length=10, choices=APC_CURRENCY_CHOICES, blank=True, null=True)
    apc_value_min = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    apc_value_max = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    apc_note = models.CharField(max_length=255, blank=True, null=True)
    licence_options = models.ManyToManyField(Licence, related_name='journals', blank=True)
    default_licence = models.ForeignKey(Licence, on_delete=models.PROTECT, blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    verbatim = models.TextField(blank=True, null=True,
                                help_text="Please copy and paste here the paragraph(s) from source stating this gold policy",
                                )
    problematic = models.BooleanField(default=False,
                                      help_text="Use this field to mark ambiguous/unclear policies requiring discussion/revision"
                                      )
    vetted = models.BooleanField(default=True)
    vetted_date = models.DateField(blank=True, null=True)
    last_checked = models.DateField(blank=True, null=True)
    superseded = models.BooleanField(default=False)
    superseded_date = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.apc_value_min != self.apc_value_max:
            return '{}: {} {}--{} ({})'.format(self.node, self.apc_currency, self.apc_value_min, self.apc_value_max,
                                               self.source)
        else:
            return '{}: {} {} ({})'.format(self.node, self.apc_currency, self.apc_value_min, self.source)

    def get_absolute_url(self):
        """
        Returns the url to access the particular node instance this gold policy is attached to.
        """
        return reverse('policies:detail', args=[str(self.node.id)])

    # def get_absolute_url(self):
    #     return reverse('policies:gold_policy_update', args=[str(self.id)])

    def get_notes(self):
        '''
        Fetch related notes that are not deletion requests
        '''
        return Note.objects.filter(goldpolicy=self.id).filter(deletion_request=False)

    def get_deletion_requests(self):
        '''
        Fetch related deletion requests
        '''
        return Note.objects.filter(goldpolicy=self.id).filter(deletion_request=True)

    def checked_recently(self):
        return self.last_checked > EXPIRY_DATE

    def updated_recently(self):
        return self.updated > EXPIRY_TIME

    def created_recently(self):
        return self.created > EXPIRY_TIME

    def vetted_recently(self):
        return self.vetted_date > EXPIRY_DATE

    class Meta:
        verbose_name_plural = "Gold policies"
        ordering = ['superseded', '-vetted', '-updated']


class GreenPolicy(models.Model):
    '''
    Embargo on self-archiving of a node, as documented by a source.
    '''
    node = models.ForeignKey(Node, on_delete=models.PROTECT, limit_choices_to={'name_status': 'PRIMARY'},
                             related_name='green_policies') # related_name is required for the API to work properly
    # NOT SURE I WANT TO IMPLEMENT OUTPUT YET
    # output = models.ManyToManyField(Output, verbose_name='outputs covered by green policy',
    #                                 help_text='Please select all output types this policy applies to.')
    outlet = models.ManyToManyField(Outlet, related_name='journals', verbose_name='self-archiving outlets',
                                    help_text='Please select all self-archiving outlets this policy applies to.')
    version = models.ManyToManyField(Version, verbose_name='versions covered by green policy',
                                     help_text='Please select all versions this policy applies to')
    deposit_allowed = models.BooleanField(default=True)
    version_embargo_months = models.IntegerField(blank=True, null=True)
    version_green_licence = models.ForeignKey(Licence, on_delete=models.PROTECT, blank=True, null=True)
    version_note = models.CharField(max_length=255, blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    verbatim = models.TextField(blank=True, null=True,
                                help_text="Please copy and paste here the paragraph(s) from source stating this green policy",
                                )
    problematic = models.BooleanField(default=False,
                                      help_text="Use this field to mark ambiguous/unclear policies requiring discussion/revision"
                                      )
    vetted = models.BooleanField(default=True)
    vetted_date = models.DateField(blank=True, null=True)
    last_checked = models.DateField(blank=True, null=True)
    superseded = models.BooleanField(default=False)
    superseded_date = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s: %s (%s)' % (self.node, ', '.join(version.__str__() for version in self.version.all()), self.source) # for loop for version required because it is a ManyToManyField

    def short_name(self):
        versions = ', '.join(version.__str__() for version in self.version.all())
        outlets = ', '.join(outlet.__str__().replace('Non-commercial ','') for outlet in self.outlet.all())
        outlets = (outlets[:40] + '...') if len(outlets) > 40 else outlets
        return '{} ({})'.format(versions, outlets)
        # truncated_source = (self.source.__str__()[:30] + '...') if len(self.source.__str__()) > 30 else self.source
        # return '{} ({})'.format(', '.join(version.__str__() for version in self.version.all()), truncated_source)

    def get_absolute_url(self):
        """
        Returns the url to access the particular node instance this policy is attached to.
        """
        return reverse('policies:detail', args=[str(self.node.id)])

    def get_outlets(self):
        '''
        Returns a queryset of outlets covered by this policy
        '''
        outlets = []
        for o in self.outlet.all():
            outlets.append(str(o))
        return outlets

    def get_versions(self):
        '''
        Returns a queryset of versions covered by this policy
        '''
        versions = []
        for v in self.version.all():
            versions.append(str(v))
        return versions

    def checked_recently(self):
        return self.last_checked > EXPIRY_DATE

    def updated_recently(self):
        return self.updated > EXPIRY_TIME

    def created_recently(self):
        return self.created > EXPIRY_TIME

    def vetted_recently(self):
        return self.vetted_date > EXPIRY_DATE

    class Meta:
        verbose_name_plural = "Green policies"

class Epmc(models.Model):
    '''
    Details of EPMC participation of a node, as documented by a source. See
    https://www.ncbi.nlm.nih.gov/pmc/pub/pubinfo/#pmcagree for more details on PMC participation

    See https://europepmc.org/journalList for bulk population of this model
    '''

    node = models.ForeignKey(Node, on_delete=models.PROTECT, limit_choices_to={'name_status': 'PRIMARY'},
                             related_name='epmc_policies') # related_name is required for the API to work properly

    FULL = 'FULL'
    NIH = 'NIH'
    NONE = 'NONE'
    PARTICIPATION_CHOICES = (
        (FULL, 'Full'),
        (NIH, 'NIH Portfolio'),
        (NONE, 'No EPMC participation')
    )
    participation_level = models.CharField(max_length=10, choices=PARTICIPATION_CHOICES)
    embargo_months = models.IntegerField(blank=True, null=True)

    ALL = 'ALL'
    SOME = 'SOME'
    NO = 'NO'
    OA_CHOICES = (
        (ALL, 'All'),
        (SOME, 'Some'),
        (NO, 'No'),
    )
    open_licence = models.CharField(max_length=10, choices=OA_CHOICES)

    NO_NEW = 'NO_NEW'
    PREDECESSOR = 'PREDECESSOR'
    NOW_SELECT = 'NOW_SELECT'
    STATUS_CHOICES = (
        (NO_NEW, 'No new content'),
        (PREDECESSOR, 'Predecessor'),
        (NOW_SELECT, 'Now select')
    )
    deposit_status = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, null=True)

    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    vetted = models.BooleanField(default=True)
    vetted_date = models.DateField(blank=True, null=True)
    last_checked = models.DateField(blank=True, null=True)
    superseded = models.BooleanField(default=False)
    superseded_date = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_participation_level_display()

    def checked_recently(self):
        return self.last_checked > EXPIRY_DATE

    def updated_recently(self):
        return self.updated > EXPIRY_TIME

    def created_recently(self):
        return self.created > EXPIRY_TIME

    def vetted_recently(self):
        return self.vetted_date > EXPIRY_DATE

class RetrospectiveOaPolicy(models.Model):
    '''
    Details of retrospective OA policy of a node, as documented by a source.
    '''
    node = models.ForeignKey(Node, on_delete=models.PROTECT, limit_choices_to={'name_status': 'PRIMARY'})
    available = models.BooleanField()
    deadline = models.CharField(max_length=600, blank=True, null=True)
    details = models.TextField
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    vetted = models.BooleanField(default=True)
    vetted_date = models.DateField(blank=True, null=True)
    last_checked = models.DateField(blank=True, null=True)
    superseded = models.BooleanField(default=False)
    superseded_date = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (self.retrospective_oa_available)

    def get_absolute_url(self):
        """
        Returns the url to access the particular node instance this policy is attached to.
        """
        return reverse('policies:detail', args=[str(self.node.id)])

    def checked_recently(self):
        return self.last_checked > EXPIRY_DATE

    def updated_recently(self):
        return self.updated > EXPIRY_TIME

    def created_recently(self):
        return self.created > EXPIRY_TIME

    def vetted_recently(self):
        return self.vetted_date > EXPIRY_DATE

    class Meta:
        verbose_name_plural = "Retrospective OA policies"


### DEV NOTES: INSTEAD OF USING THE MODEL BELOW (NOTE) FOR DELETION REQUESTS, IT IS PROBABLY BETTER
### TO ADD DELETION_REQUEST AND REASON FIELDS TO EVERY MODEL WE WANT TO SUPPORT DELETION REQUESTS

class Note(models.Model):
    '''
    Miscelaneous notes about other classes

    If deletion_request == True, note is a Request from editors/curators/users for superusers
    to delete a particular object.
    '''
    text = models.TextField()
    deletion_request = models.NullBooleanField()
    node = models.ForeignKey(Node, on_delete=models.CASCADE, blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, blank=True, null=True, related_name='source_notes')
    oastatus = models.ForeignKey(OaStatus, on_delete=models.CASCADE, related_name='oa_status_notes', blank=True,
                                   null=True)
    goldpolicy = models.ForeignKey(GoldPolicy, on_delete=models.CASCADE, related_name='gold_policy_notes', blank=True,
                                   null=True)
    greenpolicy = models.ForeignKey(GreenPolicy, on_delete=models.CASCADE, related_name='green_policy_notes', blank=True,
                                   null=True)
    retrospective_oa_policy = models.ForeignKey(RetrospectiveOaPolicy, on_delete=models.CASCADE,
                                                related_name='retrospective_policy_notes', blank=True,
                                   null=True)
# The class below has been incorporated into Note
# class DeletionRequest(models.Model):
#     '''
#     Request from editors/curators/users for superusers to delete a particular node.
#     '''
#     reason = models.TextField()
#     node = models.ForeignKey(Node, on_delete=models.PROTECT, blank=True, null=True)
#     goldpolicy = models.ForeignKey(GoldPolicy, on_delete=models.PROTECT, blank=True, null=True)

class Deal(models.Model):
    '''
    Details of any agreements with publishers that apply to a particular node
    '''
    name = models.CharField(max_length=255, blank=True, null=True)
    node = models.ForeignKey(Node, on_delete=models.PROTECT, limit_choices_to={'name_status': 'PRIMARY'},
                             related_name='deals')
    APPLIES_TO_CHOICES = (
        ('AUTHORS', 'Authors'),
        ('INSTITUTIONS', 'Institutions')
    )
    applies_to = models.CharField(max_length=20, choices=APPLIES_TO_CHOICES)
    NESLIVOUCHERS = 'NESLI VOUCHERS'
    OUPPREPAYMENT = 'OUP PREPAYMENT'
    SOCIETY = 'SOCIETY DISCOUNT'
    SPRINGERCOMPACT = 'SPRINGER COMPACT'
    WILEYDASHBOARD = 'WILEY DASHBOARD'
    DEAL_TYPES = (
        (NESLIVOUCHERS, 'NESLi vouchers'),
        (OUPPREPAYMENT, 'OUP prepayment account'),
        (SOCIETY, 'Society membership discount'),
        (SPRINGERCOMPACT, 'Springer Compact'),
        (WILEYDASHBOARD, 'Wiley Open Access Account'),
        ('MEMBER', 'Member'),
        ('OTHER', 'Other'),
        ('PREPAYMENT', 'Pre-payment account'),
        ('SUBSCRIBER', 'Subscriber')
    )
    type = models.CharField(max_length=20, choices=DEAL_TYPES)
    discount_currency = models.CharField(max_length=10, choices=APC_CURRENCY_CHOICES, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)

    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    vetted = models.BooleanField(default=True)
    vetted_date = models.DateField(blank=True, null=True)
    last_checked = models.DateField(blank=True, null=True)
    superseded = models.BooleanField(default=False)
    superseded_date = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return self.get_type_display()

    def checked_recently(self):
        return self.last_checked > EXPIRY_DATE

    def updated_recently(self):
        return self.updated > EXPIRY_TIME

    def created_recently(self):
        return self.created > EXPIRY_TIME

    def vetted_recently(self):
        return self.vetted_date > EXPIRY_DATE

    class Meta:
        ordering = ('name',)