import django.test
from qems2.qsub.packet_parser import is_answer

class PacketParserTestCase(django.test.TestCase):
    def test_is_answer(self):
        answers = ["answer:", "Answer:", "ANSWER:"]
        for answer in answers:
            self.assertTrue(is_answer(answer), msg=answer)
        non_answers = ["question:", "answer", "ansER", "asnwer:"]
        for non_answer in non_answers:
            self.assertFalse(is_answer(non_answer), msg=non_answer)
