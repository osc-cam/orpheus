from django.conf.urls import url

from . import views

app_name = 'policies'

# Homepage and other mostly static content
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^about/$', views.AboutView.as_view(), name='about'),
]

# API views
urlpatterns += [
    url(r'^api/nodes/$', views.NodeSimpleListAPIView.as_view(), name='api_nodes'),
    url(r'^api/nodes/attributes/$', views.NodeListAPIView.as_view(), name='api_nodes_attributes'),
    url(r'^api/nodes/summary/$', views.NodePreferredNameListAPIView.as_view(), name='api_nodes_preferred_name'),
    url(r'^api/nodes/(?P<pk>[0-9]+)/$', views.NodeDetailAPIView.as_view(), name='api_node_detail'),
    url(r'^api/goldpolicies/$', views.GoldPolicyListAPIView.as_view(), name='api_gold'),
    url(r'^api/goldpolicies/(?P<pk>[0-9]+)/$', views.GoldPolicyDetailAPIView.as_view(), name='api_gold_detail'),
    url(r'^api/greenpolicies/$', views.GreenPolicyListAPIView.as_view(), name='api_green'),
    url(r'^api/greenpolicies/(?P<pk>[0-9]+)/$', views.GreenPolicyDetailAPIView.as_view(), name='api_green_detail'),
    url(r'^api/oastatus/$', views.OaStatusListAPIView.as_view(), name='api_oa_status'),
    url(r'^api/oastatus/(?P<pk>[0-9]+)/$', views.OaStatusDetailAPIView.as_view(), name='api_oa_status_detail'),
    url(r'^api/sources/$', views.SourceListAPIView.as_view(), name='api_source'),
    url(r'^api/sources/(?P<pk>[0-9]+)/$', views.SourceDetailAPIView.as_view(), name='api_source_detail'),
    url(r'^api/licences/$', views.LicenceListAPIView.as_view(), name='api_licence'),
    url(r'^api/outlets/$', views.OutletListAPIView.as_view(), name='api_outlet'),
    url(r'^api/versions/$', views.VersionListAPIView.as_view(), name='api_version'),
]

# Personalized API views
urlpatterns += [
    url(r'^api/cambridge/$', views.CambridgeListAPIView.as_view(), name='api_cambridge'),
]

# Autocomplete views
urlpatterns += [
    url(r'^nodeautocomplete/$', views.NodeAutocomplete.as_view(), name='node_autocomplete'),
    url(r'^publisherautocomplete/$', views.PublisherAutocomplete.as_view(),
        name='publisher_autocomplete'),
    url(r'^sourceautocomplete/$', views.SourceAutocomplete.as_view(), name='source_autocomplete'),
]

# List views
urlpatterns += [
    url(r'^journals/$', views.JournalListView.as_view(), name='journals'),
    url(r'^publishers/$', views.PublisherListView.as_view(), name='publishers'),
    url(r'^conferences/$', views.ConferenceListView.as_view(), name='conferences'),
    url(r'^sources/$', views.SourceListView.as_view(), name='sources'),
    url(r'^(?P<pk>[0-9]+)/journals/$', views.JournalbyPublisherListView.as_view(), name='journals_by_publisher'),
]

# Curatorial list views
urlpatterns += [
    url(r'^grandchildren/$', views.GrandchildrenListView.as_view(), name='grandchildren'),
    url(r'^journalchildren/$', views.JournalchildrenListView.as_view(), name='journalchildren'),
    url(r'^problematicpolicies/$', views.ProblematicPolicies.as_view(), name='problematic_policies'),
    url(r'^synonymchildren/$', views.SynonymchildrenListView.as_view(), name='synonymchildren'),
    url(r'^synonymofsynonym/$', views.SynonymofsynonymListView.as_view(), name='synonymofsynonym'),
    url(r'^synonymswithpolicies/$', views.SynonymswithpoliciesListView.as_view(), name='synonymswithpolicies'),
]

# Detail views
urlpatterns += [
    url(r'^(?P<pk>[0-9]+)/$', views.detail.as_view(), name='detail'),
    url(r'^(?P<pk>[0-9]+)/all/$', views.NodeAllDetail.as_view(), name='node_all_detail'),
    url(r'^source/(?P<pk>[0-9]+)/$', views.SourceDetail.as_view(), name='source_detail'),
]

