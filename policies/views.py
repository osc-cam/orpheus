from django.shortcuts import get_object_or_404, render, render_to_response
from django.core.urlresolvers import reverse_lazy
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse  # Used to generate URLs by reversing the URL patterns
from django.views.generic.detail import SingleObjectMixin
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.forms.models import model_to_dict
from django.db.models import Q, Avg, Count, F

from django.http import HttpResponse, HttpResponseRedirect
# from django.template import loader

from django_addanother.views import CreatePopupMixin, UpdatePopupMixin
from dal import autocomplete

from datetime import datetime, date

from . import models
from . import forms
from search_views.search import SearchListView
from search_views.filters import BaseFilter

from rest_framework import generics
from policies import serializers

# region API views
class NodeListAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.NodeSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned nodes by filtering
        against `id`, `name`, or `issn` query parameter in the URL.

        The `issn` query parameter will match either the issn or eissn
        fields of nodes.
        """
        queryset = models.Node.objects.all()
        nodeid = self.request.query_params.get('id', None)
        nodename = self.request.query_params.get('name', None)
        nodeissn = self.request.query_params.get('issn', None)
        node_romeo = self.request.query_params.get('romeo', None)
        if nodeid is not None:
            queryset = queryset.filter(id__exact=nodeid)
        if nodeissn is not None:
            queryset = queryset.filter(Q(issn__exact=nodeissn) | Q(eissn__exact=nodeissn))
        if nodename is not None:
            queryset = queryset.filter(name__iexact=nodename)
        if node_romeo is not None:
            queryset = queryset.filter(romeo_id__exact=node_romeo)
        return queryset

class NodePreferredNameListAPIView(generics.ListCreateAPIView):
    '''
    This API view returns only nodes with name_status == 'PRIMARY' for searches
    matching both synonyms and preferred names (e.g. searches by ISSN).
    '''

    serializer_class = serializers.NodeSummarySerializer

    def get_queryset(self):
        """
        Optionally restricts the returned nodes by filtering
        against `id`, `name`, or `issn` query parameter in the URL.

        The `issn` query parameter will match either the issn or eissn
        fields of nodes.
        """
        queryset = models.Node.objects.all()
        nodeid = self.request.query_params.get('id', None)
        nodename = self.request.query_params.get('name', None)
        nodeissn = self.request.query_params.get('issn', None)
        if nodeid is not None:
            queryset = queryset.filter(id__exact=nodeid)
        elif nodename is not None:
            queryset = queryset.filter(name__iexact=nodename)
        elif nodeissn is not None:
            queryset = queryset.filter(Q(issn__exact=nodeissn) | Q(eissn__exact=nodeissn))

        if queryset:
            preferred_name_available = False
            for n in queryset:
                if n.name_status == 'PRIMARY':
                    preferred_name_available = True
            if preferred_name_available:
                queryset = queryset.filter(name_status='PRIMARY')

        return queryset

class CambridgeListAPIView(generics.ListAPIView):
    '''
    This API view returns only nodes with name_status == 'PRIMARY' for searches by ISSN
    matching both synonyms and preferred names. Only JOURNAL and
    CONFERENCE nodes are included in the response
    '''

    serializer_class = serializers.CambridgeSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned nodes by filtering
        against `id`, `name`, or `issn` query parameter in the URL.

        The `issn` query parameter will match either the issn or eissn
        fields of nodes.
        """
        def get_preferred_name_id(node):
            if node.name_status == 'PRIMARY':
                return node.id
            else:
                return node.synonym_of.id

        def name_search(raw_queryset, nodename):
            """
            Customised name search retaining homonyms. If queried name contains brackets [e.g.,
            'Astronomy & Astrophysics (Hans Publishers)'], an exact match is attempted. Otherwise,
            a match for journal names starting with the queried string is carried out and results
            differing from the queried string only by the contents of trailing brackets are considered
            as matches and returned.
            :param raw_queryset: a queryset containing all journals and conferences in the database
            :param nodename: name queried by client
            """
            if '(' in nodename:
                return raw_queryset.filter(name__iexact=nodename)
            else:
                temp_queryset = raw_queryset.filter(name__istartswith=nodename)
                wanted_ids = []
                for n in temp_queryset:
                    if '(' in n.name:
                        # publisher_names = list(models.Node.objects.filter(type__in=['PUBLISHER'])
                        #                        .values_list('name', flat=True))
                        if nodename == n.name.split('(')[0].strip():
                            wanted_ids.append(get_preferred_name_id(n))
                    elif nodename.lower() == n.name.lower():
                        wanted_ids.append(get_preferred_name_id(n))
                return raw_queryset.filter(id__in=wanted_ids)

        raw_queryset = models.Node.objects.filter(type__in=['JOURNAL', 'CONFERENCE'])
        nodeid = self.request.query_params.get('id', None)
        nodename = self.request.query_params.get('name', None)
        nodeissn = self.request.query_params.get('issn', None)
        issn_search = None
        if nodeid is not None:
            queryset = raw_queryset.filter(id__exact=nodeid)
        elif nodeissn is not None:
            for i in nodeissn.split(','): #support for comma-separated list of issns (e.g. ?issn=1111-1111,2222-2222)
                queryset = raw_queryset.filter(Q(issn__exact=i) | Q(eissn__exact=i))
                if queryset:
                    issn_search = True
                    break
            if not queryset and nodename is not None:
                queryset = name_search(raw_queryset, nodename)
        elif nodename is not None:
            queryset = name_search(raw_queryset, nodename)
        else:
            queryset = raw_queryset

        if queryset and issn_search:
            preferred_name_available = False
            for n in queryset:
                if n.name_status == 'PRIMARY':
                    preferred_name_available = True
            if preferred_name_available:
                queryset = queryset.filter(name_status='PRIMARY')

        return queryset

class NodeSimpleListAPIView(NodeListAPIView):
    serializer_class = serializers.NodeSimpleSerializer

class NodeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Node.objects.all()
    serializer_class = serializers.NodeSerializer

class GoldPolicyListAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.GoldPolicySerializer

    def get_queryset(self):
        """
        Optionally restricts the returned nodes by filtering
        against `node` query parameter in the URL.
        """
        queryset = models.GoldPolicy.objects.all()
        nodeid = self.request.query_params.get('node', None)
        if nodeid is not None:
            queryset = queryset.filter(node__exact=nodeid)
        return queryset

class GoldPolicyDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.GoldPolicy.objects.all()
    serializer_class = serializers.GoldPolicySerializer

class GreenPolicyListAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.GreenPolicySimpleSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned nodes by filtering
        against `node` query parameter in the URL.
        """
        queryset = models.GreenPolicy.objects.all()
        nodeid = self.request.query_params.get('node', None)
        if nodeid is not None:
            queryset = queryset.filter(node__exact=nodeid)
        return queryset

class GreenPolicyDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.GreenPolicy.objects.all()
    serializer_class = serializers.GreenPolicySerializer

class OaStatusListAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.OaStatusSimpleSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned nodes by filtering
        against `node` query parameter in the URL.
        """
        queryset = models.OaStatus.objects.all()
        nodeid = self.request.query_params.get('node', None)
        if nodeid is not None:
            queryset = queryset.filter(node__exact=nodeid)
        return queryset

class OaStatusDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.OaStatus.objects.all()
    serializer_class = serializers.OaStatusSerializer

class SourceListAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.SourceSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned nodes by filtering
        against `description` or `node` query parameters in the URL.
        """
        queryset = models.Source.objects.all()
        nodeid = self.request.query_params.get('node', None)
        name = self.request.query_params.get('name', None)
        if nodeid is not None:
            queryset = queryset.filter(node__exact=nodeid)
        elif name is not None:
            queryset = queryset.filter(description__startswith=name)
        return queryset

class SourceDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Source.objects.all()
    serializer_class = serializers.SourceSerializer

class LicenceListAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.LicenceSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned licences by filtering
        against `short name` or `long name` query parameters in the URL.
        """
        queryset = models.Licence.objects.all()
        short_name = self.request.query_params.get('shortname', None)
        long_name = self.request.query_params.get('longname', None)
        if short_name is not None:
            queryset = queryset.filter(short_name__exact=short_name)
        elif long_name is not None:
            queryset = queryset.filter(long_name__exact=long_name)
        return queryset

class OutletListAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.OutletSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned outlets by filtering
        against `name` query parameter in the URL.
        """
        queryset = models.Outlet.objects.all()
        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name__exact=name)
        return queryset

class VersionListAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.VersionSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned versions by filtering
        against `short name` or `long name` query parameters in the URL.
        """
        queryset = models.Version.objects.all()
        short_name = self.request.query_params.get('shortname', None)
        long_name = self.request.query_params.get('longname', None)
        if short_name is not None:
            queryset = queryset.filter(short_name__exact=short_name)
        elif long_name is not None:
            queryset = queryset.filter(long_name__exact=long_name)
        return queryset
# endregion

class NodeFilter(BaseFilter):
    search_fields = {
        'search_text': ['name', 'issn', 'eissn'],
    }

class SourceFilter(BaseFilter):
    search_fields = {
        'search_text': ['description', 'url'],
    }

