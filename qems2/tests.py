from django.test import SimpleTestCase

from qems2.qsub.packet_parser import is_answer, is_bpart, is_vhsl_bpart, is_category
from qems2.qsub.packet_parser import parse_packet_data, get_bonus_part_value, remove_category
from qems2.qsub.packet_parser import remove_answer_label, format_answerline_underscores

class PacketParserTests(SimpleTestCase):
    def test_is_answer(self):
        answers = ["answer:", "Answer:", "ANSWER:", "ANSWER: _underlined_", "ANSWER: no underline", "ANSWER: <u>underline2</u>"]
        for answer in answers:
            self.assertTrue(is_answer(answer), msg=answer)
        non_answers = ["question:", "answer", "ansER"]
        for non_answer in non_answers:
            self.assertFalse(is_answer(non_answer), msg=non_answer)
    def test_remove_answer_label(self):
        answers = ["ANSWER: <b><u>my answer</b></u>", "answer:      <b><u>my answer</b></u>", "Answer:\t<b><u>my answer</b></u>"]
        for answer in answers:
            self.assertEqual(remove_answer_label(answer), '<b><u>my answer</b></u>')
    def test_format_answerline_underscores(self):
        answer = "ANSWER: _Charles I_ [or <b><u>Charles the Bad</b></u> or _Charles The Dangling Underscore]"
        self.assertEqual(format_answerline_underscores(answer), "ANSWER: <b><u>Charles I</b></u> [or <b><u>Charles the Bad</b></u> or <b><u>Charles The Dangling Underscore]</b></u>")        
    def test_is_bpart(self):
        bonusParts = ['[10]', '[15]', '(10)', '(15)']
        for bonusPart in bonusParts:
            self.assertTrue(is_bpart(bonusPart), msg=bonusPart)
        notBonusParts = ['10', '[10', '10]', '(10]', '[10)', '[or foo]', '(not a number)']
        for notBonus in notBonusParts:
            self.assertFalse(is_bpart(notBonus), msg=notBonus)
    def test_is_vhsl_bpart(self):
        bonusParts = ['[V10]', '[V15]', '(V10)', '(V15)']
        for bonusPart in bonusParts:
            self.assertTrue(is_vhsl_bpart(bonusPart), msg=bonusPart)
        notBonusParts = ['[10]', '(10)', 'V10', '[10', '10]', '(10]', '[V10)', '[or foo]', '(not a number)']
        for notBonus in notBonusParts:
            self.assertFalse(is_vhsl_bpart(notBonus), msg=notBonus)
    def test_is_category(self):
        categories = ["{History - European}, 'ANSWER: _foo_ {Literature - American}"]
        for category in categories:
            self.assertTrue(is_category(category), msg=category)
        notCategories = ["answer: _foo_", '{History - World', 'History - Other}']
        for notCategory in notCategories:
            self.assertFalse(is_category(notCategory), msg=notCategory)
    def test_remove_category(self):
        self.assertEqual(remove_category('ANSWER: _foo_ {History - European}'), 'ANSWER: _foo_ ')
        self.assertEqual(remove_category('ANSWER: _foo_ {History - European'), 'ANSWER: _foo_ {History - European')
    def test_get_bonus_part_value(self):
        bonusParts = ['[10]', '(10)']
        for bonusPart in bonusParts:
            self.assertEqual(get_bonus_part_value(bonusPart), '10')        
    def test_parse_packet_data(self):
        validTossup = 'This is a valid test tossup.\nANSWER: <b><u>My Answer</b></u>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validTossup.splitlines())
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].question, 'This is a valid test tossup.');
        self.assertEqual(tossups[0].answer, '<b><u>My Answer</b></u>');
        self.assertEqual(tossups[0].category, '');
        
        validTossupWithCategory = 'This should be a European History tossup.\nANSWER: <b><u>Charles I</b></u> {History - European}'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validTossupWithCategory.splitlines())
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].question, 'This should be a European History tossup.');
        self.assertEqual(tossups[0].answer, '<b><u>Charles I</b></u> ');
        self.assertEqual(tossups[0].category, 'History - European');        

        validBonus = 'This is a valid bonus.  For 10 points each:\n[10] Prompt 1.\nANSWER: <b><u>Answer 1</b></u>\n[10] Prompt 2.\nANSWER: <b><u>Answer 2</b></u>\n[10] Prompt 3.\nANSWER: <b><u>Answer 3</b></u>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validBonus.splitlines())
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(bonuses[0].type, 'acf')
        self.assertEqual(bonuses[0].leadin, 'This is a valid bonus.  For 10 points each:')
        self.assertEqual(bonuses[0].parts[0], 'Prompt 1.')
        self.assertEqual(bonuses[0].answers[0], '<b><u>Answer 1</b></u>')
        self.assertEqual(bonuses[0].parts[1], 'Prompt 2.')
        self.assertEqual(bonuses[0].answers[1], '<b><u>Answer 2</b></u>')
        self.assertEqual(bonuses[0].parts[2], 'Prompt 3.')
        self.assertEqual(bonuses[0].answers[2], '<b><u>Answer 3</b></u>') 
        
        validBonusWithCategory = validBonus + " {History - American}"
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validBonusWithCategory.splitlines())
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(bonuses[0].category, "History - American");    
        
        validVHSLBonus = '[V10] This is a valid VHSL bonus.\nANSWER: <b><u>VHSL Answer</b></u>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validVHSLBonus.splitlines())
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(bonuses[0].type, 'vhsl')
        self.assertEqual(bonuses[0].leadin, '')
        self.assertEqual(bonuses[0].parts[0], 'This is a valid VHSL bonus.')
        self.assertEqual(bonuses[0].answers[0], '<b><u>VHSL Answer</b></u>')
        
        multipleQuestions = 'This is tossup 1.\nANSWER: _Tossup 1 Answer_\n[V10] This is a VHSL bonus.\nANSWER: _VHSL Answer_\nThis is another tossup.\nANSWER: _Tossup 2 Answer_'
        multipleQuestions += '\n' + validBonus
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(multipleQuestions.splitlines())
        self.assertEqual(len(bonuses), 2)
        self.assertEqual(len(tossups), 2)
        self.assertEqual(tossups[0].question, 'This is tossup 1.')
        self.assertEqual(tossups[0].answer, '<b><u>Tossup 1 Answer</b></u>')
        self.assertEqual(tossups[1].question, 'This is another tossup.')
        self.assertEqual(tossups[1].answer, '<b><u>Tossup 2 Answer</b></u>')
        self.assertEqual(bonuses[0].parts[0], 'This is a VHSL bonus.')
        self.assertEqual(bonuses[0].answers[0], '<b><u>VHSL Answer</b></u>')
        self.assertEqual(bonuses[0].type, 'vhsl')
        self.assertEqual(bonuses[1].type, 'acf')
        self.assertEqual(bonuses[1].leadin, 'This is a valid bonus.  For 10 points each:')
        self.assertEqual(bonuses[1].parts[0], 'Prompt 1.')
        self.assertEqual(bonuses[1].answers[0], '<b><u>Answer 1</b></u>')
        self.assertEqual(bonuses[1].parts[1], 'Prompt 2.')
        self.assertEqual(bonuses[1].answers[1], '<b><u>Answer 2</b></u>')
        self.assertEqual(bonuses[1].parts[2], 'Prompt 3.')
        self.assertEqual(bonuses[1].answers[2], '<b><u>Answer 3</b></u>')    
        
        multipleQuestionsBlankLines = 'This is tossup 1.\nANSWER: _Tossup 1 Answer_\n\n\nThis is tossup 2.\nANSWER: _Tossup 2 Answer_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(multipleQuestionsBlankLines.splitlines())
        self.assertEqual(len(bonuses), 0)
        self.assertEqual(len(tossups), 2)
        self.assertEqual(tossups[0].question, 'This is tossup 1.')
        self.assertEqual(tossups[0].answer, '<b><u>Tossup 1 Answer</b></u>')
        self.assertEqual(tossups[1].question, 'This is tossup 2.')
        self.assertEqual(tossups[1].answer, '<b><u>Tossup 2 Answer</b></u>')
        
        tossupWithoutAnswer = 'This is not a valid tossup.  It does not have an answer.'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithoutAnswer.splitlines())
        self.assertEqual(len(tossups), 0)
        self.assertEqual(len(bonuses), 0)
        
        tossupWithLineBreaks = 'This is not a valid tossup.\nIt has a line break before its answer.\nANSWER: _foo_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithLineBreaks.splitlines())
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].question, 'It has a line break before its answer.');
        self.assertEqual(tossups[0].answer, '<b><u>foo</b></u>');        
        self.assertEqual(len(bonuses), 0)
        
        tossupWithoutQuestion = 'ANSWER: This is an answer line without a question'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithoutQuestion.splitlines())
        self.assertEqual(len(tossups), 0)
        self.assertEqual(len(bonuses), 0)
        self.assertEqual(len(tossup_errors), 1)
        
