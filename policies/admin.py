from django import forms
from django.contrib.admin import AdminSite
from django.contrib import admin, messages
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.admin.helpers import ActionForm

from .models import Node, Source, OaStatus, GoldPolicy, GreenPolicy, RetrospectiveOaPolicy, Contact, Version, Licence, \
    Outlet, Responsibility, Note#, Output

class UpdateNodeActionForm(ActionForm):
    parent_id = forms.IntegerField(required=False)

class MyAdminSite(AdminSite):
    site_header = 'Orpheus administration'
    site_title = 'Orpheus site admin'

admin_site = MyAdminSite(name='myadmin')

class OaStatusInline(admin.StackedInline):
    model = OaStatus
    extra = 0

class GoldPolicyInline(admin.StackedInline):
    model = GoldPolicy
    extra = 0

class GreenPolicyInline(admin.StackedInline):
    model = GreenPolicy
    extra = 0

class RetrospectiveOaPolicyInline(admin.StackedInline):
    model = RetrospectiveOaPolicy
    extra = 0

class ContactInline(admin.StackedInline):
    model = Contact
    extra = 0

class SourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'description', 'url', 'type', 'created', 'updated']
    list_filter = ['type']
    search_fields = ['description', 'url']

class NodeAdmin(admin.ModelAdmin):
    action_form = UpdateNodeActionForm
    actions = ['update_parent']
    list_display = ['id', 'name', 'issn', 'parent', 'type', 'created', 'updated']
    list_filter = ['name_status', 'type', 'created', 'updated']
    search_fields = ['id', 'name', 'parent__id', 'parent__name']
    #inlines = [OaStatusInline, GreenPolicyInline, GoldPolicyInline, RetrospectiveOaPolicyInline, ContactInline]

    def update_parent(self, request, queryset):
        jqueryset = queryset.exclude(type='PUBLISHER')
        if jqueryset != queryset:
            self.message_user(request, "Selection includes publisher nodes {}. "
                                       "These were NOT updated".format(
                list(queryset.filter(type='PUBLISHER').values_list('id', flat=True).order_by('id'))
            ),
                              level=messages.WARNING)
        parent_id = request.POST['parent_id']
        print('parent_id: {} ({})'.format(parent_id, type(parent_id)))
        if not parent_id:
            self.message_user(request, "'Parent id' field is empty. Please enter the id of the new parent node",
                              level=messages.ERROR)
        else:
            parent_id = int(parent_id)
            qc = jqueryset.count()
            jqueryset.update(parent=parent_id)
            self.message_user(request, "Successfully updated parent of {} rows".format(qc))
    update_parent.short_description = 'Update parent of selected rows'

admin_site.register(Group, GroupAdmin) # https://stackoverflow.com/a/32614359
admin_site.register(User, UserAdmin)
admin_site.register(Node, NodeAdmin)
#admin_site.register(Node)
admin_site.register(Source, SourceAdmin)
admin_site.register(OaStatus)
admin_site.register(GoldPolicy)
admin_site.register(GreenPolicy)
admin_site.register(RetrospectiveOaPolicy)
admin_site.register(Contact)
admin_site.register(Version)
admin_site.register(Licence)
admin_site.register(Outlet)
admin_site.register(Responsibility)
admin_site.register(Note)
# admin_site.register(Output)