# region Staticpages
def index(request):
    '''
    View function for homepage
    '''
    # Generate counts of some of the main objects
    num_nodes = models.Node.objects.all().count()
    num_nodes_primary = models.Node.objects.filter(name_status='PRIMARY').count()
    num_publishers = models.Node.objects.filter(type='PUBLISHER').count()
    num_publishers_primary = models.Node.objects.filter(type='PUBLISHER', name_status='PRIMARY').count()
    num_journals = models.Node.objects.filter(type='JOURNAL').count()
    num_journals_primary = models.Node.objects.filter(type='JOURNAL', name_status='PRIMARY').count()
    num_conferences = models.Node.objects.filter(type='CONFERENCE').count()
    num_conferences_primary = models.Node.objects.filter(type='CONFERENCE', name_status='PRIMARY').count()

    # Generate counts of policies
    num_node_green = models.Node.objects.annotate(green_count=Count(
        'green_policies')).filter(green_count__gte=1).count()
    num_journal_oa_status = models.Node.objects.filter(type='JOURNAL').annotate(oa_count=Count(
        'oa_stata')).filter(oa_count__gte=1).count()
    num_journal_green = models.Node.objects.filter(type='JOURNAL').annotate(green_count=Count(
        'green_policies')).filter(green_count__gte=1).count()
    num_journal_gold = models.Node.objects.filter(type='JOURNAL').annotate(gold_count=Count(
        'gold_policies')).filter(gold_count__gte=1).count()
    num_journal_epmc = models.Node.objects.filter(type='JOURNAL').annotate(epmc_count=Count(
        'epmc_policies')).filter(epmc_count__gte=1).count()
    num_journal_deals = models.Node.objects.filter(type='JOURNAL').annotate(deal_count=Count(
        'deals')).filter(deal_count__gte=1).count()
    num_journal_contacts = models.Node.objects.filter(type='JOURNAL').annotate(contact_count=Count(
        'contacts')).filter(contact_count__gte=1).count()
    num_publisher_oa_status = models.Node.objects.filter(type='PUBLISHER').annotate(oa_count=Count(
        'oa_stata')).filter(oa_count__gte=1).count()
    num_publisher_green = models.Node.objects.filter(type='PUBLISHER').annotate(green_count=Count(
        'green_policies')).filter(green_count__gte=1).count()
    num_publisher_gold = models.Node.objects.filter(type='PUBLISHER').annotate(gold_count=Count(
        'gold_policies')).filter(gold_count__gte=1).count()
    num_publisher_epmc = models.Node.objects.filter(type='PUBLISHER').annotate(epmc_count=Count(
        'epmc_policies')).filter(epmc_count__gte=1).count()
    num_publisher_deals = models.Node.objects.filter(type='PUBLISHER').annotate(deal_count=Count(
        'deals')).filter(deal_count__gte=1).count()
    num_publisher_contacts = models.Node.objects.filter(type='PUBLISHER').annotate(contact_count=Count(
        'contacts')).filter(contact_count__gte=1).count()
    num_conference_oa_status = models.Node.objects.filter(type='CONFERENCE').annotate(oa_count=Count(
        'oa_stata')).filter(oa_count__gte=1).count()
    num_conference_green = models.Node.objects.filter(type='CONFERENCE').annotate(green_count=Count(
        'green_policies')).filter(green_count__gte=1).count()
    num_conference_gold = models.Node.objects.filter(type='CONFERENCE').annotate(gold_count=Count(
        'gold_policies')).filter(gold_count__gte=1).count()
    num_conference_epmc = models.Node.objects.filter(type='CONFERENCE').annotate(epmc_count=Count(
        'epmc_policies')).filter(epmc_count__gte=1).count()
    num_conference_deals = models.Node.objects.filter(type='CONFERENCE').annotate(deal_count=Count(
        'deals')).filter(deal_count__gte=1).count()
    num_conference_contacts = models.Node.objects.filter(type='CONFERENCE').annotate(contact_count=Count(
        'contacts')).filter(contact_count__gte=1).count()

    publisher_list = models.Node.objects.filter(type='PUBLISHER', name_status='PRIMARY').order_by('name')
    journal_list = models.Node.objects.filter(type='JOURNAL', name_status='PRIMARY').order_by('name')
    conference_list = models.Node.objects.filter(type='CONFERENCE', name_status='PRIMARY').order_by('name')
    context = {'publisher_list': publisher_list,
               'journal_list': journal_list,
               'conference_list': conference_list,
               'num_nodes': num_nodes,
                'num_nodes_primary': num_nodes_primary,
                'num_publishers': num_publishers,
                'num_publishers_primary': num_publishers_primary,
                'num_journals': num_journals,
                'num_journals_primary': num_journals_primary,
                'num_conferences': num_conferences,
                'num_conferences_primary': num_conferences_primary,
                'num_node_green': num_node_green,
                'num_journal_oa_status': num_journal_oa_status,
                'num_journal_green': num_journal_green,
                'num_journal_gold': num_journal_gold,
                'num_journal_epmc': num_journal_epmc,
                'num_journal_deals': num_journal_deals,
                'num_journal_contacts': num_journal_contacts,
                'num_publisher_oa_status': num_publisher_oa_status,
                'num_publisher_green': num_publisher_green,
                'num_publisher_gold': num_publisher_gold,
                'num_publisher_epmc': num_publisher_epmc,
                'num_publisher_deals': num_publisher_deals,
                'num_publisher_contacts': num_publisher_contacts,
                'num_conference_oa_status': num_conference_oa_status,
                'num_conference_green': num_conference_green,
                'num_conference_gold': num_conference_gold,
                'num_conference_epmc': num_conference_epmc,
                'num_conference_deals': num_conference_deals,
                'num_conference_contacts': num_conference_contacts,
               }
    return render(request, 'policies/index.html', context)

class AboutView(TemplateView):
    template_name = "policies/static/about.html"
# endregion


# region Node list views
class NodeListView(LoginRequiredMixin, SearchListView):
    '''
    Generic class-based view listing all nodes in the database;
    with a search bar
    '''
    # regular django.views.generic.list.ListView configuration
    model = models.Node
    paginate_by = 50
    template_name = "policies/base_list_view.html"
    # additional configuration for SearchListView
    form_class = forms.ListViewSearchForm
    filter_class = NodeFilter

class JournalListView(NodeListView):
    template_name = "policies/journal_list_view.html"

    def get_queryset(self):
        return models.Node.objects.filter(type='JOURNAL').order_by('name')

class PublisherListView(NodeListView):
    template_name = "policies/publisher_list_view.html"

    def get_queryset(self):
        return models.Node.objects.filter(type='PUBLISHER').order_by('name')

class ConferenceListView(NodeListView):
    template_name = "policies/conference_list_view.html"

    def get_queryset(self):
        return models.Node.objects.filter(type='CONFERENCE').order_by('name')

# region curatorial Node list views
class GrandchildrenListView(NodeListView):
    '''
    Curatorial view displaying nodes whose parent has a parent
    '''
    template_name = "policies/curatorial/grandchildren_list_view.html"

    def get_queryset(self):
        return models.Node.objects.filter(parent__isnull=False).exclude(parent__parent__isnull=True).order_by('name')

class JournalchildrenListView(NodeListView):
    '''
    Curatorial view displaying nodes whose parent is not a publisher
    '''
    template_name = "policies/curatorial/journalchildren_list_view.html"

    def get_queryset(self):
        return models.Node.objects.filter(parent__isnull=False).exclude(parent__type='PUBLISHER').order_by('name')

class ProblematicPolicies(NodeListView):
    '''
    Curatorial view displaying nodes with one or more attached policies marked as problematic
    '''
    template_name = "policies/curatorial/problematic_policies_list_view.html"

    def get_queryset(self):
        return models.Node.objects.filter(green_policies__problematic=True)\
            .annotate(children_n=Count('children')).order_by('-children_n')

class SynonymchildrenListView(NodeListView):
    '''
    Curatorial view displaying nodes whose parent is not a preferred name
    '''
    template_name = "policies/curatorial/synonymchildren_list_view.html"

    def get_queryset(self):
        return models.Node.objects.filter(parent__isnull=False).exclude(parent__name_status='PRIMARY').order_by('name')

class SynonymofsynonymListView(NodeListView):
    '''
    Curatorial view displaying nodes that are synonyms of other synonyms
    '''
    template_name = "policies/curatorial/synonymofsynonym_list_view.html"

    def get_queryset(self):
        return models.Node.objects.filter(synonym_of__isnull=False).exclude(synonym_of__name_status='PRIMARY').order_by('name')

