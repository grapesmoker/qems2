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
        bonusParts = ['[10]', '[15]']
        for bonusPart in bonusParts:
            self.assertTrue(is_bpart(bonusPart), msg=bonusPart)
        notBonusParts = ['(10)', '10', '[10', '10]', '(10]', '[10)', '[or foo]', '(not a number)', '[10.5]', '[<i>10</i>]']
        for notBonus in notBonusParts:
            self.assertFalse(is_bpart(notBonus), msg=notBonus)
    def test_is_vhsl_bpart(self):
        bonusParts = ['[V10]', '[V15]']
        for bonusPart in bonusParts:
            self.assertTrue(is_vhsl_bpart(bonusPart), msg=bonusPart)
        notBonusParts = ['(V10)', '[10]', '(10)', 'V10', '[10', '10]', '(10]', '[V10)', '[or foo]', '(not a number)']
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
        bonusParts = ['[10]']
        for bonusPart in bonusParts:
            self.assertEqual(get_bonus_part_value(bonusPart), '10')        
    def test_parse_packet_data(self):
        validTossup = 'This is a valid test tossup.\nANSWER: _My Answer_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validTossup.splitlines())
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].question, 'This is a valid test tossup.');
        self.assertEqual(tossups[0].answer, '_My Answer_');
        self.assertEqual(tossups[0].category, '');
        
        validTossupWithCategory = 'This should be a ~European History~ tossup.\nANSWER: _Charles I_ {History - European}'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validTossupWithCategory.splitlines())
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].question, 'This should be a ~European History~ tossup.');
        self.assertEqual(tossups[0].answer, '_Charles I_ ');
        self.assertEqual(tossups[0].category, 'History - European');        

        validBonus = 'This is a valid bonus.  For 10 points each:\n[10] Prompt 1.\nANSWER: _Answer 1_\n[10] Prompt 2.\nANSWER: _Answer 2_\n[10] Prompt 3.\nANSWER: _Answer 3_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validBonus.splitlines())
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(bonuses[0].type, 'acf')
        self.assertEqual(bonuses[0].leadin, 'This is a valid bonus.  For 10 points each:')
        self.assertEqual(bonuses[0].parts[0], 'Prompt 1.')
        self.assertEqual(bonuses[0].answers[0], '_Answer 1_')
        self.assertEqual(bonuses[0].values[0], '10');
        self.assertEqual(bonuses[0].parts[1], 'Prompt 2.')
        self.assertEqual(bonuses[0].answers[1], '_Answer 2_')
        self.assertEqual(bonuses[0].values[1], '10');
        self.assertEqual(bonuses[0].parts[2], 'Prompt 3.')
        self.assertEqual(bonuses[0].answers[2], '_Answer 3_') 
        self.assertEqual(bonuses[0].values[2], '10');
        
        validBonusWithCategory = validBonus + " {History - American}"
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validBonusWithCategory.splitlines())
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(bonuses[0].category, "History - American");    
        
        validVHSLBonus = '[V10] This is a valid VHSL bonus.\nANSWER: _VHSL Answer_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validVHSLBonus.splitlines())
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(bonuses[0].type, 'vhsl')
        self.assertEqual(bonuses[0].leadin, '')
        self.assertEqual(bonuses[0].parts[0], 'This is a valid VHSL bonus.')
        self.assertEqual(bonuses[0].answers[0], '_VHSL Answer_')
        
        multipleQuestions = 'This is tossup 1.\nANSWER: _Tossup 1 Answer_\n[V10] This is a VHSL bonus.\nANSWER: _VHSL Answer_\nThis is another tossup.\nANSWER: _Tossup 2 Answer_'
        multipleQuestions += '\n' + validBonus
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(multipleQuestions.splitlines())
        self.assertEqual(len(bonuses), 2)
        self.assertEqual(len(tossups), 2)
        self.assertEqual(tossups[0].question, 'This is tossup 1.')
        self.assertEqual(tossups[0].answer, '_Tossup 1 Answer_')
        self.assertEqual(tossups[1].question, 'This is another tossup.')
        self.assertEqual(tossups[1].answer, '_Tossup 2 Answer_')
        self.assertEqual(bonuses[0].parts[0], 'This is a VHSL bonus.')
        self.assertEqual(bonuses[0].answers[0], '_VHSL Answer_')
        self.assertEqual(bonuses[0].type, 'vhsl')
        self.assertEqual(bonuses[1].type, 'acf')
        self.assertEqual(bonuses[1].leadin, 'This is a valid bonus.  For 10 points each:')
        self.assertEqual(bonuses[1].parts[0], 'Prompt 1.')
        self.assertEqual(bonuses[1].answers[0], '_Answer 1_')
        self.assertEqual(bonuses[1].parts[1], 'Prompt 2.')
        self.assertEqual(bonuses[1].answers[1], '_Answer 2_')
        self.assertEqual(bonuses[1].parts[2], 'Prompt 3.')
        self.assertEqual(bonuses[1].answers[2], '_Answer 3_')    
        
        multipleQuestionsBlankLines = 'This is tossup 1.\nANSWER: _Tossup 1 Answer_\n\n\nThis is tossup 2.\nANSWER: _Tossup 2 Answer_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(multipleQuestionsBlankLines.splitlines())
        self.assertEqual(len(bonuses), 0)
        self.assertEqual(len(tossups), 2)
        self.assertEqual(tossups[0].question, 'This is tossup 1.')
        self.assertEqual(tossups[0].answer, '_Tossup 1 Answer_')
        self.assertEqual(tossups[1].question, 'This is tossup 2.')
        self.assertEqual(tossups[1].answer, '_Tossup 2 Answer_')
        
        tossupWithoutAnswer = 'This is not a valid tossup.  It does not have an answer.'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithoutAnswer.splitlines())
        self.assertEqual(len(tossups), 0)
        self.assertEqual(len(bonuses), 0)
        
        tossupWithLineBreaks = 'This is not a valid tossup.\nIt has a line break before its answer.\nANSWER: _foo_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithLineBreaks.splitlines())
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].question, 'It has a line break before its answer.');
        self.assertEqual(tossups[0].answer, '_foo_');        
        self.assertEqual(len(bonuses), 0)
        
        tossupWithoutQuestion = 'ANSWER: This is an answer line without a question'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithoutQuestion.splitlines())
        self.assertEqual(len(tossups), 0)
        self.assertEqual(len(bonuses), 0)
        self.assertEqual(len(tossup_errors), 1)
        
        tossupWithSingleQuotes = "This is a tossup with 'single quotes' in it.\nANSWER: '_Single Quoted Answer_'"
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithSingleQuotes.splitlines())
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].question, "This is a tossup with &#39;single quotes&#39; in it.");
        self.assertEqual(tossups[0].answer, "&#39;_Single Quoted Answer_&#39;");
        
        tossupWithDoubleQuotes = 'This is a tossup with "double quotes" in it.\nANSWER: "_Double Quoted Answer_"'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithDoubleQuotes.splitlines())
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].question, 'This is a tossup with &quot;double quotes&quot; in it.');
        self.assertEqual(tossups[0].answer, '&quot;_Double Quoted Answer_&quot;');        
        
        tossupWithDoubleQuotes = 'This is a tossup with an <i>italic tag</i> in it.\nANSWER: <i>_Italic Answer_</i>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithDoubleQuotes.splitlines())
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].question, 'This is a tossup with an &lt;i&gt;italic tag&lt;/i&gt; in it.');
        self.assertEqual(tossups[0].answer, '&lt;i&gt;_Italic Answer_&lt;/i&gt;');
        
        bonusWithNonIntegerValues = 'This is a bonus with non-integer values.  For 10 points each:\n[A] Prompt 1.\nANSWER: _Answer 1_\n[10.5] Prompt 2.\nANSWER: _Answer 2_\n[10C] Prompt 3.\nANSWER: _Answer 3_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(bonusWithNonIntegerValues.splitlines())
        self.assertEqual(len(bonuses), 0)

        bonusWithHtmlValues = 'This is a bonus with html values.  For 10 points each:\n[<i>10</i>] Prompt 1.\nANSWER: _Answer 1_\n[10] Prompt 2.\nANSWER: _Answer 2_\n[<i>10</i>] Prompt 3.\nANSWER: _Answer 3_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(bonusWithHtmlValues.splitlines())
        self.assertEqual(len(bonuses), 0)        
        
        bonusWithQuotesAndHtml = 'This is a <i>valid</i> "bonus".  For 10 points each:\n[10] <i>Prompt 1</i>.\nANSWER: "_Answer 1_"\n[10] "Prompt 2."\nANSWER: <i>_Answer 2_</i>\n[10] <i>Prompt 3.</i>\nANSWER: <i>_Answer 3_</i>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(bonusWithQuotesAndHtml.splitlines())
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(bonuses[0].type, 'acf')
        self.assertEqual(bonuses[0].leadin, 'This is a &lt;i&gt;valid&lt;/i&gt; &quot;bonus&quot;.  For 10 points each:')
        self.assertEqual(bonuses[0].parts[0], '&lt;i&gt;Prompt 1&lt;/i&gt;.')
        self.assertEqual(bonuses[0].answers[0], '&quot;_Answer 1_&quot;')
        self.assertEqual(bonuses[0].values[0], '10');
        self.assertEqual(bonuses[0].parts[1], '&quot;Prompt 2.&quot;')
        self.assertEqual(bonuses[0].answers[1], '&lt;i&gt;_Answer 2_&lt;/i&gt;')
        self.assertEqual(bonuses[0].values[1], '10');
        self.assertEqual(bonuses[0].parts[2], '&lt;i&gt;Prompt 3.&lt;/i&gt;')
        self.assertEqual(bonuses[0].answers[2], '&lt;i&gt;_Answer 3_&lt;/i&gt;') 
        self.assertEqual(bonuses[0].values[2], '10');