# Node forms
urlpatterns += [
    url(r'^newnode/$', views.NodeCreate.as_view(), name='node_add'),
    url(r'^newjournal/$', views.JournalCreate.as_view(), name='journal_add'),
    url(r'^newpublisher/$', views.PublisherCreate.as_view(), name='publisher_add'),
    url(r'^newconference/$', views.ConferenceCreate.as_view(), name='conference_add'),
    url(r'^(?P<pk>[0-9]+)/newchild/$', views.ChildCreate.as_view(), name='child_add'),
    url(r'^(?P<pk>[0-9]+)/newsynonym/$', views.SynonymCreate.as_view(), name='synonym_add'),
    url(r'^(?P<pk>[0-9]+)/edit/$', views.NodeUpdate.as_view(), name='updateNode'),
    url(r'^(?P<pk>[0-9]+)/editpublisher/$', views.PublisherUpdate.as_view(), name='publisher_update'),
    url(r'^(?P<pk>[0-9]+)/editjournal/$', views.JournalUpdate.as_view(), name='journal_update'),
    url(r'^(?P<pk>[0-9]+)/editconference/$', views.ConferenceUpdate.as_view(), name='conference_update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.NodeDelete.as_view(), name='node_delete'),
    url(r'^(?P<pk>[0-9]+)/confirmdelete/$', views.NodeConfirmDelete.as_view(), name='node_confirm_delete'),
]

# OA status forms
urlpatterns += [
    url(r'^(?P<pk>[0-9]+)/newoastatus/$', views.OaStatusCreate.as_view(), name='oa_status_add'),
    url(r'^oastatus/(?P<pk>[0-9]+)/edit/$', views.OaStatusUpdate.as_view(), name='oa_status_update'),
    url(r'^oastatus/(?P<pk>[0-9]+)/delete/$', views.OaStatusDelete.as_view(), name='oa_status_delete'),
    url(r'^oastatus/(?P<pk>[0-9]+)/confirmdelete/$', views.OaStatusConfirmDelete.as_view(), name='oa_status_confirm_delete'),
]

# Gold policy forms
urlpatterns += [
    url(r'^(?P<pk>[0-9]+)/newgoldpolicy/$', views.GoldPolicyCreate.as_view(), name='gold_policy_add'),
    url(r'^goldpolicies/(?P<pk>[0-9]+)/edit/$', views.GoldPolicyUpdate.as_view(), name='gold_policy_update'),
    url(r'^goldpolicies/(?P<pk>[0-9]+)/delete/$', views.GoldPolicyDelete.as_view(), name='gold_policy_delete'),
    url(r'^goldpolicies/(?P<pk>[0-9]+)/confirmdelete/$', views.GoldPolicyConfirmDelete.as_view(), name='gold_policy_confirm_delete'),
]

# Green policy forms
urlpatterns += [
    url(r'^(?P<pk>[0-9]+)/newgreenpolicy/$', views.GreenPolicyCreate.as_view(), name='green_policy_add'),
    url(r'^greenpolicies/(?P<pk>[0-9]+)/edit/$', views.GreenPolicyUpdate.as_view(), name='green_policy_update'),
    url(r'^greenpolicies/(?P<pk>[0-9]+)/delete/$', views.GreenPolicyDelete.as_view(), name='green_policy_delete'),
    url(r'^greenpolicies/(?P<pk>[0-9]+)/confirmdelete/$', views.GreenPolicyConfirmDelete.as_view(), name='green_policy_confirm_delete'),
]

# Epmc forms
urlpatterns += [
    url(r'^(?P<pk>[0-9]+)/newepmc/$', views.EpmcCreate.as_view(), name='epmc_add'),
    url(r'^epmc/(?P<pk>[0-9]+)/edit/$', views.EpmcUpdate.as_view(), name='epmc_update'),
    url(r'^epmc/(?P<pk>[0-9]+)/delete/$', views.EpmcDelete.as_view(), name='epmc_delete'),
    url(r'^epmc/(?P<pk>[0-9]+)/confirmdelete/$', views.EpmcConfirmDelete.as_view(), name='epmc_confirm_delete'),
]

# Deal forms
urlpatterns += [
    url(r'^(?P<pk>[0-9]+)/newdeal/$', views.DealCreate.as_view(), name='deal_add'),
    url(r'^deal/(?P<pk>[0-9]+)/edit/$', views.DealUpdate.as_view(), name='deal_update'),
    url(r'^deal/(?P<pk>[0-9]+)/delete/$', views.DealDelete.as_view(), name='deal_delete'),
    url(r'^deal/(?P<pk>[0-9]+)/confirmdelete/$', views.DealConfirmDelete.as_view(), name='deal_confirm_delete'),
]

# Contact forms
urlpatterns += [
    url(r'^(?P<pk>[0-9]+)/newcontact/$', views.ContactCreate.as_view(), name='contact_add'),
    url(r'^contact/(?P<pk>[0-9]+)/edit/$', views.ContactUpdate.as_view(), name='contact_update'),
    url(r'^contact/(?P<pk>[0-9]+)/delete/$', views.ContactDelete.as_view(), name='contact_delete'),
    url(r'^contact/(?P<pk>[0-9]+)/confirmdelete/$', views.ContactConfirmDelete.as_view(), name='contact_confirm_delete'),
]

# Source forms
urlpatterns += [
    url(r'^source/add/$', views.SourceCreate.as_view(), name='source_add'),
    url(r'^source/(?P<pk>[0-9]+)/edit/$', views.SourceUpdate.as_view(), name='source_update'),
    url(r'^source/(?P<pk>[0-9]+)/delete/$', views.SourceDelete.as_view(), name='source_delete'),
    url(r'^source/(?P<pk>[0-9]+)/confirmdelete/$', views.SourceConfirmDelete.as_view(), name='source_confirm_delete'),
]

# Licence.json forms
urlpatterns += [
    url(r'^licence/add/$', views.LicenceCreate.as_view(), name='licence_add'),
]