class SynonymswithpoliciesListView(NodeListView):
    '''
    Curatorial view displaying synonym nodes with attached policies
    '''
    template_name = "policies/curatorial/synonymswithpolicies_list_view.html"

    def get_queryset(self):
        return models.Node.objects.filter(synonym_of__isnull=False)\
            .annotate(green_n=Count('green_policies'), gold_n=Count('gold_policies'), oa_n=Count('oa_stata'))\
            .annotate(total_count=F('green_n') + F('gold_n') + F('oa_n')).filter(total_count__gte=1)
# endregion
# endregion

# region Node detail views
class detail(LoginRequiredMixin, DetailView):
    model = models.Node
    template_name = 'policies/node_detail.html'
    def get_context_data(self, **kwargs):
        context = super(detail, self).get_context_data(**kwargs)

        oastata = models.OaStatus.objects.filter(node=self.object.id)
        oastatus_prov = ''
        if not oastata:
            oastata = self.object.get_parent_oa_stata()
            try:
                oastatus_prov = '[inherited from %s: %s]' % (self.object.parent.get_type_display().lower(), self.object.parent)
            except AttributeError: # Node does not have a parent
                pass
        context['oastatus_list'] = oastata.filter(superseded=False)
        context['oastatus_prov'] = oastatus_prov

        gold = models.GoldPolicy.objects.filter(node=self.object.id)
        gold_prov = ''
        if not gold:
            gold = self.object.get_parent_gold_policies()
            try:
                gold_prov = '[inherited from %s: %s]' % (self.object.parent.get_type_display().lower(), self.object.parent)
            except AttributeError:  # Node does not have a parent
                pass
        context['goldpolicy_list'] = gold.filter(superseded=False)
        context['goldpolicy_prov'] = gold_prov

        green = models.GreenPolicy.objects.filter(node=self.object.id)
        green_prov = ''
        if not green:
            green = self.object.get_parent_green_policies()
            try:
                green_prov = '[inherited from %s: %s]' % (self.object.parent.get_type_display().lower(), self.object.parent)
            except AttributeError:  # Node does not have a parent
                pass
        context['greenpolicy_list'] = green.filter(superseded=False)
        context['greenpolicy_prov'] = green_prov

        epmc = models.Epmc.objects.filter(node=self.object.id)
        epmc_prov = ''
        if not epmc:
            epmc = self.object.get_parent_epmc_policies()
            try:
                epmc_prov = '[inherited from %s: %s]' % (self.object.parent.get_type_display().lower(), self.object.parent)
            except AttributeError:  # Node does not have a parent
                pass
        context['epmc_list'] = epmc.filter(superseded=False)
        context['epmc_prov'] = epmc_prov

        deal = models.Deal.objects.filter(node=self.object.id)
        deal_prov = ''
        if not deal:
            deal = self.object.get_parent_deal_policies()
            try:
                deal_prov = '[inherited from %s: %s]' % (self.object.parent.get_type_display().lower(), self.object.parent)
            except AttributeError:  # Node does not have a parent
                pass
        context['deal_list'] = deal.filter(superseded=False)
        context['deal_prov'] = deal_prov

        contact = models.Contact.objects.filter(node=self.object.id)
        contact_prov = ''
        if not contact:
            contact = self.object.get_parent_contacts()
            try:
                contact_prov = '[inherited from %s: %s]' % (self.object.parent.get_type_display().lower(), self.object.parent)
            except AttributeError:  # Node does not have a parent
                pass
        context['contact_list'] = contact.filter(active=True)
        context['contact_prov'] = contact_prov

        context['retro_list'] = models.RetrospectiveOaPolicy.objects.filter(superseded=False)
        return context

class NodeAllDetail(detail):
    def get_context_data(self, **kwargs):
        context = super(NodeAllDetail, self).get_context_data(**kwargs)

        oastata = models.OaStatus.objects.filter(node=self.object.id)
        oastatus_prov = ''
        if not oastata:
            oastata = self.object.get_parent_oa_stata()
            try:
                oastatus_prov = '[inherited from %s: %s]' % (
                self.object.parent.get_type_display().lower(), self.object.parent)
            except AttributeError:  # Node does not have a parent
                pass
        context['oastatus_list'] = oastata
        context['oastatus_prov'] = oastatus_prov

        gold = models.GoldPolicy.objects.filter(node=self.object.id)
        gold_prov = ''
        if not gold:
            gold = self.object.get_parent_gold_policies()
            try:
                gold_prov = '[inherited from %s: %s]' % (
                self.object.parent.get_type_display().lower(), self.object.parent)
            except AttributeError:  # Node does not have a parent
                pass
        context['goldpolicy_list'] = gold
        context['goldpolicy_prov'] = gold_prov

        green = models.GreenPolicy.objects.filter(node=self.object.id)
        green_prov = ''
        if not green:
            green = self.object.get_parent_green_policies()
            try:
                green_prov = '[inherited from %s: %s]' % (
                self.object.parent.get_type_display().lower(), self.object.parent)
            except AttributeError:  # Node does not have a parent
                pass
        context['greenpolicy_list'] = green
        context['greenpolicy_prov'] = green_prov

        epmc = models.Epmc.objects.filter(node=self.object.id)
        epmc_prov = ''
        if not epmc:
            epmc = self.object.get_parent_epmc_policies()
            try:
                epmc_prov = '[inherited from %s: %s]' % (
                    self.object.parent.get_type_display().lower(), self.object.parent)
            except AttributeError:  # Node does not have a parent
                pass
        context['epmc_list'] = epmc
        context['epmc_prov'] = epmc_prov

        deal = models.Deal.objects.filter(node=self.object.id)
        deal_prov = ''
        if not deal:
            deal = self.object.get_parent_deal_policies()
            try:
                deal_prov = '[inherited from %s: %s]' % (self.object.parent.get_type_display().lower(), self.object.parent)
            except AttributeError:  # Node does not have a parent
                pass
        context['deal_list'] = deal
        context['deal_prov'] = deal_prov

        contact = models.Contact.objects.filter(node=self.object.id)
        contact_prov = ''
        if not contact:
            contact = self.object.get_parent_contacts()
            try:
                contact_prov = '[inherited from %s: %s]' % (self.object.parent.get_type_display().lower(), self.object.parent)
            except AttributeError:  # Node does not have a parent
                pass
        context['contact_list'] = contact
        context['contact_prov'] = contact_prov

        context['retro_list'] = models.RetrospectiveOaPolicy.objects.filter(superseded=False)
        return context
