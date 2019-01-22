from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from .models import Node

TEST_ISSN = '1111-1111'
TEST_NAME = 'Test Journal'

def create_node(name, issn=None, eissn=None):
    """
    Create a node with given name
    :param name:
    :return:
    """
    return Node.objects.create(name=name, name_status='PRIMARY', type='JOURNAL', issn=issn, eissn=eissn)

class CambridgeListAPIViewTests(TestCase):

    def test_node_name(self):
        """
        Sanity check test of the simplest case
        """
        create_node(TEST_NAME)
        response = self.client.get(reverse('policies:api_cambridge'), {'name': TEST_NAME})
        self.assertContains(response, TEST_NAME)

    def test_node_name_containing_brackets(self):
        """
        The API should support node names containing brackets
        """
        test_name = 'Test Journal (Cambridge, UK)'
        create_node(test_name)
        response = self.client.get(reverse('policies:api_cambridge'), {'name': test_name})
        self.assertContains(response, test_name)

    def test_name_search_after_issn_seach_attempt_failed(self):
        """
        If a search by issn returns no results, a search by name should be attempted
        """
        create_node(TEST_NAME, TEST_ISSN)
        response = self.client.get(reverse('policies:api_cambridge'), {'name': TEST_NAME, 'issn': '2222-2222'})
        self.assertContains(response, TEST_NAME)

    def test_homonyms_are_returned(self):
        """
        Test that homonyms are returned
        """
        test_name = 'Test Journal (Cambridge, UK)'
        create_node(TEST_NAME)
        create_node(test_name)
        response = self.client.get(reverse('policies:api_cambridge'), {'name': TEST_NAME})
        self.assertContains(response, test_name)


