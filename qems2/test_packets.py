from django.contrib.auth.models import User
import django

from qems2.qsub.models import *
from qems2.qsub.model_utils import *

class PacketsViewTests(django.test.TestCase):

    if django.VERSION[:2] == (1, 7):
        # Django 1.7 requires an explicit setup() when running tests in PTVS
        @classmethod
        def setUpClass(cls):
            django.setup()
    elif django.VERSION[:2] >= (1, 8):
        # Django 1.8 requires a different setup. See https://github.com/Microsoft/PTVS-Samples/issues/1
        @classmethod
        def setUpClass(cls):
            super(DjangoTestCase, cls).setUpClass()
            django.setup()

    def setUp(self):
        user = "testuser"
        password = "top_secret"
        self.user = User.objects.create_user(username=user, password=password, email="qems2test@gmail.com")
        self.user.save()
                        
        self.writer = Writer.objects.get(user=self.user.id)
        self.writer.save()

        self.dist = Distribution.objects.create(name="Test Distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        self.dist.save()

        self.euroHistory = DistributionEntry(category="History", subcategory="European", distribution=self.dist)
        self.euroHistory.save()

        self.qset = QuestionSet.objects.create(name="new_set", date=timezone.now(), host="test host", owner=self.writer, num_packets=10, distribution=self.dist)
        self.qset.save()

        # Test user must be logged in for packet-related calls to pass
        response = self.client.login(username=user, password=password)


    def test_add_packet_packet_name(self):
        packet_name = "new_packet"
        data = { "packet_name": packet_name }
        url = self._get_packet_url()

        response = self.client.post(url, data)
        self.assertEqual(200, response.status_code, "Request should have succeeded.")
        self.assertNotEqual(
            -1, response.content.find("alert-box success"), "Packet creation did not return a success message.")
        
        packet_query = Packet.objects.filter(question_set=self.qset, packet_name=packet_name)
        self.assertTrue(packet_query.exists(), "Packet was not saved.")

    def test_add_packet_name_base(self):
        packet_name = "new_packet"
        data = { "name_base": packet_name, "num_packets": "2" }
        url = self._get_packet_url()

        response = self.client.post(url, data)
        self.assertEqual(200, response.status_code, "Request should have succeeded.")
        self.assertNotEqual(
            -1, response.content.find("alert-box success"), "Packet creation did not return a success message.")
        
        first_packet_name = packet_name + " 01"
        packet_query = Packet.objects.filter(question_set=self.qset, packet_name=first_packet_name)
        self.assertTrue(packet_query.exists(), "First packet was not saved.")
        second_packet_name = packet_name + " 02"
        packet_query = Packet.objects.filter(question_set=self.qset, packet_name=second_packet_name)
        self.assertTrue(packet_query.exists(), "Second packet was not saved.")

        third_packet_name = packet_name + " 03"
        packet_query = Packet.objects.filter(question_set=self.qset, packet_name=third_packet_name)
        self.assertFalse(packet_query.exists(), "There should be no third packet.")

    def test_add_same_packet(self):
        packet_name = "new_packet 01"
        data = { "packet_name": packet_name }
        url = self._get_packet_url()

        response = self.client.post(url, data)
        self.assertEqual(200, response.status_code, "First request should have succeeded.")
        self.assertNotEqual(
            -1, response.content.find("alert-box success"), "Packet creation did not return a success message.")

        # We should see a failure due to the same packet being added
        response = self.client.post(url, data)
        self.assertEqual(200, response.status_code, "Second request should have succeeded.")
        self.assertNotEqual(
            -1,
            response.content.find("alert-box warning"),
            "Duplicate packet creation did not return a warning message when using packet_name.")

        # We should see a failure when using the base approach
        data = { "name_base": "new_packet", "num_packets": "1" }
        response = self.client.post(url, data)
        self.assertEqual(200, response.status_code, "Third request should have succeeded.")
        self.assertNotEqual(
            -1,
            response.content.find("alert-box warning"),
            "Duplicate packet creation did not return a warning message when using .")
        
        packet_query = Packet.objects.filter(question_set=self.qset, packet_name=packet_name)
        self.assertEqual(1, packet_query.count(), "Wrong number of packets were saved.")

    def _get_packet_url(self):
        return "/add_packets/{0}/".format(self.qset.id)