# endregion

# region Node create forms
class NodeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return models.Node.objects.none()
        qs = models.Node.objects.all()
        type = self.forwarded.get('type', None)
        if type:
            qs = qs.filter(type__exact=type)
        if self.q:
            qs = qs.filter(name__istartswith=self.q)
        return qs

class PublisherAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return models.Node.objects.none()
        qs = models.Node.objects.filter(type__exact='PUBLISHER')
        if self.q:
            qs = qs.filter(name__istartswith=self.q)
        return qs

class NodeCreate(CreatePopupMixin, LoginRequiredMixin, CreateView):
    model = models.Node
    form_class = forms.NodeForm
    #fields = '__all__' ## This is now handled by NodeForm
    initial = {'vetted' : True, 'vetted_date' : date.today()} ## The only problem with this is that it overwrites vetted_date if it already exists; ideally we should check the existing value of that field
    template_name_suffix = '_create_form'

class ChildCreate(NodeCreate):
    form_class = forms.ChildNodeForm
    template_name_suffix = '_child_create_form'

    def form_valid(self, form): # https://docs.djangoproject.com/en/1.11/topics/class-based-views/generic-editing/
        parent = SingleObjectMixin.get_object(self, queryset=models.Node.objects.filter(id=self.kwargs['pk']))
        form.instance.parent = parent
        return super(ChildCreate, self).form_valid(form)

    def get_context_data(self, **kwargs):
        self.parent = SingleObjectMixin.get_object(self, queryset=models.Node.objects.filter(id=self.kwargs['pk']))
        context = super(ChildCreate, self).get_context_data(**kwargs)
        context['parentnode'] = self.parent
        return context

class SynonymCreate(NodeCreate):
    template_name_suffix = '_synonym_create_form'

    def get_initial(self): # http://melardev.com/eng/blog/2017/11/04/createview-django-4-examples/
        initial_data = super(SynonymCreate, self).get_initial()
        synonym_of = SingleObjectMixin.get_object(self, queryset=models.Node.objects.filter(id=self.kwargs['pk']))
        initial_data['synonym_of'] = synonym_of
        initial_data['name'] = synonym_of
        initial_data['name_status'] = 'SYNONYM'
        initial_data['type'] = synonym_of.type
        initial_data['url'] = synonym_of.url
        initial_data['issn'] = synonym_of.issn
        initial_data['eissn'] = synonym_of.eissn
        initial_data['epmc_url'] = synonym_of.epmc_url
        initial_data['romeo_id'] = synonym_of.romeo_id
        initial_data['parent'] = synonym_of.parent
        return initial_data

    def get_context_data(self, **kwargs):
        self.synonym_of = SingleObjectMixin.get_object(self, queryset=models.Node.objects.filter(id=self.kwargs['pk']))
        context = super(SynonymCreate, self).get_context_data(**kwargs)
        context['preferred_name'] = self.synonym_of
        return context

class PublisherCreate(NodeCreate):
    form_class = forms.PublisherNodeForm
    template_name = 'policies/publisher_create_form.html'

    def form_valid(self, form):
        form.instance.type = 'PUBLISHER'
        return super(PublisherCreate, self).form_valid(form)

class JournalCreate(NodeCreate):
    form_class = forms.JournalNodeForm
    template_name = 'policies/journal_create_form.html'

    def form_valid(self, form):
        form.instance.type = 'JOURNAL'
        return super(JournalCreate, self).form_valid(form)

class ConferenceCreate(NodeCreate):
    form_class = forms.ConferenceNodeForm
    template_name = 'policies/conference_create_form.html'

    def form_valid(self, form):
        form.instance.type = 'CONFERENCE'
        return super(ConferenceCreate, self).form_valid(form)
# endregion

# region Node update forms
class NodeUpdate(UpdatePopupMixin, LoginRequiredMixin, UpdateView):
    model = models.Node
    form_class = forms.NodeForm
    #fields = '__all__' ## This is now handled by NodeForm
    initial = {'vetted' : True, 'vetted_date' : date.today()} ## The only problem with this is that it overwrites vetted_date if it already exists; ideally we should check the existing value of that field
    template_name_suffix = '_update_form'

class PublisherUpdate(NodeUpdate):
    form_class = forms.PublisherNodeForm

class JournalUpdate(NodeUpdate):
    form_class = forms.JournalNodeForm

class ConferenceUpdate(NodeUpdate):
    form_class = forms.JournalNodeForm
# endregion

class NodeDelete(LoginRequiredMixin, CreateView):
    model = models.Note
    form_class = forms.DeleteForm
    template_name = 'policies/node_delete_form.html'

    def form_valid(self, form):
        node = SingleObjectMixin.get_object(self, queryset=models.Node.objects.filter(id=self.kwargs['pk']))
        form.instance.node = node
        form.instance.deletion_request = True
        return super(NodeDelete, self).form_valid(form)

    def get_context_data(self, **kwargs):
        self.node = SingleObjectMixin.get_object(self, queryset=models.Node.objects.filter(id=self.kwargs['pk']))
        context = super(NodeDelete, self).get_context_data(**kwargs)
        context['node'] = self.node
        return context

    def get_success_url(self): # https://stackoverflow.com/questions/26290415/deleteview-with-a-dynamic-success-url-dependent-on-id
        node = self.object.node
        return reverse_lazy('policies:detail', kwargs={'pk': node.id})

class NodeConfirmDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'policies.node.can_delete_node'
    model = models.Node

    def get_success_url(self):
        return reverse_lazy('policies:index')

# region Source views
class SourceAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return models.Source.objects.none()
        qs = models.Source.objects.all()
        if self.q:
            qs = qs.filter(description__istartswith=self.q)
        return qs

class SourceListView(LoginRequiredMixin, SearchListView):
    '''
    Generic class-based view listing all sources in the database;
    with a search bar
    '''
    # regular django.views.generic.list.ListView configuration
    model = models.Source
    paginate_by = 50
    template_name = "policies/source_list_view.html"
    # additional configuration for SearchListView
    form_class = forms.ListViewSearchForm
    filter_class = SourceFilter

class SourceDetail(LoginRequiredMixin, DetailView):
    model = models.Source
    template_name = 'policies/source_detail.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(SourceDetail, self).get_context_data(**kwargs)

        nodes = models.Node.objects.filter(source=self.object.id)
        nodes_page = self.request.GET.get('page', 1)
        nodes_paginator = Paginator(nodes, self.paginate_by)
        try:
            node_list = nodes_paginator.page(nodes_page)
        except PageNotAnInteger:
            node_list = nodes_paginator.page(1)
        except EmptyPage:
            node_list = nodes_paginator.page(nodes_paginator.num_pages)
        context['node_list'] = node_list
        context['node_count'] = nodes.count()

        oastatus = models.OaStatus.objects.filter(source=self.object.id)
        page = self.request.GET.get('page', 1)
        paginator = Paginator(oastatus, self.paginate_by)
        try:
            list = paginator.page(page)
        except PageNotAnInteger:
            list = paginator.page(1)
        except EmptyPage:
            list = paginator.page(paginator.num_pages)
        context['oastatus_list'] = list
        context['oastatus_count'] = oastatus.count()

        gold = models.GoldPolicy.objects.filter(source=self.object.id)
        page = self.request.GET.get('page', 1)
        paginator = Paginator(gold, self.paginate_by)
        try:
            list = paginator.page(page)
        except PageNotAnInteger:
            list = paginator.page(1)
        except EmptyPage:
            list = paginator.page(paginator.num_pages)
        context['gold_list'] = list
        context['gold_count'] = gold.count()

        green = models.GreenPolicy.objects.filter(source=self.object.id)
        page = self.request.GET.get('page', 1)
        paginator = Paginator(green, self.paginate_by)
        try:
            list = paginator.page(page)
        except PageNotAnInteger:
            list = paginator.page(1)
        except EmptyPage:
            list = paginator.page(paginator.num_pages)
        context['green_list'] = list
        context['green_count'] = green.count()

        return context

class SourceCreate(CreatePopupMixin, LoginRequiredMixin, CreateView):
    model = models.Source
    form_class = forms.SourceForm
    template_name_suffix = '_create_form'

class SourceUpdate(UpdatePopupMixin, LoginRequiredMixin, UpdateView):
    model = models.Source
    form_class = forms.SourceForm
    #fields = '__all__' ## This is now handled by NodeForm
    template_name_suffix = '_update_form'

class SourceDelete(LoginRequiredMixin, CreateView):
    model = models.Source
    form_class = forms.DeleteForm
    template_name = 'policies/node_delete_form.html'

    def form_valid(self, form):
        source = SingleObjectMixin.get_object(self, queryset=models.Source.objects.filter(id=self.kwargs['pk']))
        form.instance.source = source
        form.instance.deletion_request = True
        return super(SourceDelete, self).form_valid(form)

    def get_context_data(self, **kwargs):
        self.source = SingleObjectMixin.get_object(self, queryset=models.Source.objects.filter(id=self.kwargs['pk']))
        context = super(SourceDelete, self).get_context_data(**kwargs)
        context['source'] = self.source
        return context

    def get_success_url(self): # https://stackoverflow.com/questions/26290415/deleteview-with-a-dynamic-success-url-dependent-on-id
        source = self.object.souce
        return reverse_lazy('policies:source_detail', kwargs={'pk': source.id})

class SourceConfirmDelete(LoginRequiredMixin, DeleteView):
    model = models.Source

    def get_success_url(self):
        return reverse_lazy('policies:index')
# endregion

class LicenceCreate(CreatePopupMixin, LoginRequiredMixin, CreateView):
    model = models.Licence
    form_class = forms.LicenceForm
    template_name_suffix = '_create_form'

