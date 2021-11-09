import re
from math import sqrt

from pipe import where

from core.processor import WordProcessor


def resolve_into_equation(equation_text):
    starters = WordProcessor().get_starters("calculation_request")
    equation = equation_text

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


def calculation_request_handler(ai_engine_instance, command, command_classifications=None):
    response_to_command = []
    has_modified_command = False
    modified_command = command

    if command_classifications is None:
        command_classifications = []

    result = resolve_into_equation(command)
    answer = eval(result["equation"])
    ai_engine_instance.talk(f'{result["text_equation"]} is {answer}')

    if "calculation_request" in command_classifications:
        command_classifications.remove("calculation_request")

    return {
        "original_command": command,
        "modified_command": modified_command,
        "has_modified_command": has_modified_command,
        "command_classifications": command_classifications,
        "responses": response_to_command
    }
