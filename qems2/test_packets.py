from django.contrib.auth.models import User
import django

from qems2.qsub.models import *
from qems2.qsub.model_utils import *
from django.test.client import Client

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
        self.password = "top_secret"
        self.user = User.objects.create_user(username=user, password=self.password, email="qems2test@gmail.com")
        self.user.save()

        self.otherWriterUser = User.objects.create_user(username="otherwriter", password=self.password)
        self.otherWriterUser.save()

        self.nonWriterUser = User.objects.create_user(username="nonwriter", password=self.password)
        self.nonWriterUser.save()
                        
        self.writer = Writer.objects.get(user=self.user.id)
        self.writer.save()

        self.otherWriter = Writer.objects.get(user=self.otherWriterUser.id)
        self.otherWriter.save()

        self.dist = Distribution.objects.create(name="Test Distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        self.dist.save()

        self.euroHistory = DistributionEntry(category="History", subcategory="European", distribution=self.dist)
        self.euroHistory.save()

        self.worldLit = DistributionEntry(category="Literature", subcategory="Wordl", distribution=self.dist)
        self.worldLit.save()

        self.qset = QuestionSet.objects.create(name="new_set", date=timezone.now(), host="test host", owner=self.writer, num_packets=10, distribution=self.dist)
        self.qset.save()

        self.qset.writer.add(self.otherWriter)

        # Test user must be logged in for packet-related calls to pass
        self.client.login(username=user, password=self.password)


    def test_add_packet_packet_name(self):
        packet_name = "new_packet"
        data = { "packet_name": packet_name }
        url = self._get_add_packet_url()
        
        self._check_post(self.client, url, data, "success", "Packet creation did not return a success message.")
        
        packet_query = Packet.objects.filter(question_set=self.qset, packet_name=packet_name)
        self.assertTrue(packet_query.exists(), "Packet was not saved.")

    def test_other_writer_add_packet_packet_name(self):
        packet_name = "new_packet"
        data = { "packet_name": packet_name }
        url = self._get_add_packet_url()

        client = Client()
        client.login(username=self.otherWriterUser.username, password=self.password)

        self._check_post(client, url, data, "alert", "Packet creation did not return a warning message.")
        
        packet_query = Packet.objects.filter(question_set=self.qset, packet_name=packet_name)
        self.assertFalse(packet_query.exists(), "Packet should not have been saved.")

    def test_add_packet_name_base(self):
        packet_name = "new_packet"
        data = { "name_base": packet_name, "num_packets": "2" }
        url = self._get_add_packet_url()

        self._check_post(self.client, url, data, "success", "Packet creation did not return a success message.")
        
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
        url = self._get_add_packet_url()

        self._check_post(self.client, url, data, "success", "Packet creation did not return a success message.")

        # We should see a failure due to the same packet being added
        self._check_post(self.client, url, data, "warning", "Duplicate packet creation did not return a warning message when using packet_name.")

        # We should see a failure when using the base approach
        data = { "name_base": "new_packet", "num_packets": "1" }
        self._check_post(self.client, url, data, "warning", "Duplicate packet creation did not return a warning message when using name_base.")
        
        packet_query = Packet.objects.filter(question_set=self.qset, packet_name=packet_name)
        self.assertEqual(1, packet_query.count(), "Wrong number of packets were saved.")

    def _get_add_packet_url(self):
        return "/add_packets/{0}/".format(self.qset.id)

    def _check_post(self, client, url, data, alert_box_type, assert_message):
        response = client.post(url, data)
        self.assertEqual(200, response.status_code, "Unexpected status code.")
        self.assertNotEqual(-1, response.content.find("alert-box " + alert_box_type), assert_message)
