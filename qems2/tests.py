from django.test import SimpleTestCase

from qems2.qsub.packet_parser import is_answer, is_bpart, is_vhsl_bpart, is_category
from qems2.qsub.packet_parser import parse_packet_data, get_bonus_part_value, remove_category
from qems2.qsub.packet_parser import remove_answer_label, are_special_characters_balanced
from qems2.qsub.utils import get_character_count, get_formatted_question_html

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
    def test_are_special_characters_balanced(self):
        balancedLines = ["", "No special chars", "_Underscores_", "~Italics~", "(Parens)", "_~Several_~ (items) in (one) _question_."]
        unbalancedLines = ["_", "~", "_test__", "~~test~", "(test", "test)", "((test)", "(", ")", ")test(", "(test))"]
        for balancedLine in balancedLines:
            self.assertTrue(are_special_characters_balanced(balancedLine))
        for unbalancedLine in unbalancedLines:
            self.assertFalse(are_special_characters_balanced(unbalancedLine))
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
        
        tossupWithUnbalancedSpecialCharsInQuestion = 'This is a tossup question with ~an unclosed tilde.\nANSWER: _foo_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithUnbalancedSpecialCharsInQuestion.splitlines())
        self.assertEqual(len(tossup_errors), 1)

        tossupWithUnbalancedSpecialCharsInAnswer = 'This is a tossup question.\nANSWER: _unclosed answer'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithUnbalancedSpecialCharsInAnswer.splitlines())
        self.assertEqual(len(tossup_errors), 1)
        
        bonusWithUnbalancedSpecialCharsInLeadin = 'This is a bonus with (unbalanced leadin characters.  For 10 points each:\n[10] <i>Prompt 1</i>.\nANSWER: "_Answer 1_"\n[10] "Prompt 2."\nANSWER: <i>_Answer 2_</i>\n[10] <i>Prompt 3.</i>\nANSWER: <i>_Answer 3_</i>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(bonusWithUnbalancedSpecialCharsInLeadin.splitlines())
        self.assertEqual(len(bonus_errors), 1)
        
        bonusWithUnbalancedSpecialCharsInPrompts = 'This is a bonus with unbalanced prompt characters.  For 10 points each:\n[10] ~Prompt 1.\nANSWER: "_Answer 1_"\n[10] "Prompt 2."\nANSWER: <i>_Answer 2_</i>\n[10] <i>Prompt 3.</i>\nANSWER: <i>_Answer 3_</i>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(bonusWithUnbalancedSpecialCharsInPrompts.splitlines())
        self.assertEqual(len(bonus_errors), 1)

        bonusWithUnbalancedSpecialCharsInAnswers = 'This is a bonus with unbalanced answer characters.  For 10 points each:\n[10] Prompt 1.\nANSWER: "_Answer 1_"\n[10] "Prompt 2."\nANSWER: _Answer 2\n[10] <i>Prompt 3.</i>\nANSWER: <i>_Answer 3_</i>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(bonusWithUnbalancedSpecialCharsInAnswers.splitlines())
        self.assertEqual(len(bonus_errors), 1)
    def test_get_character_count(self):
        emptyTossup = ""
        self.assertEqual(get_character_count(emptyTossup), 0)
        
        noSpecialCharacters = "123456789"
        self.assertEqual(get_character_count(noSpecialCharacters), 9)
        
        onlySpecialCharacters = "~~()"
        self.assertEqual(get_character_count(onlySpecialCharacters), 0)
        
        mixed = "(~1234~) ~67~"
        self.assertEqual(get_character_count(mixed), 3)
        
    def test_get_formatted_question_html(self):
        emptyLine = ""
        self.assertEqual(get_formatted_question_html(emptyLine, False, True, False), "")
        self.assertEqual(get_formatted_question_html(emptyLine, True, True, False), "")
        
        noSpecialChars = "No special chars"
        self.assertEqual(get_formatted_question_html(noSpecialChars, False, True, False), noSpecialChars)
        self.assertEqual(get_formatted_question_html(noSpecialChars, True, True, False), noSpecialChars)
        
        specialChars = "_Underlines_, ~italics~ and (parens).  And again _Underlines_, ~italics~ and (parens)."
        self.assertEqual(get_formatted_question_html(specialChars, False, True, False), "_Underlines_, <i>italics</i> and <strong>(parens)</strong>.  And again _Underlines_, <i>italics</i> and <strong>(parens)</strong>.")
        self.assertEqual(get_formatted_question_html(specialChars, True, True, False), "<b><u>Underlines</b></u>, <i>italics</i> and <strong>(parens)</strong>.  And again <b><u>Underlines</b></u>, <i>italics</i> and <strong>(parens)</strong>.")
        
        newLinesNoParens = "(No parens).&lt;br&gt;New line."
        self.assertEqual(get_formatted_question_html(newLinesNoParens, False, False, False), "(No parens).&lt;br&gt;New line.")
        self.assertEqual(get_formatted_question_html(newLinesNoParens, False, False, True), "(No parens).<br>New line.")
