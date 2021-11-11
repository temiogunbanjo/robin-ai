import os
import re
import json
from math import sqrt
from pipe import where, select
from utils.utils import contains, starts_with, remove_punctuations


class WordProcessor:
    def __init__(self):
        self.classifications = {
            "confirmations": {
                "examples": [
                    'yes', 'yeah', 'yea', 'yep', 'sure', 'ok', 'exactly', "that's right",
                    "that is right", "you are correct", "you are right", "for sure"
                ],
                "starters": ['yes', 'yeah', 'yea', 'yep', 'ok', 'exactly', 'sure'],
                "keywords": [
                    'correct', 'right', 'yes', 'yeah', 'yea', 'yep', 'ok', 'exactly',
                    'sure'
                ],
                "exceptions": None
            },
            "disagreements": {
                "examples": [
                    'not right', 'wrong', r'(not)* at all', 'nah', 'nope'
                ],
                "starters": ['no', 'not', 'nah', 'nope', 'at all'],
                "keywords": [
                    'no', 'not', 'wrong', 'nah', 'nope', 'cancel',
                    r'(at all)$'
                ],
                "exceptions": None
            },
            "dismissals": {
                "examples": [
                    r'not(\s*)(to)?(\s*)worry'
                ],
                "starters": [
                    r'never(\s*)mind', r'forget(\s*)(about)?(\s*)it',
                    r"(do not|don't) worry", r"(do not|don't) bother"
                ],
                "keywords": [
                    'not', 'forget', 'bother', 'worry', 'dismissed', r'never(\s*)mind'
                ],
                "exceptions": None
            },
            "gratitude": {
                "examples": [
                    'thank you', 'thanks a lot',
                    'thanks'
                ],
                "starters": [
                    r'thank(s*)',
                ],
                "keywords": [
                    r'thank(s*)'
                ],
                "exceptions": None
            },
            "greetings": {
                "examples": [
                    r'(\w+\s+)?good (morning|afternoon|evening|day)',
                    r'(\w+\s+)?how are you', 'howdy', 'hi', r"(\w+\s+)?what's up",
                    r"(\w+\s+)?what's good", 'hello', 'hey'
                ],
                "starters": [
                    r'good (morning|afternoon|evening|day)',
                    'how are you', 'howdy', 'hi', 'hey', 'yo',
                    "what's up", 'hello'
                ],
                "keywords": [
                    'morning', 'afternoon', 'evening', 'hello', 'hi',
                    'hey', 'how', 'yo', "what's up"
                ],
                "exceptions": None
            },
            "sendoffs": {
                "examples": [
                    'bye', 'bye bye', 'goodbye', 'get out', 'go away',
                    r'good(\s*)night', 'go to bed', 'get some sleep', 'talk later',
                    'see you later', 'i am leaving'
                ],
                "starters": ['go'],
                "keywords": [
                    'bye', 'away', 'sleep', 'out', 'leave', 'leaving',
                    'later', 'see you', r'good(\s*)night'
                ],
                "exceptions": None
            },
            "system_action_request": {
                "examples": [
                    'please turn on my wifi',
                    'open command prompt',
                    r'(\w+)?\s*(open|close) (.+)',
                    r'(\w+)?\s*(start|stop) (.+) app',
                    r'(\w+)?\s*(turn|put) (on|off) (.+)',
                    r'(\w+)?\s*launch (.+) app',
                    r'(\w+)?\s*(activate|deactivate) (.+)',
                    r'(\w+)?\s*(take a screenshot)'
                ],
                "starters": [
                    r'((kindly|please|help (me)?|please help (me)?)?\s*(open|close)\s*)',
                    r'((kindly|please|help (me)?|please help (me)?)?\s*(start|stop)\s*)',
                    r'((kindly|please|help (me)?|please help (me)?)?\s*(turn|put)?\s*(on|off)\s*)',
                    r'((kindly|please|help (me)?|please help (me)?)?\s*(launch)\s*)',
                    r'((kindly|please|help (me)?|please help (me)?)?\s*(activate|deactivate)\s*)',
                    r'((kindly|please|help (me)?|please help (me)?)?\s*(shut(\s*)down)\s*)',
                    r'((kindly|please|help (me)?|please help (me)?)?\s*(restart)\s*)',
                    r'((kindly|please|help (me)?|please help (me)?|take (a)?)?\s*(screenshot)\s*)',
                    r'((kindly|please|help (me)?|please help (me)?)?\s*(set|create) (a)?\s*(reminder)\s*)',
                    r'((kindly|please|help (me)?|please help (me)?)?\s*(set|create) (an)?\s*(alarm)\s*)',
                    r'((kindly|please)?\s*(remind me)\s*)'
                ],
                "keywords": [
                    'open', 'close', 'app',
                    r'(activate|deactivate)',
                    r'(turn|put)?\s*(on|off)',
                    'shut(\s*)down', 'restart', 'set',
                    'screenshot', r'remind(er)?'
                ],
                "exceptions": {
                    "starters": [
                        r"(\w+|please|help (me)?)?\s*(how|what('s|\s(is)|s)?|who|which|why)\s*",
                        r"(.*)(what is|what'?s|what was)",
                        r"how (to|can|would|will|is)"
                    ]
                }
            },
            "ai_customisation_requests": {
                "keywords": [r'change your (name|voice)'],
                "examples": [
                    'change your name', r"(what is|what'?s) your name",
                    'what are you called', 'name you are called'
                ],
                "starters": [
                    r"change your (\w+\s+)(name|voice)"
                ],
                "exceptions": None
            },
            "name_request": {
                "examples": [
                    'your name', r"(what is|what'?s) your name",
                    'what are you called', 'name you are called'
                ],
                "starters": [
                    r"(what is|what'?s)", 'tell me', 'give me', 'what should',
                    r'what do\s+'
                ],
                "keywords": ['your name', 'call you'],
                "exceptions": {
                    "starters": [
                        r"how"
                    ],
                    "contains": ["change your"]
                }
            },
            "time_request": {
                "examples": [
                    r'what time (is|was) it', 'time in',
                    'what says the time', r"(what is|what'?s) the time",
                    'say the time', 'current time', 'what does the time say',
                    'what the time says'
                ],
                "starters": [
                    r"(what is|what's)", 'what says', 'tell me', 'give me'
                ],
                "keywords": ["time"],
                "exceptions": None
            },
            "media_request": {
                "examples": [
                    r'play\s+.+', r'(.+)* song(s)?', r'music(s)?', r'video(s)?',
                    r'album(s)?', r'mixtape(s)?'
                ],
                "starters": [
                    r'play\s+.+', 'sing'
                ],
                "keywords": [
                    'play', 'find', r'song(s)?', 'music', r'video(s)?', r'album(s)?',
                    r'mixtape(s)?', 'sing'
                ],
                "exceptions": None
            },
            "calculation_request": {
                "examples": [
                    r'(\d+\s*(plus|\+)\s*\d+)',
                    r'(\d+\s*(minus|-)\s*\d+)',
                    r'(\d+\s*(divided by|over|\/)\s*\d+)',
                    r'(\d+\s*(multiplied by|times|\*|x)\s*\d+)',
                    r'((\d+\s+(squared))|((square(d)? of)\s+\d+))',
                    r'(\d+\s*(\^)\s*\d+)|(\d+\s*(raise(d)?)?(\s*)to(\sthe)?\s+power(\sof)?\s*\d+)',
                    r'((\d+)?\s*((square )?root(\s(of))?)\s*\d+)'
                ],
                "starters": [
                    "(what is|what'?s)",
                    "solve", "evaluate"
                ],
                "keywords": [
                    r'(plus|\+)',
                    r'(minus|-)',
                    r'(divided by|over|\/)',
                    r"(multiplied by|times|\*|x)",
                    r"((square )?root)",
                    r"(square(d)?)",
                    r"(\^)|((raise(d)?)?(\s*)to(\sthe)?\s+power(\sof)?)"
                ],
                "exceptions": None
            },
            "permission_request": {
                "examples": [
                    'please can i do something'
                ],
                "starters": [
                    r"(\w+\s+)?can\s+(i|they|we|she|he|you)",
                    r"(\w+\s+)?should\s+(i|they|we|she|he)"
                ],
                "keywords": [
                    r"can\s+(i|they|we|she|he|you)",
                    r"should\s+(i|they|we|she|he)",
                    r"(will|would) you"
                ],
                "exceptions": {
                    "starters": ['what', "what", "why", "who", "when"],
                    "contains": None
                }
            },
            "info_request": {
                "examples": [
                    r'(what|why|who|when) (is|was|will|would|were) .+',
                    'how to', "what's .+", r"tell me\s*(.+)?\s*about .+"
                ],
                "starters": ['what', 'whats', 'why', 'who', 'when', 'how'],
                "keywords": [
                    r"what('s)?", "whats", 'why', 'who', 'when', 'how',
                    "tell me"
                ],
                "exceptions": None
            }
        }
        self._custom_classifications = None

        self.units = [
            'zero', 'one', 'two', 'three', 'four', 'five', 'six',
            'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
            'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen',
            'eighteen', 'nineteen'
        ]
        self.tens = [
            '', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy',
            'eighty', 'ninety'
        ]
        self.scales = [
            'hundred', 'thousand', 'million', 'billion', 'trillion', 'quadrillion'
        ]
        self.affiliations = ['friend', 'buddy', 'paddy', 'pal', 'boss']
        self.load_custom_classifications()

    def load_custom_classifications(self):
        """
        Loads all user defined classification rules and adds it to classifications
        if it exists
        """
        path = "../plugins/classifications.json"
        custom_classifications_exists = os.path.isfile(path)
        if custom_classifications_exists:
            with open(path, 'r') as cf:
                content = cf.read()

            classifications = json.loads(content)
            if self.validate_custom_classifications(classifications):
                self._custom_classifications = classifications
                self.classifications = {
                    **self._custom_classifications,
                    **self.classifications
                }
                # print(self._custom_classifications)
            else:
                raise BaseException("The structure of custom classifications is invalid")

    @staticmethod
    def validate_custom_classifications(custom_classifications):
        for classification, rules in custom_classifications.items():
            if "examples" not in rules or "starters" not in rules or "keywords" not in rules:
                return False
            print(rules)
            for rule_type, rule_list in rules.items():
                if rule_list is not None:
                    rule_list = list(
                        rule_list
                        | select(lambda p: re.sub(r"\\w", r"\w", p))
                        | select(lambda p: re.sub(r"\\s", r"\s", p))
                        | select(lambda p: re.sub(r"\\d", r"\d", p))
                        | select(lambda p: re.sub(r"\\W", r"\W", p))
                        | select(lambda p: re.sub(r"\\S", r"\S", p))
                        | select(lambda p: re.sub(r"\\D", r"\D", p))
                    )
                    rules[rule_type] = rule_list
            print(rules)

        return True

    def get_classification(self, sentence):
        """
        Analyzes the sentence given and return possible classification
        of the sentence

        :param sentence: sentence to analyze
        :return: a classification key based on analysis or None if not found
        """
        ret_value = []

        sentence = remove_punctuations(sentence)
        arithmetic_operators_pattern = re.compile(r"(\d+)[/+*-](\d+)")
        for match in arithmetic_operators_pattern.finditer(sentence):
            start, end = match.span()
            operator_position = re.compile(r"[/+*-]").search(sentence[start:end]).span()
            start_of_operator, end_of_operator = operator_position[0] + start, operator_position[1] + start
            sentence = sentence[:start_of_operator] \
                       + re.sub(r"[/+*-]", f" {sentence[start_of_operator:end_of_operator]} ", sentence) \
                       + sentence[end_of_operator:]

        for classification in self.classifications:

            keywords = self.get_keywords(classification)
            examples = self.get_examples(classification)
            starters = self.get_starters(classification)

            keywords = keywords if keywords is not None else []
            examples = examples if examples is not None else []
            starters = starters if starters is not None else []

            if contains(sentence, keywords) and (
                    contains(sentence, examples) or
                    starts_with(sentence, starters)
            ):
                # Check exception rules before returning
                if self.test_exceptions(sentence, classification) is True:
                    # Store classification
                    ret_value.append(classification)

        print(ret_value)
        return ret_value

    def test_exceptions(self, sentence, classification):
        exceptions = self.get_exceptions(classification) or {}
        if not exceptions:
            return True
        else:
            starter_exception_not_exists = "starters" not in exceptions or not exceptions["starters"]
            contain_exception_not_exists = "contains" not in exceptions or not exceptions["contains"]
            pass_starter_exceptions = True if starter_exception_not_exists else not starts_with(sentence,
                                                                                                exceptions["starters"])
            pass_contain_exceptions = True if contain_exception_not_exists else not contains(sentence,
                                                                                             exceptions["contains"])
            return pass_starter_exceptions and pass_contain_exceptions

    def get_affiliations(self):
        return self.affiliations

    def get_examples(self, key):
        return self.classifications[key]["examples"]

    def get_keywords(self, key):
        return self.classifications[key]["keywords"]

    def get_starters(self, key):
        return self.classifications[key]["starters"]

    def get_exceptions(self, key):
        return self.classifications[key]["exceptions"]

    @staticmethod
    def transform_speech_to_other_person(sentence):
        possible_pronouns = ['i', 'my', 'you are', 'me']
        possible_pronoun_replacements = ['you', 'your', 'i am', 'you']

        for i in range(len(possible_pronouns)):
            pronoun = possible_pronouns[i]
            pronoun_replacement = possible_pronoun_replacements[i]

            if contains(sentence, pronoun):
                sentence = re.sub(f' {pronoun} ', f' {pronoun_replacement} ', sentence)

        return sentence

    def transform_numbers_to_text(self, text):
        def make_word_version_of_digit_list(instance, magnitude_of_tens, num):
            _list = []
            _list.insert(0, instance.tens[magnitude_of_tens])
            remaining_digit = num - (magnitude_of_tens * 10)
            if remaining_digit > 0:
                _list.insert(1, instance.units[remaining_digit])
            return _list

        text = remove_punctuations(text)

        #  Pattern to search for an 'a' before any of the scales e.g a thousand
        pattern = re.compile(r'a (hundred|thousand|million|billion|trillion|quadrillion)')
        matches = pattern.finditer(text)

        for match in matches:
            text = text[:match.start()] + 'one' + text[match.start() + 1:]

        # Pattern to search for "digits" before any of the scales e.g 20 million
        pattern = re.compile(r'\d+ (hundred|thousand|million|billion|trillion|quadrillion)')
        matches = pattern.finditer(text)

        for match in matches:
            start, end = match.span()
            digit_and_scale = text[start:end].split()
            digit = int(digit_and_scale[0])

            # Example: 5
            if 0 <= digit < 20:
                word_version_of_digit = self.units[digit]

            # Example: 21
            elif 20 <= digit < 100:
                word_version_of_digit_list = [str(digit)]

                if 20 <= digit < 30:
                    word_version_of_digit_list = make_word_version_of_digit_list(self, 2, digit)
                elif 30 <= digit < 40:
                    word_version_of_digit_list = make_word_version_of_digit_list(self, 3, digit)
                elif 40 <= digit < 50:
                    word_version_of_digit_list = make_word_version_of_digit_list(self, 4, digit)
                elif 50 <= digit < 60:
                    word_version_of_digit_list = make_word_version_of_digit_list(self, 5, digit)
                elif 60 <= digit < 70:
                    word_version_of_digit_list = make_word_version_of_digit_list(self, 6, digit)
                elif 70 <= digit < 80:
                    word_version_of_digit_list = make_word_version_of_digit_list(self, 7, digit)
                elif 80 <= digit < 90:
                    word_version_of_digit_list = make_word_version_of_digit_list(self, 8, digit)
                elif 90 <= digit < 100:
                    word_version_of_digit_list = make_word_version_of_digit_list(self, 9, digit)

                word_version_of_digit = " ".join(word_version_of_digit_list)
            else:
                word_version_of_digit = digit

            digit_and_scale[0] = str(word_version_of_digit)
            text = text[:start] + " ".join(digit_and_scale) + text[end:]

        return text

    def transform_text_to_numbers(self, text):
        num_words = {}
        text = remove_punctuations(text)

        if not num_words:
            num_words['and'] = (1, 0)

            for idx, word in enumerate(self.units): num_words[word] = (1, idx)
            for idx, word in enumerate(self.tens): num_words[word] = (1, idx * 10)
            for idx, word in enumerate(self.scales): num_words[word] = (10 ** (idx * 3 or 2), 0)

        text = self.transform_numbers_to_text(text)

        current = result = None
        revised_text_list = []

        word_list = text.strip().split()
        word_count = 0

        for word in word_list:
            should_not_be_number = False

            if word == 'and':
                # Join tens and unit list into one
                units_and_tens = self.units + self.tens[2:]
                pattern = re.compile(r'(hundred|thousand|million|billion|trillion|quadrillion)\s+and\s+('
                                     + '|'.join(units_and_tens) + ')')
                match = pattern.search(' '.join(word_list[word_count - 1:]))
                should_not_be_number = match is None

            if word not in num_words or should_not_be_number is True:
                if current is not None and result is not None:
                    numbs = result + current
                    revised_text_list.append(str(numbs))
                    current = result = None
                revised_text_list.append(word)

            else:
                current = 0 if current is None else current
                result = 0 if result is None else result

                scale, increment = num_words[word]
                current = current * scale + increment

                if scale > 100:
                    result += current
                    current = 0

            word_count += 1

        if current is not None and result is not None:
            revised_text_list.append(str(int(result + current)))
        return ' '.join(revised_text_list)

    def resolve_into_equation(self, text):
        starters = self.get_starters("calculation_request")
        equation = self.transform_text_to_numbers(text)

        for starter in starters:
            equation = re.sub(starter, '', equation).strip()

        equation = re.sub(r'(multiplied by|times|x)', '*', equation)
        equation = re.sub(r'(plus)', '+', equation)
        equation = re.sub(r'(divided by|over|all over)', '/', equation)
        equation = re.sub(r'(minus)', '-', equation)
        equation = re.sub(r'((raise(d)?)?(\s*)to(\sthe)?\s+power(\sof)?)|(\^)', '**', equation)

        equation_text_version = equation
        equation_text_version = re.sub(r'\*\*', '^', equation_text_version)

        # Check for exponential (squares) patterns
        exponential_pattern = re.compile(r'((\d+\s+(square(d)?))|((square(d)? of)\s+\d+))')
        exponential_pattern_matches = exponential_pattern.finditer(equation)
        if exponential_pattern_matches is not None:
            for match in exponential_pattern_matches:
                matched_text = match.group()
                digit_in_match = int(re.compile(r"(\d+)").search(matched_text).group())
                equation = re.sub(matched_text, f"{digit_in_match ** 2}", equation)
                equation_text_version = re.sub(matched_text, f"{digit_in_match} squared", equation_text_version)

        # Check for root (square root) patterns
        root_pattern = re.compile(r'((square(d)?\s+)?root(\s(of))?\s*\d+)')
        root_pattern_matches = root_pattern.finditer(equation)
        if root_pattern_matches is not None:
            for match in root_pattern_matches:
                matched_text = match.group()
                digit_in_match = int(re.compile(r"(\d+)").search(matched_text).group())
                equation = re.sub(matched_text, f"{sqrt(digit_in_match)}", equation)
                equation_text_version = re.sub(matched_text, f"root {digit_in_match}", equation_text_version)

        # Remove useless words in equation

        equation_list = equation.split(' ')
        pattern = re.compile(r'(\d+)|[/+*-]|\)|\(')

        equation_list = list(
            equation_list
            | where(lambda el: pattern.search(el) is not None and el is not '')
        )

        # Remove useless words in text version of equation
        equation_text_list = equation_text_version.split(' ')
        pattern = re.compile(r'(\d+)|[/+*-]|root|squared|\^|\)|\(')

        equation_text_list = list(
            equation_text_list
            | where(lambda el: pattern.search(el) is not None)
        )

        equation = ' '.join(equation_list).strip()
        # Remove any letters or equal to symbols left in equation
        equation = re.sub(r'[a-z=]', '', equation)

        equation_text_version = ' '.join(equation_text_list).strip()
        print(equation, equation_text_version)
        return {
            "equation": equation,
            "text_equation": equation_text_version
        }

# This is how i test this word processor module and classification
# stop = False
# wp = WordProcessor()
# while stop is False:
#     phrase = input('Type in a sentence to get its classification: ')
#     print(wp.get_classification(phrase))
#     stop_command = input('Type "stop" to exit or press enter to continue:\n>>>')
#     print()
#     if stop_command is 'stop':
#         stop = True
