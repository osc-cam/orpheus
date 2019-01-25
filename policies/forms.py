from django import forms
from django.core.urlresolvers import reverse_lazy
from django_addanother.widgets import AddAnotherWidgetWrapper, AddAnotherEditSelectedWidgetWrapper
from dal import autocomplete
from . import models

# region Node forms
class NodeForm(forms.ModelForm):
    vetted = forms.BooleanField(disabled=True)
    vetted_date = forms.DateTimeField(disabled=True)

    class Meta:
        model = models.Node
        fields = '__all__'
        widgets = {
            'synonym_of': AddAnotherWidgetWrapper(
                autocomplete.ModelSelect2(url='policies:node_autocomplete', forward=['type']),
                reverse_lazy('policies:node_add'),
            ),
            'parent': AddAnotherWidgetWrapper(
                autocomplete.ModelSelect2(url='policies:publisher_autocomplete'),
                reverse_lazy('policies:node_add'),
            ),
            'source': AddAnotherWidgetWrapper(
                autocomplete.ModelSelect2(url='policies:source_autocomplete'),
                # forms.Select,
                reverse_lazy('policies:source_add'),
            ),
        }

class ChildNodeForm(NodeForm):
    '''
    Subclass of NodeForm for adding children nodes
    '''

    class Meta(NodeForm.Meta): # https://docs.djangoproject.com/en/1.11/topics/db/models/#meta-inheritance
        exclude = ['parent']

class PublisherNodeForm(NodeForm):
    '''
    Subclass of NodeForm for adding publisher nodes
    '''
    name = forms.CharField(label='Publisher name')

    class Meta(NodeForm.Meta):
        exclude = ['issn', 'eissn', 'type', 'parent', 'epmc_url']

class JournalNodeForm(NodeForm):
    '''
    Subclass of NodeForm for adding journal nodes
    '''
    name = forms.CharField(label='Journal name')

    class Meta(NodeForm.Meta):
        exclude = ['type', 'romeo_id']

class ConferenceNodeForm(NodeForm):
    '''
    Subclass of NodeForm for adding conference nodes
    '''
    name = forms.CharField(label='Conference name')

    class Meta(NodeForm.Meta):
        exclude = ['type', 'romeo_id']

# endregion

class DeleteForm(forms.ModelForm):
    class Meta:
        model = models.Note
        fields = ['text']
        labels = {'text': 'Reason', }

class SourceForm(forms.ModelForm):
    class Meta:
        model = models.Source
        fields = '__all__'

class LicenceForm(forms.ModelForm):
    class Meta:
        model = models.Licence
        fields = '__all__'

class ListViewSearchForm(forms.Form):
    search_text = forms.CharField(label='Phrase match',
                                  required=False,
                                  widget=forms.TextInput(attrs={'placeholder': 'name or issn'})
                                  )
    search_name_exact = forms.CharField(label='Exact match',
                                  required=False,
                                  widget=forms.TextInput(attrs={'placeholder': 'name or issn'})
                                  )

class ListViewSearchFormSources(forms.Form):
    search_text = forms.CharField(label='Phrase match',
                                  required=False,
                                  widget=forms.TextInput(attrs={'placeholder': 'name or url'})
                                  )
    search_name_exact = forms.CharField(label='Exact match',
                                  required=False,
                                  widget=forms.TextInput(attrs={'placeholder': 'name or url'})
                                  )

# region policies
class NodeAttributeForm(forms.ModelForm):
    vetted = forms.BooleanField(disabled=True)
    vetted_date = forms.DateTimeField(disabled=True)

    class Meta:
        exclude = ['node']
        widgets = {
            'source': AddAnotherWidgetWrapper(
                autocomplete.ModelSelect2(url='policies:source_autocomplete'),
                # forms.Select,
                reverse_lazy('policies:source_add'),
            ),
            'vetted_date': forms.DateInput(
                attrs={'type': 'date'}  # https://stackoverflow.com/a/41942774
            ),
            'last_checked': forms.DateInput(
                attrs={'type': 'date'}  # https://stackoverflow.com/a/41942774
            ),
            'superseded_date': forms.DateInput(
                attrs={'type': 'date'}  # https://stackoverflow.com/a/41942774
            ),
            'default_licence': AddAnotherWidgetWrapper( # Gold policy field
                forms.Select,
                reverse_lazy('policies:licence_add'),
            ),
            'version_green_licence': AddAnotherWidgetWrapper( # Green policy field
                forms.Select,
                reverse_lazy('policies:licence_add'),
            ),
            'outlet': forms.SelectMultiple(
                attrs={'size': 8}
            ),
            'version': forms.SelectMultiple(
                attrs={'size': 5}
            ),
        }

class OaStatusForm(NodeAttributeForm):
    class Meta(NodeAttributeForm.Meta):
        model = models.OaStatus

class GoldPolicyForm(NodeAttributeForm):
    class Meta(NodeAttributeForm.Meta):
        model = models.GoldPolicy

class GreenPolicyForm(NodeAttributeForm):
    class Meta(NodeAttributeForm.Meta):
        model = models.GreenPolicy

class EpmcForm(NodeAttributeForm):
    class Meta(NodeAttributeForm.Meta):
        model = models.Epmc

class DealForm(NodeAttributeForm):
    class Meta(NodeAttributeForm.Meta):
        model = models.Deal
# endregion

class ContactForm(forms.ModelForm):
    class Meta:
        model = models.Contact
        exclude = ['node']

# region Note forms
class NoteForm(forms.ModelForm):
    class Meta:
        model = models.Note
        fields = ['text']
        labels = {'text': 'Note', }
# endregion