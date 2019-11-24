from django.contrib.auth.models import User
import django
from django.test import TestCase

from qems2.qsub.models import *
from qems2.qsub.model_utils import *
from django.test.client import Client

class PacketsViewTests(TestCase):

    # TODO: Determine if we really need this block of code anymore
    #if django.VERSION[:2] == (1, 7):
    #    # Django 1.7 requires an explicit setup() when running tests in PTVS
    #    @classmethod
    #    def setUpClass(cls):
    #        django.setup()
    #elif django.VERSION[:2] >= (1, 8):
    #    # Django 1.8 requires a different setup. See https://github.com/Microsoft/PTVS-Samples/issues/1
    #    @classmethod
    #    def setUpClass(cls):
    #        super(DjangoTestCase, cls).setUpClass()
    #        django.setup()

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

        self.packet = Packet.objects.create(packet_name="test_packet", date_submitted=datetime.now(), question_set=self.qset, created_by=self.writer)
        self.packet.save()

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

    def test_edit_packet_question_numbers(self):
        # Regression test for #185: TU/B in packet doesn't have question_number
        current_date = datetime.now()
        tossup1 = Tossup.objects.create(
            packet=self.packet, question_set=self.qset, tossup_text="Tossup 1", tossup_answer="Answer 1", author=self.writer,
            created_date=current_date, last_changed_date=current_date, question_number=0)
        tossup1.save()
        tossup2 = Tossup.objects.create(
            packet=self.packet, question_set=self.qset, tossup_text="Tossup 2", tossup_answer="Answer 2", author=self.writer,
            created_date=current_date, last_changed_date=current_date, question_number=1)
        tossup2.save()

        bonus1 = Bonus.objects.create(
            packet=self.packet, question_set=self.qset, part1_text="Part 1", part1_answer="Answer 1", part2_text="Part 2",
            part2_answer="Answer 2", part3_text="Part 3", part3_answer="Answer 3", author=self.writer,
            created_date=current_date, last_changed_date=current_date, question_number=0, leadin="Leadin")
        bonus1.save()
        bonus2 = Bonus.objects.create(
            packet=self.packet, question_set=self.qset, part1_text="Tossup 2", part1_answer="Answer 2", part2_text="Part 2",
            part2_answer="Answer 2", part3_text="Part 3", part3_answer="Answer 3", author=self.writer,
            created_date=current_date, last_changed_date=current_date, question_number=1, leadin="Leadin")
        bonus2.save()

        url = self._get_edit_packet_url()
        response = self.client.get(url)
        self.assertEqual(200, response.status_code, "Unexpected status code.")

        content = response.content
        tossupsIndex = content.find("id=\"tossups\"")
        bonusesIndex = content.find("id=\"bonuses\"")
        self.assertNotEqual(-1, tossupsIndex, "Could not find Tossups section.")
        self.assertNotEqual(-1, bonusesIndex, "Could not find Bonuses section.")
        self.assertGreater(bonusesIndex, tossupsIndex, "Bonuses section appears before the tossups section.")

        tossups = content[tossupsIndex:bonusesIndex]
        bonuses = content[bonusesIndex:]
        self.assertNotEqual(-1, tossups.find("<td> 1 </td>"), "Could not find #1 label in Tossups")
        self.assertNotEqual(-1, tossups.find("<td> 2 </td>"), "Could not find #2 label in Tossups")
        self.assertNotEqual(-1, bonuses.find("<td> 1 </td>"), "Could not find #1 label in Bonuses")
        self.assertNotEqual(-1, bonuses.find("<td> 2 </td>"), "Could not find #2 label in Bonuses")

    def _get_add_packet_url(self):
        return "/add_packets/{0}/".format(self.qset.id)

    def _get_edit_packet_url(self):
        return "/edit_packet/{0}/".format(self.packet.id)

    def _check_post(self, client, url, data, alert_box_type, assert_message):
        response = client.post(url, data)
        self.assertEqual(200, response.status_code, "Unexpected status code.")
        self.assertNotEqual(-1, response.content.find("alert-box " + alert_box_type), assert_message)