class NodeAttributeCreateView(LoginRequiredMixin, CreateView): # https://stackoverflow.com/questions/11027996/success-url-in-updateview-based-on-passed-value
    '''
    A subclass of CreateView for adding attributes that only make sense in the
    context of a single node (e.g. GoldPolicy, GreenPolicy, etc).
    '''
    template_name_suffix = '_create_form'
    initial = {'vetted': True, 'vetted_date': date.today(), 'last_checked': date.today(),}

    def form_valid(self, form):
        node = SingleObjectMixin.get_object(self, queryset=models.Node.objects.filter(id=self.kwargs['pk']))
        form.instance.node = node
        return super(NodeAttributeCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        self.node = SingleObjectMixin.get_object(self, queryset=models.Node.objects.filter(id=self.kwargs['pk']))
        context = super(NodeAttributeCreateView, self).get_context_data(**kwargs)
        context['node'] = self.node
        return context

    def get_success_url(self):  # https://stackoverflow.com/questions/26564027/django-createview-with-success-url-being-the-same-view
        return reverse('policies:detail', args=[str(self.kwargs['pk'])])

# region Oa Status views
class OaStatusCreate(NodeAttributeCreateView):
    model = models.OaStatus
    form_class = forms.OaStatusForm

class OaStatusUpdate(LoginRequiredMixin, UpdateView):
    model = models.OaStatus
    form_class = forms.OaStatusForm
    template_name_suffix = '_update_form'
    initial = {'vetted': True, 'vetted_date': date.today(), 'last_checked': date.today()}

class OaStatusDelete(LoginRequiredMixin, CreateView):
    model = models.Note
    form_class = forms.DeleteForm
    template_name = 'policies/oastatus_delete_form.html'

    def form_valid(self, form):
        oastatus = SingleObjectMixin.get_object(self, queryset=models.OaStatus.objects.filter(id=self.kwargs['pk']))
        form.instance.oastatus = oastatus
        form.instance.deletion_request = True
        return super(OaStatusDelete, self).form_valid(form)

    def get_context_data(self, **kwargs):
        self.oastatus = SingleObjectMixin.get_object(self, queryset=models.OaStatus.objects.filter(id=self.kwargs['pk']))
        context = super(OaStatusDelete, self).get_context_data(**kwargs)
        context['oastatus'] = self.oastatus
        return context

    def get_success_url(self):
        self.oastatus = SingleObjectMixin.get_object(self,
                                                     queryset=models.OaStatus.objects.filter(id=self.kwargs['pk']))
        self.node = self.oastatus.node
        return reverse_lazy('policies:detail', kwargs={'pk': self.node.id})

class OaStatusConfirmDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'policies.oa_status.can_delete_oa_status'
    model = models.OaStatus

    def get_success_url(self):
        self.oastatus = SingleObjectMixin.get_object(self,
                                                       queryset=models.OaStatus.objects.filter(id=self.kwargs['pk']))
        self.node = self.oastatus.node
        return reverse_lazy('policies:detail', kwargs={'pk': self.node.id})
# endregion

# region Gold Policy views
class GoldPolicyCreate(NodeAttributeCreateView):
    model = models.GoldPolicy
    form_class = forms.GoldPolicyForm

class GoldPolicyUpdate(LoginRequiredMixin, UpdateView):
    model = models.GoldPolicy
    form_class = forms.GoldPolicyForm
    template_name_suffix = '_update_form'
    initial = {'vetted' : True, 'vetted_date' : date.today()}

class GoldPolicyDelete(LoginRequiredMixin, CreateView):
    model = models.Note
    form_class = forms.DeleteForm
    template_name = 'policies/goldpolicy_delete_form.html'

    def form_valid(self, form):
        goldpolicy = SingleObjectMixin.get_object(self, queryset=models.GoldPolicy.objects.filter(id=self.kwargs['pk']))
        form.instance.goldpolicy = goldpolicy
        form.instance.deletion_request = True
        return super(GoldPolicyDelete, self).form_valid(form)

    def get_context_data(self, **kwargs):
        self.goldpolicy = SingleObjectMixin.get_object(self, queryset=models.GoldPolicy.objects.filter(id=self.kwargs['pk']))
        context = super(GoldPolicyDelete, self).get_context_data(**kwargs)
        context['goldpolicy'] = self.goldpolicy
        return context

    def get_success_url(self):
        self.goldpolicy = SingleObjectMixin.get_object(self,
                                                       queryset=models.GoldPolicy.objects.filter(id=self.kwargs['pk']))
        self.node = self.goldpolicy.node
        return reverse_lazy('policies:detail', kwargs={'pk': self.node.id})

# permissions for view below https://stackoverflow.com/questions/5531258/example-of-django-class-based-deleteview
class GoldPolicyConfirmDelete(LoginRequiredMixin, DeleteView):
    model = models.GoldPolicy

    def get_success_url(self):
        self.goldpolicy = SingleObjectMixin.get_object(self,
                                                       queryset=models.GoldPolicy.objects.filter(
                                                           id=self.kwargs['pk']))
        self.node = self.goldpolicy.node
        return reverse_lazy('policies:detail', kwargs={'pk': self.node.id})
# endregion

# region Green policy views
class GreenPolicyCreate(NodeAttributeCreateView):
    model = models.GreenPolicy
    form_class = forms.GreenPolicyForm

class GreenPolicyUpdate(LoginRequiredMixin, UpdateView):
    model = models.GreenPolicy
    form_class = forms.GreenPolicyForm
    template_name_suffix = '_update_form'
    initial = {'vetted' : True, 'vetted_date' : date.today()}

class GreenPolicyDelete(LoginRequiredMixin, CreateView):
    model = models.Note
    form_class = forms.DeleteForm
    template_name = 'policies/greenpolicy_delete_form.html'

    def form_valid(self, form):
        greenpolicy = SingleObjectMixin.get_object(self, queryset=models.GreenPolicy.objects.filter(id=self.kwargs['pk']))
        form.instance.greenpolicy = greenpolicy
        form.instance.deletion_request = True
        return super(GreenPolicyDelete, self).form_valid(form)

    def get_context_data(self, **kwargs):
        self.greenpolicy = SingleObjectMixin.get_object(self, queryset=models.GreenPolicy.objects.filter(id=self.kwargs['pk']))
        context = super(GreenPolicyDelete, self).get_context_data(**kwargs)
        context['greenpolicy'] = self.greenpolicy
        return context

    def get_success_url(self):
        self.greenpolicy = SingleObjectMixin.get_object(self,
                                                       queryset=models.GreenPolicy.objects.filter(id=self.kwargs['pk']))
        self.node = self.greenpolicy.node
        return reverse_lazy('policies:detail', kwargs={'pk': self.node.id})

class GreenPolicyConfirmDelete(LoginRequiredMixin, DeleteView):
    model = models.GreenPolicy

    def get_success_url(self):
        self.greenpolicy = SingleObjectMixin.get_object(self,
                                                       queryset=models.GreenPolicy.objects.filter(id=self.kwargs['pk']))
        self.node = self.greenpolicy.node
        return reverse_lazy('policies:detail', kwargs={'pk': self.node.id})
# endregion

# region Epmc policy views
class EpmcCreate(NodeAttributeCreateView):
    model = models.Epmc
    form_class = forms.EpmcForm

class EpmcUpdate(LoginRequiredMixin, UpdateView):
    model = models.Epmc
    form_class = forms.EpmcForm
    template_name_suffix = '_update_form'
    initial = {'vetted' : True, 'vetted_date' : date.today()}

class EpmcDelete(LoginRequiredMixin, CreateView):
    model = models.Note
    form_class = forms.DeleteForm
    template_name = 'policies/epmc_delete_form.html'

    def form_valid(self, form):
        epmc = SingleObjectMixin.get_object(self, queryset=models.Epmc.objects.filter(id=self.kwargs['pk']))
        form.instance.epmc = epmc
        form.instance.deletion_request = True
        return super(EpmcDelete, self).form_valid(form)

    def get_context_data(self, **kwargs):
        self.epmc = SingleObjectMixin.get_object(self, queryset=models.Epmc.objects.filter(id=self.kwargs['pk']))
        context = super(EpmcDelete, self).get_context_data(**kwargs)
        context['epmc'] = self.epmc
        return context

    def get_success_url(self):
        self.epmc = SingleObjectMixin.get_object(self,
                                                       queryset=models.Epmc.objects.filter(id=self.kwargs['pk']))
        self.node = self.epmc.node
        return reverse_lazy('policies:detail', kwargs={'pk': self.node.id})

class EpmcConfirmDelete(LoginRequiredMixin, DeleteView):
    model = models.Epmc

    def get_success_url(self):
        self.epmc = SingleObjectMixin.get_object(self,
                                                       queryset=models.Epmc.objects.filter(id=self.kwargs['pk']))
        self.node = self.epmc.node
        return reverse_lazy('policies:detail', kwargs={'pk': self.node.id})
# endregion

# region Deal views
class DealCreate(NodeAttributeCreateView):
    model = models.Deal
    form_class = forms.DealForm

class DealUpdate(LoginRequiredMixin, UpdateView):
    model = models.Deal
    form_class = forms.DealForm
    template_name_suffix = '_update_form'
    initial = {'vetted' : True, 'vetted_date' : date.today()}

class DealDelete(LoginRequiredMixin, CreateView):
    model = models.Note
    form_class = forms.DeleteForm
    template_name = 'policies/deal_delete_form.html'

    def form_valid(self, form):
        deal = SingleObjectMixin.get_object(self, queryset=models.Deal.objects.filter(id=self.kwargs['pk']))
        form.instance.deal = deal
        form.instance.deletion_request = True
        return super(DealDelete, self).form_valid(form)

    def get_context_data(self, **kwargs):
        self.deal = SingleObjectMixin.get_object(self, queryset=models.Deal.objects.filter(id=self.kwargs['pk']))
        context = super(DealDelete, self).get_context_data(**kwargs)
        context['deal'] = self.deal
        return context

    def get_success_url(self):
        self.deal = SingleObjectMixin.get_object(self,
                                                       queryset=models.Deal.objects.filter(id=self.kwargs['pk']))
        self.node = self.deal.node
        return reverse_lazy('policies:detail', kwargs={'pk': self.node.id})

class DealConfirmDelete(LoginRequiredMixin, DeleteView):
    model = models.Deal

    def get_success_url(self):
        self.deal = SingleObjectMixin.get_object(self,
                                                       queryset=models.Deal.objects.filter(id=self.kwargs['pk']))
        self.node = self.deal.node
        return reverse_lazy('policies:detail', kwargs={'pk': self.node.id})
# endregion

# region Contact views
class ContactCreate(NodeAttributeCreateView):
    model = models.Contact
    form_class = forms.ContactForm

class ContactUpdate(LoginRequiredMixin, UpdateView):
    model = models.Contact
    form_class = forms.ContactForm
    template_name_suffix = '_update_form'

class ContactDelete(LoginRequiredMixin, CreateView):
    model = models.Note
    form_class = forms.DeleteForm
    template_name = 'policies/contact_delete_form.html'

    def form_valid(self, form):
        contact = SingleObjectMixin.get_object(self, queryset=models.Contact.objects.filter(id=self.kwargs['pk']))
        form.instance.contact = contact
        form.instance.deletion_request = True
        return super(ContactDelete, self).form_valid(form)

    def get_context_data(self, **kwargs):
        self.contact = SingleObjectMixin.get_object(self, queryset=models.Contact.objects.filter(id=self.kwargs['pk']))
        context = super(ContactDelete, self).get_context_data(**kwargs)
        context['contact'] = self.contact
        return context

    def get_success_url(self):
        self.contact = SingleObjectMixin.get_object(self,
                                                     queryset=models.Contact.objects.filter(id=self.kwargs['pk']))
        self.node = self.contact.node
        return reverse_lazy('policies:detail', kwargs={'pk': self.node.id})

class ContactConfirmDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'policies.contact.can_delete_contact'
    model = models.Contact

    def get_success_url(self):
        self.contact = SingleObjectMixin.get_object(self,
                                                       queryset=models.Contact.objects.filter(id=self.kwargs['pk']))
        self.node = self.contact.node
        return reverse_lazy('policies:detail', kwargs={'pk': self.node.id})
# endregion





class JournalbyPublisherListView(LoginRequiredMixin, SearchListView):
    '''
    Generic class-based view listing all journals by a publisher in the database;
    with a search bar
    '''
    # regular django.views.generic.list.ListView configuration
    model = models.Node
    form_class = forms.ListViewSearchForm
    paginate_by = 50
    template_name = "policies/journal_list_view.html"

    def get_queryset(self):
        return models.Node.objects.filter(type='JOURNAL', parent=self.kwargs['pk']).order_by('name') # https://stackoverflow.com/a/11494666/9903

    # additional configuration for SearchListView
    form_class = forms.ListViewSearchForm
    filter_class = NodeFilter