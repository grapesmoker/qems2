from django.test import SimpleTestCase
from django.contrib.auth.models import AnonymousUser, User
import django
from datetime import datetime

from qems2.qsub.packet_parser import is_answer, is_bpart, is_vhsl_bpart, is_category
from qems2.qsub.packet_parser import parse_packet_data, get_bonus_part_value, remove_category
from qems2.qsub.packet_parser import remove_answer_label
from qems2.qsub.utils import get_character_count, get_formatted_question_html, are_special_characters_balanced
from qems2.qsub.models import *
from qems2.qsub.model_utils import *
from qems2.qsub.packetizer import *

class PacketParserTests(SimpleTestCase):

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

    user = None
    writer = None
    
    def setUp(self):
        self.user, created = User.objects.get_or_create(username="testuser")
        if (created):
            self.user.email='qems2test@gmail.com'
            self.user.password='top_secret'
            self.user.save()
                        
        self.writer = Writer.objects.get(user=self.user.id)

        acfTossup = QuestionType.objects.get_or_create(question_type=ACF_STYLE_TOSSUP)
        acfBonus = QuestionType.objects.get_or_create(question_type=ACF_STYLE_BONUS)
        vhslBonus = QuestionType.objects.get_or_create(question_type=VHSL_BONUS)
            
    def test_is_answer(self):
        answers = ["answer:", "Answer:", "ANSWER:", "ANSWER: _underlined_", "ANSWER: no underline", "ANSWER: <u>underline2</u>"]
        for answer in answers:
            self.assertTrue(is_answer(answer), msg=answer)
        non_answers = ["question:", "answer", "ansER"]
        for non_answer in non_answers:
            self.assertFalse(is_answer(non_answer), msg=non_answer)

    def test_remove_answer_label(self):
        answers = ["ANSWER: <u><b>my answer</b></u>", "answer:      <u><b>my answer</b></u>", "Answer:\t<u><b>my answer</b></u>"]
        for answer in answers:
            self.assertEqual(remove_answer_label(answer), '<u><b>my answer</b></u>')

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
        dist = Distribution.objects.create(name="Test Distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist.save()
        print "dist.id: " + str(dist.id)

        euroHistory = DistributionEntry(category="History", subcategory="European", distribution=dist)
        euroHistory.save()

        americanHistory = DistributionEntry(category="History", subcategory="American", distribution=dist)
        americanHistory.save()

        qset = QuestionSet.objects.create(name="new_set", date=timezone.now(), host="test host", owner=self.writer, num_packets=10, distribution=dist)

        validTossup = 'This is a valid test tossup.\nANSWER: _My Answer_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validTossup.splitlines(), qset)
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].tossup_text, 'This is a valid test tossup.');
        self.assertEqual(tossups[0].tossup_answer, '_My Answer_');
        self.assertEqual(tossups[0].category, None);

        validTossupWithCategory = 'This should be a ~European History~ tossup.\nANSWER: _Charles I_ {History - European}'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validTossupWithCategory.splitlines(), qset)
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].tossup_text, 'This should be a ~European History~ tossup.');
        self.assertEqual(tossups[0].tossup_answer, '_Charles I_ ');
        self.assertEqual(str(tossups[0].category), 'History - European');

        validBonus = 'This is a valid bonus.  For 10 points each:\n[10] Prompt 1.\nANSWER: _Answer 1_\n[10] Prompt 2.\nANSWER: _Answer 2_\n[10] Prompt 3.\nANSWER: _Answer 3_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validBonus.splitlines(), qset)
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(str(bonuses[0].question_type), 'ACF-style bonus')
        self.assertEqual(bonuses[0].leadin, 'This is a valid bonus.  For 10 points each:')
        self.assertEqual(bonuses[0].part1_text, 'Prompt 1.')
        self.assertEqual(bonuses[0].part1_answer, '_Answer 1_')
        self.assertEqual(bonuses[0].part2_text, 'Prompt 2.')
        self.assertEqual(bonuses[0].part2_answer, '_Answer 2_')
        self.assertEqual(bonuses[0].part3_text, 'Prompt 3.')
        self.assertEqual(bonuses[0].part3_answer, '_Answer 3_')

        validBonusWithCategory = validBonus + " {History - American}"
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validBonusWithCategory.splitlines(), qset)
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(str(bonuses[0].category), "History - American");

        validVHSLBonus = '[V10] This is a valid VHSL bonus.\nANSWER: _VHSL Answer_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(validVHSLBonus.splitlines(), qset)
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(str(bonuses[0].question_type), 'VHSL bonus')
        self.assertEqual(bonuses[0].leadin, '')
        self.assertEqual(bonuses[0].part1_text, 'This is a valid VHSL bonus.')
        self.assertEqual(bonuses[0].part1_answer, '_VHSL Answer_')

        multipleQuestions = 'This is tossup 1.\nANSWER: _Tossup 1 Answer_\n[V10] This is a VHSL bonus.\nANSWER: _VHSL Answer_\nThis is another tossup.\nANSWER: _Tossup 2 Answer_'
        multipleQuestions += '\n' + validBonus
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(multipleQuestions.splitlines(), qset)
        self.assertEqual(len(bonuses), 2)
        self.assertEqual(len(tossups), 2)
        self.assertEqual(tossups[0].tossup_text, 'This is tossup 1.')
        self.assertEqual(tossups[0].tossup_answer, '_Tossup 1 Answer_')
        self.assertEqual(tossups[1].tossup_text, 'This is another tossup.')
        self.assertEqual(tossups[1].tossup_answer, '_Tossup 2 Answer_')
        self.assertEqual(bonuses[0].part1_text, 'This is a VHSL bonus.')
        self.assertEqual(bonuses[0].part1_answer, '_VHSL Answer_')
        self.assertEqual(str(bonuses[0].question_type), 'VHSL bonus')
        self.assertEqual(str(bonuses[1].question_type), 'ACF-style bonus')
        self.assertEqual(bonuses[1].leadin, 'This is a valid bonus.  For 10 points each:')
        self.assertEqual(bonuses[1].part1_text, 'Prompt 1.')
        self.assertEqual(bonuses[1].part1_answer, '_Answer 1_')
        self.assertEqual(bonuses[1].part2_text, 'Prompt 2.')
        self.assertEqual(bonuses[1].part2_answer, '_Answer 2_')
        self.assertEqual(bonuses[1].part3_text, 'Prompt 3.')
        self.assertEqual(bonuses[1].part3_answer, '_Answer 3_')

        multipleQuestionsBlankLines = 'This is tossup 1.\nANSWER: _Tossup 1 Answer_\n\n\nThis is tossup 2.\nANSWER: _Tossup 2 Answer_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(multipleQuestionsBlankLines.splitlines(), qset)
        self.assertEqual(len(bonuses), 0)
        self.assertEqual(len(tossups), 2)
        self.assertEqual(tossups[0].tossup_text, 'This is tossup 1.')
        self.assertEqual(tossups[0].tossup_answer, '_Tossup 1 Answer_')
        self.assertEqual(tossups[1].tossup_text, 'This is tossup 2.')
        self.assertEqual(tossups[1].tossup_answer, '_Tossup 2 Answer_')

        tossupWithoutAnswer = 'This is not a valid tossup.  It does not have an answer.'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithoutAnswer.splitlines(), qset)
        self.assertEqual(len(tossups), 0)
        self.assertEqual(len(bonuses), 0)

        tossupWithLineBreaks = 'This is not a valid tossup.\nIt has a line break before its answer.\nANSWER: _foo_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithLineBreaks.splitlines(), qset)
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].tossup_text, 'It has a line break before its answer.');
        self.assertEqual(tossups[0].tossup_answer, '_foo_');
        self.assertEqual(len(bonuses), 0)

        tossupWithoutQuestion = 'ANSWER: This is an answer line without a question'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithoutQuestion.splitlines(), qset)
        self.assertEqual(len(tossups), 0)
        self.assertEqual(len(bonuses), 0)
        self.assertEqual(len(tossup_errors), 1)

        tossupWithSingleQuotes = "This is a tossup with 'single quotes' in it.\nANSWER: '_Single Quoted Answer_'"
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithSingleQuotes.splitlines(), qset)
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].tossup_text, "This is a tossup with &#39;single quotes&#39; in it.");
        self.assertEqual(tossups[0].tossup_answer, "&#39;_Single Quoted Answer_&#39;");

        tossupWithDoubleQuotes = 'This is a tossup with "double quotes" in it.\nANSWER: "_Double Quoted Answer_"'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithDoubleQuotes.splitlines(), qset)
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].tossup_text, 'This is a tossup with &quot;double quotes&quot; in it.');
        self.assertEqual(tossups[0].tossup_answer, '&quot;_Double Quoted Answer_&quot;');

        tossupWithDoubleQuotes = 'This is a tossup with an <i>italic tag</i> in it.\nANSWER: <i>_Italic Answer_</i>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithDoubleQuotes.splitlines(), qset)
        self.assertEqual(len(tossups), 1)
        self.assertEqual(tossups[0].tossup_text, 'This is a tossup with an &lt;i&gt;italic tag&lt;/i&gt; in it.');
        self.assertEqual(tossups[0].tossup_answer, '&lt;i&gt;_Italic Answer_&lt;/i&gt;');

        bonusWithNonIntegerValues = 'This is a bonus with non-integer values.  For 10 points each:\n[A] Prompt 1.\nANSWER: _Answer 1_\n[10.5] Prompt 2.\nANSWER: _Answer 2_\n[10C] Prompt 3.\nANSWER: _Answer 3_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(bonusWithNonIntegerValues.splitlines(), qset)
        self.assertEqual(len(bonuses), 0)

        bonusWithHtmlValues = 'This is a bonus with html values.  For 10 points each:\n[<i>10</i>] Prompt 1.\nANSWER: _Answer 1_\n[10] Prompt 2.\nANSWER: _Answer 2_\n[<i>10</i>] Prompt 3.\nANSWER: _Answer 3_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(bonusWithHtmlValues.splitlines(), qset)
        self.assertEqual(len(bonuses), 0)

        bonusWithQuotesAndHtml = 'This is a <i>valid</i> "bonus".  For 10 points each:\n[10] <i>Prompt 1</i>.\nANSWER: "_Answer 1_"\n[10] "Prompt 2."\nANSWER: <i>_Answer 2_</i>\n[10] <i>Prompt 3.</i>\nANSWER: <i>_Answer 3_</i>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(bonusWithQuotesAndHtml.splitlines(), qset)
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(str(bonuses[0].question_type), 'ACF-style bonus')
        self.assertEqual(bonuses[0].leadin, 'This is a &lt;i&gt;valid&lt;/i&gt; &quot;bonus&quot;.  For 10 points each:')
        self.assertEqual(bonuses[0].part1_text, '&lt;i&gt;Prompt 1&lt;/i&gt;.')
        self.assertEqual(bonuses[0].part1_answer, '&quot;_Answer 1_&quot;')
        self.assertEqual(bonuses[0].part2_text, '&quot;Prompt 2.&quot;')
        self.assertEqual(bonuses[0].part2_answer, '&lt;i&gt;_Answer 2_&lt;/i&gt;')
        self.assertEqual(bonuses[0].part3_text, '&lt;i&gt;Prompt 3.&lt;/i&gt;')
        self.assertEqual(bonuses[0].part3_answer, '&lt;i&gt;_Answer 3_&lt;/i&gt;')

        tossupWithUnbalancedSpecialCharsInQuestion = 'This is a tossup question with ~an unclosed tilde.\nANSWER: _foo_'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithUnbalancedSpecialCharsInQuestion.splitlines(), qset)
        self.assertEqual(len(tossup_errors), 1)

        tossupWithUnbalancedSpecialCharsInAnswer = 'This is a tossup question.\nANSWER: _unclosed answer'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(tossupWithUnbalancedSpecialCharsInAnswer.splitlines(), qset)
        self.assertEqual(len(tossup_errors), 1)

        bonusWithUnbalancedSpecialCharsInLeadin = 'This is a bonus with (unbalanced leadin characters.  For 10 points each:\n[10] <i>Prompt 1</i>.\nANSWER: "_Answer 1_"\n[10] "Prompt 2."\nANSWER: <i>_Answer 2_</i>\n[10] <i>Prompt 3.</i>\nANSWER: <i>_Answer 3_</i>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(bonusWithUnbalancedSpecialCharsInLeadin.splitlines(), qset)
        self.assertEqual(len(bonus_errors), 1)

        bonusWithUnbalancedSpecialCharsInPrompts = 'This is a bonus with unbalanced prompt characters.  For 10 points each:\n[10] ~Prompt 1.\nANSWER: "_Answer 1_"\n[10] "Prompt 2."\nANSWER: <i>_Answer 2_</i>\n[10] <i>Prompt 3.</i>\nANSWER: <i>_Answer 3_</i>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(bonusWithUnbalancedSpecialCharsInPrompts.splitlines(), qset)
        self.assertEqual(len(bonus_errors), 1)

        bonusWithUnbalancedSpecialCharsInAnswers = 'This is a bonus with unbalanced answer characters.  For 10 points each:\n[10] Prompt 1.\nANSWER: "_Answer 1_"\n[10] "Prompt 2."\nANSWER: _Answer 2\n[10] <i>Prompt 3.</i>\nANSWER: <i>_Answer 3_</i>'
        tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(bonusWithUnbalancedSpecialCharsInAnswers.splitlines(), qset)
        self.assertEqual(len(bonus_errors), 1)

    def test_get_character_count(self):
        emptyTossup = ""
        self.assertEqual(get_character_count(emptyTossup, True), 0)

        noSpecialCharacters = "123456789"
        self.assertEqual(get_character_count(noSpecialCharacters, True), 9)

        onlySpecialCharacters = "~~()"
        self.assertEqual(get_character_count(onlySpecialCharacters, True), 0)

        mixed = "(~1234~) ~67~"
        self.assertEqual(get_character_count(mixed, True), 3)
        self.assertEqual(get_character_count(mixed, False), len(mixed))

    def test_get_formatted_question_html(self):
        emptyLine = ""
        self.assertEqual(get_formatted_question_html(emptyLine, False, True, False), "")
        self.assertEqual(get_formatted_question_html(emptyLine, True, True, False), "")

        noSpecialChars = "No special chars"
        self.assertEqual(get_formatted_question_html(noSpecialChars, False, True, False), noSpecialChars)
        self.assertEqual(get_formatted_question_html(noSpecialChars, True, True, False), noSpecialChars)

        specialChars = "_Underlines_, ~italics~ and (parens).  And again _Underlines_, ~italics~ and (parens)."
        self.assertEqual(get_formatted_question_html(specialChars, False, True, False), "_Underlines_, <i>italics</i> and <strong>(parens)</strong>.  And again _Underlines_, <i>italics</i> and <strong>(parens)</strong>.")
        self.assertEqual(get_formatted_question_html(specialChars, True, True, False), "<u><b>Underlines</b></u>, <i>italics</i> and <strong>(parens)</strong>.  And again <u><b>Underlines</b></u>, <i>italics</i> and <strong>(parens)</strong>.")

        newLinesNoParens = "(No parens).&lt;br&gt;New line."
        self.assertEqual(get_formatted_question_html(newLinesNoParens, False, False, False), "(No parens).&lt;br&gt;New line.")
        self.assertEqual(get_formatted_question_html(newLinesNoParens, False, False, True), "(No parens).<br />New line.")

    def test_does_answerline_have_underlines(self):
        self.assertFalse(does_answerline_have_underlines("ANSWER: Foo"))
        self.assertTrue(does_answerline_have_underlines("ANSWER: _Foo_"))
        self.assertTrue(does_answerline_have_underlines(""))

    def test_tossup_to_html(self):
        dist = Distribution.objects.create(name="test_tossup_to_html distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist.save()

        acfTossup, created = QuestionType.objects.get_or_create(question_type="ACF-style tossup")

        americanHistory = DistributionEntry(category="History", subcategory="American", distribution=dist)
        americanHistory.save()

        tossup_text = "(Test) ~tossup~."
        tossup_answer = "_test answer_"
        tossup_no_category_no_question_type = Tossup(tossup_text=tossup_text, tossup_answer=tossup_answer)
        expectedOutput = "<p><strong>(Test)</strong> <i>tossup</i>.<br />ANSWER: <u><b>test answer</b></u></p>"
        self.assertEqual(tossup_no_category_no_question_type.to_html(), expectedOutput)
        self.assertEqual(tossup_no_category_no_question_type.to_html(include_category=True), expectedOutput)
        expectedOutputWithCharCount = expectedOutput + "<p><strong>Character Count:</strong> 8</p>"
        self.assertEqual(tossup_no_category_no_question_type.to_html(include_character_count=True), expectedOutputWithCharCount)

        tossup_with_category = Tossup(tossup_text=tossup_text, tossup_answer=tossup_answer, category=americanHistory)
        self.assertEqual(tossup_with_category.to_html(), expectedOutput)
        expectedOutputWithCategory = "<p><strong>(Test)</strong> <i>tossup</i>.<br />ANSWER: <u><b>test answer</b></u></p><p><strong>Category:</strong> History - American</p>"
        self.assertEqual(tossup_with_category.to_html(include_category=True), expectedOutputWithCategory)

    def test_bonus_to_html(self):
        dist = Distribution.objects.create(name="test_bonus_to_html distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist.save()

        acfBonus, created = QuestionType.objects.get_or_create(question_type="ACF-style bonus")

        vhslBonus, created = QuestionType.objects.get_or_create(question_type="VHSL bonus")

        americanHistory = DistributionEntry(category="History", subcategory="American", distribution=dist)
        americanHistory.save()

        leadin = "Leadin with ~italics~ and (parens) and _underlines_."
        part1_text = "Part 1 with ~italics~ and (parens) and _underlines_."
        part1_answer = "_~Answer 1~_ [or foo (bar)]"
        part2_text = "Part 2."
        part2_answer = "_answer 2_"
        part3_text = "Part 3."
        part3_answer = "_answer 3_"
        acf_bonus_no_category = Bonus(leadin=leadin, part1_text=part1_text, part1_answer=part1_answer, part2_text=part2_text, part2_answer=part2_answer, part3_text=part3_text, part3_answer=part3_answer)
        expectedOutput = "<p>Leadin with <i>italics</i> and <strong>(parens)</strong> and _underlines_.<br />"
        expectedOutput += "[10] Part 1 with <i>italics</i> and <strong>(parens)</strong> and _underlines_.<br />"
        expectedOutput += "ANSWER: <u><b><i>Answer 1</i></b></u> [or foo <strong>(bar)</strong>]<br />"
        expectedOutput += "[10] Part 2.<br />"
        expectedOutput += "ANSWER: <u><b>answer 2</b></u><br />"
        expectedOutput += "[10] Part 3.<br />"
        expectedOutputWithoutLastLine = expectedOutput
        expectedOutput += "ANSWER: <u><b>answer 3</b></u></p>"
        self.assertEqual(acf_bonus_no_category.to_html(), expectedOutput)
        self.assertEqual(acf_bonus_no_category.to_html(include_category=True), expectedOutput)
        expectedOutputWithCharCount = expectedOutput + "<p><strong>Character Count:</strong> "
        expectedOutputWithCharCount += "98</p>"
        self.assertEqual(acf_bonus_no_category.to_html(include_character_count=True), expectedOutputWithCharCount)
        acf_bonus_no_category.category = americanHistory
        self.assertEqual(acf_bonus_no_category.to_html(), expectedOutput)
        expectedOutputWithCategory = expectedOutputWithoutLastLine + "ANSWER: <u><b>answer 3</b></u></p><p><strong>Category:</strong> History - American</p>"
        self.assertEqual(acf_bonus_no_category.to_html(include_category=True), expectedOutputWithCategory)

        vhsl_bonus_no_category = Bonus(part1_text=part1_text, part1_answer=part1_answer, question_type=vhslBonus)
        expectedVhslOutput = "<p>Part 1 with <i>italics</i> and <strong>(parens)</strong> and _underlines_.<br />"
        expectedVhslOutput += "ANSWER: <u><b><i>Answer 1</i></b></u> [or foo <strong>(bar)</strong>]</p>"
        self.assertEqual(vhsl_bonus_no_category.to_html(), expectedVhslOutput)
        vhsl_bonus_no_category.category = americanHistory
        self.assertEqual(vhsl_bonus_no_category.to_html(), expectedVhslOutput)
        expectedVhslOutput = "<p>Part 1 with <i>italics</i> and <strong>(parens)</strong> and _underlines_.<br />"
        expectedVhslOutput += "ANSWER: <u><b><i>Answer 1</i></b></u> [or foo <strong>(bar)</strong>]</p><p><strong>Category:</strong> History - American</p>"
        self.assertEqual(vhsl_bonus_no_category.to_html(include_category=True), expectedVhslOutput)

    def test_category_entry_get_requirements_methods(self):
        dist = Distribution.objects.create(name="new_distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist.save()
        
        category_entry = CategoryEntry(distribution=dist, category_type=CATEGORY, category_name="Test Category", acf_tossup_fraction=2.2, acf_bonus_fraction=1, vhsl_bonus_fraction=0, min_total_questions_in_period=3, max_total_questions_in_period=4)
        category_entry.save()
        
        self.assertEqual(category_entry.get_acf_tossup_integer(), 2)
        self.assertEqual(round(category_entry.get_acf_tossup_remainder(), 2), 0.20)
        self.assertEqual(category_entry.get_acf_bonus_integer(), 1)
        self.assertEqual(round(category_entry.get_acf_bonus_remainder(), 2), 0)
        self.assertEqual(category_entry.get_vhsl_bonus_integer(), 0)
        self.assertEqual(round(category_entry.get_vhsl_bonus_remainder(), 2), 0)
    
    def test_sub_sub_category_to_string(self):
        dist = Distribution.objects.create(name="new_distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist.save()
        
        category_entry = CategoryEntry(distribution=dist, category_type=CATEGORY, category_name="Arts", acf_tossup_fraction=2.2, acf_bonus_fraction=1, vhsl_bonus_fraction=0, min_total_questions_in_period=3, max_total_questions_in_period=4)
        category_entry.save()

        sub_category_entry = CategoryEntry(distribution=dist, category_type=SUB_CATEGORY, category_name="Arts", sub_category_name="Opera", acf_tossup_fraction=0.3, acf_bonus_fraction=0.3, vhsl_bonus_fraction=0, min_total_questions_in_period=0, max_total_questions_in_period=1)
        sub_category_entry.save()

        sub_sub_category_entry = CategoryEntry(distribution=dist, category_type=SUB_SUB_CATEGORY, category_name="Arts", sub_category_name="Opera", sub_sub_category_name="Baroque", acf_tossup_fraction=0.1, acf_bonus_fraction=0.1, vhsl_bonus_fraction=0, min_total_questions_in_period=0, max_total_questions_in_period=1)
        sub_sub_category_entry.save()
        
        self.assertEqual(str(category_entry), "Arts")
        self.assertEqual(str(sub_category_entry), "Arts - Opera")                
        self.assertEqual(str(sub_sub_category_entry), "Arts - Opera - Baroque")

    def test_period_wide_entry_reset_current_values(self):        
        dist = Distribution.objects.create(name="new_distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist.save()
        
        qset = QuestionSet.objects.create(name="new_set", date=timezone.now(), host="test host", owner=self.writer, num_packets=10, distribution=dist)
        qset.save()
        
        pwe = PeriodWideEntry.objects.create(period_type=ACF_REGULAR_PERIOD, question_set=qset, distribution=dist, acf_tossup_cur=5, acf_bonus_cur=5, vhsl_bonus_cur=5, acf_tossup_total=10, acf_bonus_total=10, vhsl_bonus_total=10)
        pwe.save()
        pwe.reset_current_values()
        self.assertEqual(pwe.acf_tossup_cur, 0)
        self.assertEqual(pwe.acf_bonus_cur, 0)
        self.assertEqual(pwe.vhsl_bonus_cur, 0)
    
    def create_period(self):
        dist = Distribution.objects.create(name="new_distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist.save()
        
        qset = QuestionSet.objects.create(name="new_set", date=timezone.now(), host="test host", owner=self.writer, num_packets=10, distribution=dist)
        qset.save()
        
        pwe = PeriodWideEntry.objects.create(period_type=ACF_REGULAR_PERIOD, question_set=qset, distribution=dist, acf_tossup_cur=5, acf_bonus_cur=5, vhsl_bonus_cur=5, acf_tossup_total=10, acf_bonus_total=10, vhsl_bonus_total=10)
        pwe.save()
        
        packet = Packet.objects.create(packet_name="Test Packet", question_set=qset, created_by=self.writer)
        packet.save()
        
        period = Period.objects.create(name="Test Period", packet=packet, period_wide_entry=pwe, acf_tossup_cur=10, acf_bonus_cur=10, vhsl_bonus_cur=10)
        period.save()
        
        return dist, qset, pwe, packet, period
        
    
    def test_period_reset_current_values(self):
        dist, qset, pwe, packet, period = self.create_period()
        period.reset_current_values()
        self.assertEqual(period.acf_tossup_cur, 0)
        self.assertEqual(period.acf_bonus_cur, 0)
        self.assertEqual(period.vhsl_bonus_cur, 0)        

    def test_period_wide_category_entry_reset_current_values(self):
        dist = Distribution.objects.create(name="new_distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist.save()
        
        qset = QuestionSet.objects.create(name="new_set", date=timezone.now(), host="test host", owner=self.writer, num_packets=10, distribution=dist)
        qset.save()
        
        pwe = PeriodWideEntry.objects.create(period_type=ACF_REGULAR_PERIOD, question_set=qset, distribution=dist, acf_tossup_cur=5, acf_bonus_cur=5, vhsl_bonus_cur=5, acf_tossup_total=10, acf_bonus_total=10, vhsl_bonus_total=10)
        pwe.save()
        pwe.reset_current_values()
        
        ce = CategoryEntry.objects.create(distribution=dist, category_name="Test Category", category_type=CATEGORY)
        ce.save()
        
        pwce = PeriodWideCategoryEntry.objects.create(period_wide_entry=pwe, category_entry=ce, acf_tossup_cur_across_periods=10, acf_bonus_cur_across_periods=10, vhsl_bonus_cur_across_periods=10, acf_tossup_total_across_periods=10, acf_bonus_total_across_periods=10, vhsl_bonus_total_across_periods=10)
        pwce.save()
        pwce.reset_current_values()
        self.assertEqual(pwce.acf_tossup_cur_across_periods, 0)
        self.assertEqual(pwce.acf_bonus_cur_across_periods, 0)
        self.assertEqual(pwce.vhsl_bonus_cur_across_periods, 0)

    def test_period_wide_category_entry_reset_total_values(self):
        dist = Distribution.objects.create(name="new_distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist.save()
        
        qset = QuestionSet.objects.create(name="new_set", date=timezone.now(), host="test host", owner=self.writer, num_packets=10, distribution=dist)
        qset.save()
        
        pwe = PeriodWideEntry.objects.create(period_type=ACF_REGULAR_PERIOD, question_set=qset, distribution=dist, acf_tossup_cur=5, acf_bonus_cur=5, vhsl_bonus_cur=5, acf_tossup_total=10, acf_bonus_total=10, vhsl_bonus_total=10)
        pwe.save()
        pwe.reset_current_values()
        
        ce = CategoryEntry.objects.create(distribution=dist, category_name="Test Category", category_type=CATEGORY)
        ce.save()
        
        pwce = PeriodWideCategoryEntry.objects.create(period_wide_entry=pwe, category_entry=ce, acf_tossup_cur_across_periods=10, acf_bonus_cur_across_periods=10, vhsl_bonus_cur_across_periods=10, acf_tossup_total_across_periods=10, acf_bonus_total_across_periods=10, vhsl_bonus_total_across_periods=10)
        pwce.save()
        pwce.reset_total_values()
        self.assertEqual(pwce.acf_tossup_total_across_periods, 0)
        self.assertEqual(pwce.acf_bonus_total_across_periods, 0)
        self.assertEqual(pwce.vhsl_bonus_total_across_periods, 0)
        
    # Helper:
    def get_one_period_category_entry(self, question_fractions, min_total_questions_in_period, max_total_questions_in_period):
        dist = Distribution.objects.create(name="new_distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist.save()
        
        qset = QuestionSet.objects.create(name="new_set", date=timezone.now(), host="test host", owner=self.writer, num_packets=10, distribution=dist)
        qset.save()
        
        pwe = PeriodWideEntry.objects.create(period_type=ACF_REGULAR_PERIOD, question_set=qset, distribution=dist, acf_tossup_cur=5, acf_bonus_cur=5, vhsl_bonus_cur=5, acf_tossup_total=10, acf_bonus_total=10, vhsl_bonus_total=10)
        pwe.save()
        pwe.reset_current_values()
        
        ce = CategoryEntry.objects.create(distribution=dist, category_name="Test Category", category_type=CATEGORY, acf_tossup_fraction=question_fractions, acf_bonus_fraction=question_fractions, vhsl_bonus_fraction=question_fractions, min_total_questions_in_period=min_total_questions_in_period, max_total_questions_in_period=max_total_questions_in_period)
        ce.save()
        
        self.ce = ce
        
        pwce = PeriodWideCategoryEntry.objects.create(period_wide_entry=pwe, category_entry=ce, acf_tossup_cur_across_periods=10, acf_bonus_cur_across_periods=10, vhsl_bonus_cur_across_periods=10, acf_tossup_total_across_periods=10, acf_bonus_total_across_periods=10, vhsl_bonus_total_across_periods=10)
        pwce.save()
        
        packet = Packet.objects.create(packet_name="Test Packet", question_set=qset, created_by=self.writer)
        packet.save()
        
        period = Period.objects.create(name="Test Period", packet=packet, period_wide_entry=pwe, acf_tossup_cur=10, acf_bonus_cur=10, vhsl_bonus_cur=10)
        period.save()
        
        opce = OnePeriodCategoryEntry.objects.create(period=period, period_wide_category_entry=pwce, acf_tossup_cur_in_period=10, acf_bonus_cur_in_period=10, vhsl_bonus_cur_in_period=10, acf_tossup_total_in_period=10, acf_bonus_total_in_period=10, vhsl_bonus_total_in_period=10)
        return opce        
        
    def test_one_period_category_entry_get_linked_category_entry(self):
        opce = self.get_one_period_category_entry(question_fractions=10, min_total_questions_in_period=30, max_total_questions_in_period=30)
        linked_entry = opce.get_linked_category_entry()
        self.assertEqual(linked_entry, self.ce)
    
    def test_one_period_category_entry_get_total_questions_all_types(self):
        opce = self.get_one_period_category_entry(question_fractions=10, min_total_questions_in_period=30, max_total_questions_in_period=30)
        self.assertEqual(opce.get_total_questions_all_types(), 30)
        
    def test_one_period_category_entry_is_under_max_total_questions_limit(self):
        # It creates 30 total questions by default, and we've said the max total is 20
        opce = self.get_one_period_category_entry(question_fractions=5, min_total_questions_in_period=20, max_total_questions_in_period=20)        
        self.assertEqual(opce.is_under_max_total_questions_limit(), False)
                
        # Now try when the max total is 40
        opce = self.get_one_period_category_entry(question_fractions=5, min_total_questions_in_period=40, max_total_questions_in_period=40)        
        self.assertEqual(opce.is_under_max_total_questions_limit(), True)
        
    def test_one_period_category_entry_is_over_min_total_questions_limit(self):
        # It creates 30 total questions by default, and we've said the max total is 20
        opce = self.get_one_period_category_entry(question_fractions=5, min_total_questions_in_period=20, max_total_questions_in_period=20)        
        self.assertEqual(opce.is_over_min_total_questions_limit(), True)
                
        # Now try when the max total is 40
        opce = self.get_one_period_category_entry(question_fractions=5, min_total_questions_in_period=40, max_total_questions_in_period=40)        
        self.assertEqual(opce.is_over_min_total_questions_limit(), False)
        
    def test_one_period_category_entry_reset_current_values(self):
        opce = self.get_one_period_category_entry(question_fractions=5, min_total_questions_in_period=20, max_total_questions_in_period=20)
        opce.reset_current_values()
        self.assertEqual(opce.acf_tossup_cur_in_period, 0)
        self.assertEqual(opce.acf_bonus_cur_in_period, 0)
        self.assertEqual(opce.vhsl_bonus_cur_in_period, 0)

    def test_one_period_category_entry_reset_total_values(self):
        opce = self.get_one_period_category_entry(question_fractions=5, min_total_questions_in_period=20, max_total_questions_in_period=20)
        opce.reset_total_values()
        self.assertEqual(opce.acf_tossup_total_in_period, 0)
        self.assertEqual(opce.acf_bonus_total_in_period, 0)
        self.assertEqual(opce.vhsl_bonus_total_in_period, 0)
    
    #############################################################
    # Packetizer Tests
    #############################################################
    
    def test_clear_questions(self):
        dist, qset, pwe, packet, period = self.create_period()
        tossup = self._create_tossup(self.writer, qset, packet, None, 1, "Foo", "_bar_", get_question_type_from_string(ACF_STYLE_TOSSUP))
        bonus = self._create_bonus(self.writer, qset, packet, None, 2, get_question_type_from_string(VHSL_BONUS), None, "Foobar", "_vhsl_")
        tossup_pk = tossup.pk
        bonus_pk = bonus.pk

        clear_questions(qset)
        # Django caches values for existing references, so we have to fetch the object again
        tossup = Tossup.objects.filter(pk=tossup_pk)[0]
        self.assertEqual(tossup.packet, None)
        self.assertEqual(tossup.period, None)
        self.assertEqual(tossup.question_number, None)
        bonus = Bonus.objects.filter(pk=bonus_pk)[0]
        self.assertEqual(bonus.packet, None)
        self.assertEqual(bonus.period, None)
        self.assertEqual(bonus.question_number, None)
        
    def test_get_unassigned_acf_tossups(self):
        dist, qset, pwe, packet, period = self.create_period()
        assigned_tossup = self._create_tossup(self.writer, qset, packet, period, 1, "Assigned Tossup", "_bar_", None)
        unassigned_tossup = self._create_tossup(self.writer, qset, None, None, None, "Unassigned Tossup", "_bar_", None)
        acf_tossups = get_unassigned_acf_tossups(qset)
        self.assertEqual(len(acf_tossups), 1)
        self.assertEqual(acf_tossups[0].tossup_text, "Unassigned Tossup")
                
    def test_get_unassigned_acf_bonuses(self):
        dist, qset, pwe, packet, period = self.create_period()
        self._setup_assigned_bonus_tests_bonuses(qset, packet, period)

        acf_bonuses = get_unassigned_acf_bonuses(qset)
        self.assertEqual(len(acf_bonuses), 1)
        self.assertEqual(acf_bonuses[0].leadin, "Unassigned ACF bonus.")
        
    def test_get_unassigned_vhsl_bonuses(self):
        dist, qset, pwe, packet, period = self.create_period()
        self._setup_assigned_bonus_tests_bonuses(qset, packet, period)

        vhsl_bonuses = get_unassigned_vhsl_bonuses(qset)
        self.assertEqual(len(vhsl_bonuses), 1)
        self.assertEqual(vhsl_bonuses[0].leadin, "Unassigned VHSL bonus.")

    def test_get_assigned_acf_tossups_in_period(self):
        dist, qset, pwe, packet, period = self.create_period()
        tossup1 = self._create_tossup(self.writer, qset, packet, period, 1, "Assigned Tossup", "_bar_", None)
        tossup2 = self._create_tossup(self.writer, qset, packet, None, 1, "Unassigned Tossup", "_foo_", None)
        
        assigned_tossups = get_assigned_acf_tossups_in_period(qset, period)
        self.assertEqual(len(assigned_tossups), 1)
        self.assertEqual(assigned_tossups[0].tossup_text, "Assigned Tossup")

    def test_get_assigned_acf_bonuses_in_period(self):
        dist, qset, pwe, packet, period = self.create_period()
        self._setup_assigned_bonus_tests_bonuses(qset, packet, period)

        assigned_bonuses = get_assigned_acf_bonuses_in_period(qset, period)
        self.assertEqual(len(assigned_bonuses), 1)
        self.assertEqual(assigned_bonuses[0].leadin, "My ACF assigned bonus.")

    def test_get_assigned_vhsl_bonuses_in_period(self):
        dist, qset, pwe, packet, period = self.create_period()
        self._setup_assigned_bonus_tests_bonuses(qset, packet, period)

        assigned_bonuses = get_assigned_vhsl_bonuses_in_period(qset, period)
        self.assertEqual(len(assigned_bonuses), 1)
        self.assertEqual(assigned_bonuses[0].leadin, "My assigned VHSL bonus.")

    def test_reset_category_counts(self):
        dist, qset, pwe, packet, period = self.create_period()
        pwe.acf_tossup_cur = 10
        pwe.acf_tossup_total = 10
        period.acf_tossup_cur = 10
        pwe.save()
        period.save()
        pwe_pk = pwe.pk
        period_pk = period.pk

        ce = CategoryEntry(distribution=dist, category_name="History", category_type=CATEGORY)
        ce.save()
        
        pwce = PeriodWideCategoryEntry(period_wide_entry=pwe, category_entry=ce)
        pwce.acf_tossup_cur_across_periods = 10
        pwce.acf_tossup_total_across_periods = 10
        pwce.save()
        pwce_pk = pwce.pk
        
        opce = OnePeriodCategoryEntry(period=period, period_wide_category_entry=pwce)
        opce.acf_tossup_cur_in_period = 10
        opce.acf_tossup_total_in_period = 10
        opce.save()
        opce_pk = opce.pk
        
        reset_category_counts(qset, False)
        pwe = PeriodWideEntry.objects.filter(pk=pwe_pk)[0]
        period = Period.objects.filter(pk=period_pk)[0]
        pwce = PeriodWideCategoryEntry.objects.filter(pk=pwce_pk)[0]
        opce = OnePeriodCategoryEntry.objects.filter(pk=opce_pk)[0]
        self.assertEqual(pwe.acf_tossup_cur, 0)
        self.assertEqual(pwe.acf_tossup_total, 10)
        self.assertEqual(period.acf_tossup_cur, 0)
        self.assertEqual(pwce.acf_tossup_cur_across_periods, 0)
        self.assertEqual(pwce.acf_tossup_total_across_periods, 10)
        self.assertEqual(opce.acf_tossup_cur_in_period, 0)
        self.assertEqual(opce.acf_tossup_total_in_period, 10)
        
        reset_category_counts(qset, True)
        pwe = PeriodWideEntry.objects.filter(pk=pwe_pk)[0]
        period = Period.objects.filter(pk=period_pk)[0]
        pwce = PeriodWideCategoryEntry.objects.filter(pk=pwce_pk)[0]
        opce = OnePeriodCategoryEntry.objects.filter(pk=opce_pk)[0]
        self.assertEqual(pwe.acf_tossup_cur, 0)
        self.assertEqual(pwe.acf_tossup_total, 0)
        self.assertEqual(period.acf_tossup_cur, 0)
        self.assertEqual(pwce.acf_tossup_cur_across_periods, 0)
        self.assertEqual(pwce.acf_tossup_total_across_periods, 0)
        self.assertEqual(opce.acf_tossup_cur_in_period, 0)
        self.assertEqual(opce.acf_tossup_total_in_period, 0)

    def test_get_parents_from_category_entry(self):
        # Just category entry
        dist = Distribution.objects.create(name="new_distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist.save()

        dist2 = Distribution.objects.create(name="new_distribution2", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist2.save()
        
        ce = CategoryEntry(distribution=dist, category_name="History", category_type=CATEGORY)
        ce.save()

        ce2 = CategoryEntry(distribution=dist2, category_name="History", category_type=CATEGORY)
        ce2.save()
        
        c, sc, ssc = get_parents_from_category_entry(ce)
        self.assertEqual(c, ce)
        self.assertEqual(sc, None)
        self.assertEqual(ssc, None)
        
        # From a subcat with a parent
        
        subcat1 = CategoryEntry(distribution=dist, category_name="History", sub_category_name="European", category_type=SUB_CATEGORY)
        subcat1.save()
        
        c, sc, ssc = get_parents_from_category_entry(subcat1)
        self.assertEqual(c, ce)
        self.assertEqual(sc, subcat1)
        self.assertEqual(ssc, None)        
        
        # From a subcat without a parent for some reason
        
        subcat2 = CategoryEntry(distribution=dist, category_name="Literature", sub_category_name="European", category_type=SUB_CATEGORY)
        subcat2.save()
        c, sc, ssc = get_parents_from_category_entry(subcat2)        
        self.assertEqual(c, None)
        self.assertEqual(sc, subcat2)
        self.assertEqual(ssc, None)
                
        # From a subsubcat with valid parents
        
        subsubcat1 = CategoryEntry(distribution=dist, category_name="History", sub_category_name="European", sub_sub_category_name="British", category_type=SUB_SUB_CATEGORY)
        subsubcat1.save()
        self.assertEqual(c, ce)
        self.assertEqual(sc, subcat1)
        self.assertEqual(ssc, subsubcat1)
        
        # From a subsubcat without a parent
        
        subsubcat2 = CategoryEntry(distribution=dist, category_name="Geography", sub_category_name="World", sub_sub_category_name="French", category_type=SUB_SUB_CATEGORY)
        subsubcat2.save()
        self.assertEqual(c, None)
        self.assertEqual(sc, None)
        self.assertEqual(ssc, subsubcat2)
        
    def test_get_children_from_category_entry(self):
        # Just category entry
        dist = Distribution.objects.create(name="new_distribution", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist.save()

        dist2 = Distribution.objects.create(name="new_distribution2", acf_tossup_per_period_count=20, acf_bonus_per_period_count=20, vhsl_bonus_per_period_count=20)
        dist2.save()
        
        ce = CategoryEntry(distribution=dist, category_name="History", category_type=CATEGORY)
        ce.save()

        ce2 = CategoryEntry(distribution=dist2, category_name="History", category_type=CATEGORY)
        ce2.save()
        
        children = get_children_from_category_entry(ce)
        self.assertEqual(len(children), 1)
        
        # One with multiple sub cats
        subcat1 = CategoryEntry(distribution=dist, category_name="History", sub_category_name="European", category_type=SUB_CATEGORY)
        subcat1.save()
        subcat2 = CategoryEntry(distribution=dist, category_name="History", sub_category_name="American", category_type=SUB_CATEGORY)
        subcat2.save()
        subcat3 = CategoryEntry(distribution=dist, category_name="Literature", sub_category_name="European", category_type=SUB_CATEGORY)
        subcat3.save()
        
        children = get_children_from_category_entry(ce)
        self.assertEqual(len(children), 3)
                
        # One with multiple sub sub cats
        subsubcat1 = CategoryEntry(distribution=dist, category_name="History", sub_category_name="European", sub_sub_category_name="British", category_type=SUB_SUB_CATEGORY)
        subsubcat1.save()
        subsubcat2 = CategoryEntry(distribution=dist, category_name="History", sub_category_name="European", sub_sub_category_name="French", category_type=SUB_SUB_CATEGORY)
        subsubcat2.save()
        subsubcat3 = CategoryEntry(distribution=dist, category_name="History", sub_category_name="American", sub_sub_category_name="Political", category_type=SUB_SUB_CATEGORY)
        subsubcat3.save()
        subsubcat4 = CategoryEntry(distribution=dist, category_name="Literature", sub_category_name="European", sub_sub_category_name="British", category_type=SUB_SUB_CATEGORY)
        subsubcat4.save()
        
        # Should return the 1 category, 2 subcats, and 3 subsubcats
        children = get_children_from_category_entry(ce)
        self.assertEqual(len(children), 6)

    def test_get_period_entries_from_category_entry(self):
        # Create a category entry and a period
        dist, qset, pwe, packet, period = self.create_period()
        ce = CategoryEntry(distribution=dist, category_name="History", category_type=CATEGORY)
        ce.save()
        
        # TODO: Possibly try the null case
        
        # Create a pwce and a opce
        existing_pwce = PeriodWideCategoryEntry(period_wide_entry=pwe, category_entry=ce)
        existing_pwce.save()
        existing_opce = OnePeriodCategoryEntry(period=period, period_wide_category_entry=existing_pwce)
        existing_opce.save()
        
        pwce, opce = get_period_entries_from_category_entry(ce, period)
        self.assertEqual(pwce, existing_pwce)
        self.assertEqual(opce, existing_opce)
        
    def test_get_period_entries_from_category_entry_with_parents(self):
        # Create a hierarchy of category entries and pwces and opces
        dist, qset, pwe, packet, period = self.create_period()
        ce = CategoryEntry(distribution=dist, category_name="History", category_type=CATEGORY)
        ce.save()
        
        # TODO: Finish writing these tests

    def _setup_assigned_bonus_tests_bonuses(self, qset, packet, period):
        part1_text = u"Part 1 with ~italics~ and (parens) and _underlines_."
        part1_answer = u"_~Answer 1~_ [or foo (bar)]"
        part2_text = u"Part 2."
        part2_answer = u"_answer 2_"
        part3_text = u"Part 3."
        part3_answer = u"_answer 3_"
        acf_question_type = get_question_type_from_string(ACF_STYLE_BONUS)
        vhsl_question_type = get_question_type_from_string(VHSL_BONUS)
        self._create_bonus(self.writer, qset, packet, period, 1, acf_question_type, "My ACF assigned bonus.", part1_text, part1_answer, part2_text, part2_answer, part3_text, part3_answer)
        self._create_bonus(self.writer, qset, None, None, None, acf_question_type, "Unassigned ACF bonus.", part1_text, part1_answer, part2_text, part2_answer, part3_text, part3_answer)
        self._create_bonus(self.writer, qset, packet, period, 1, vhsl_question_type, "My assigned VHSL bonus.", part1_text, part1_answer, part2_text, part2_answer, part3_text, part3_answer)
        self._create_bonus(self.writer, qset, None, None, None, vhsl_question_type, "Unassigned VHSL bonus.", part1_text, part1_answer, part2_text, part2_answer, part3_text, part3_answer)

    def _create_tossup(self, writer, qset, packet, period, number, text, answer, question_type):
        return Tossup.objects.create(author=writer, question_set=qset, packet=packet, question_number=number, tossup_text=text, \
            period=period, tossup_answer=answer, question_type=question_type, created_date=datetime.now(), last_changed_date=datetime.now())

    def _create_bonus(self, writer, qset, packet, period, number, question_type, leadin, part1_text, part1_answer, part2_text=None, part2_answer=None, part3_text=None, part3_answer=None):
        return Bonus.objects.create(author=writer, question_set=qset, packet=packet, question_number=number, period=period, leadin=leadin, \
            part1_text=part1_text, part1_answer=part1_answer, question_type=question_type, created_date=datetime.now(), last_changed_date=datetime.now())