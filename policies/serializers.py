from rest_framework import serializers
from . import models

# class OutletSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Outlet
#         fields = '__all__'
#
# class VersionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Version
#         fields = '__all__'

class LicenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Licence
        fields = '__all__'

class OutletSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Outlet
        fields = '__all__'

class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Version
        fields = '__all__'

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Source
        fields = '__all__'

class GoldPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GoldPolicy
        fields = '__all__'

class GreenPolicySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GreenPolicy
        fields = '__all__'

class GreenPolicySerializer(serializers.ModelSerializer):
    outlet = serializers.StringRelatedField(many=True)
    version = serializers.StringRelatedField(many=True)
    version_green_licence = serializers.StringRelatedField()
    source = SourceSerializer(read_only=True)

    class Meta:
        model = models.GreenPolicy
        fields = '__all__'

class OaStatusSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OaStatus
        fields = '__all__'

class OaStatusSerializer(serializers.ModelSerializer):
    source = SourceSerializer(read_only=True)

    class Meta:
        model = models.OaStatus
        fields = '__all__'

class DealSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Deal
        fields = '__all__'

class DealSerializer(serializers.ModelSerializer):
    source = SourceSerializer(read_only=True)

    class Meta:
        model = models.Deal
        fields = '__all__'

class EpmcSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Epmc
        fields = '__all__'

class EpmcSerializer(serializers.ModelSerializer):
    source = SourceSerializer(read_only=True)

    class Meta:
        model = models.Epmc
        fields = '__all__'

class NodeSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Node
        fields = '__all__'

class NodeSummarySerializer(serializers.ModelSerializer):

    most_reliable_oa_status = serializers.ReadOnlyField()
    most_reliable_green_policies_for_ir = serializers.ReadOnlyField()
    most_reliable_gold_policy = serializers.ReadOnlyField()

    class Meta:
        model = models.Node
        fields = ['id', 'name', 'name_status', 'type', 'url', 'issn', 'eissn', 'synonym_of', 'parent', 'source',
                  'vetted', 'vetted_date', 'created', 'updated',
                  'most_reliable_oa_status', 'most_reliable_green_policies_for_ir', 'most_reliable_gold_policy']

class CambridgeSerializer(serializers.ModelSerializer):
    '''
    Personalised serializer for Apollo/ZD integration
    '''

    apollo_am_embargo_months = serializers.ReadOnlyField()
    apollo_vor_embargo_months = serializers.ReadOnlyField()
    zd_publisher = serializers.ReadOnlyField()
    zd_green_allowed_version = serializers.ReadOnlyField()
    zd_embargo_duration = serializers.ReadOnlyField()
    zd_green_licence = serializers.ReadOnlyField()
    zd_journal_oa_status = serializers.ReadOnlyField()
    zd_apc_range = serializers.ReadOnlyField()
    zd_gold_licence_options = serializers.ReadOnlyField()
    zd_commitment_guidance = serializers.ReadOnlyField()
    zd_deal = serializers.ReadOnlyField()
    zd_epmc_participation = serializers.ReadOnlyField()
    zd_epmc_embargo_months = serializers.ReadOnlyField()
    zd_epmc_open_licence = serializers.ReadOnlyField()
    zd_epmc_deposit_status = serializers.ReadOnlyField()
    romeo_url = serializers.ReadOnlyField()
    preferred_name = serializers.ReadOnlyField()

    class Meta:
        model = models.Node
        fields = ['id', 'name', 'preferred_name', 'issn', 'eissn', 'url', 'apollo_am_embargo_months', 'apollo_vor_embargo_months',
                  'zd_publisher', 'zd_green_allowed_version', 'zd_embargo_duration', 'zd_green_licence',
                  'zd_journal_oa_status', 'zd_apc_range', 'zd_gold_licence_options', 'zd_commitment_guidance',
                  'zd_deal', 'zd_epmc_participation', 'zd_epmc_embargo_months', 'zd_epmc_open_licence',
                  'zd_epmc_deposit_status', 'romeo_url']

class BaseNodeSerializer(serializers.ModelSerializer):
    synonyms = NodeSimpleSerializer(many=True, read_only=True)
    gold_policies = GoldPolicySerializer(many=True, read_only=True)
    green_policies = GreenPolicySerializer(many=True,
                                           #read_only=True
                                           )
    oa_stata = OaStatusSerializer(many=True, read_only=True)
    source = SourceSerializer(read_only=True)

    class Meta:
        model = models.Node
        fields = ['id', 'name', 'name_status', 'type', 'url', 'issn', 'eissn', 'synonym_of', 'parent', 'source',
                  'vetted', 'vetted_date', 'created', 'updated', 'gold_policies', 'green_policies', 'oa_stata',
                  'synonyms']

    def create(self, validated_data):
        green_policies_data = validated_data.pop('green_policies')
        node = models.Node.objects.create(**validated_data)
        for green_policy_data in green_policies_data:
            models.GreenPolicy.objects.create(node=node, **green_policy_data)

class ParentSerializer(BaseNodeSerializer):
    '''
    This subclass is needed only to resolve info for the parent
    node of `synonym_of` in NodeSerializer
    '''
    parent = BaseNodeSerializer(read_only=True)

    class Meta(BaseNodeSerializer.Meta):
        pass

class NodeSerializer(BaseNodeSerializer):
    parent = BaseNodeSerializer(read_only=True)
    synonym_of = ParentSerializer(read_only=True)

    class Meta(BaseNodeSerializer.Meta):
        pass