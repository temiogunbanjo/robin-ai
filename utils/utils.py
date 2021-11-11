import random
import re


def convert_dictionary_to_string(dictionary):
    string = '{\n'
    for key in dictionary:
        string += f"  {key}: {dictionary[key]},\n"
    string += '}'
    return string


def to_capitalize_case(text):
    """
    Capitalize the first letter of each word in text

    :param text: Text to capitalize
    :return: str
    """
    word_list = text.split()
    for i in range(len(word_list)):
        word_list[i] = word_list[i][0:1].upper() + word_list[i][1:].lower()
    return " ".join(word_list)


# STATIC FUNCTIONS ========================================================
def contains(text, search):
    """
    Checks for an exact phrase match in the text and return either True or False
    depending on whether phrase is found

    :param text: The text to be searched
    :param search: The phrase to search for in text. Can be of type str or list
    :return: Boolean
    """
    text = str(text).lower()

    if type(search).__name__ == 'list':
        for a_search in search:
            # pattern = text starts with a_search and is followed by a non word
            #           or a_search is somewhere in the text and is preceded
            #           and succeeded by a space(s)
            #           or a_search is at the end of text and is preceded by zero
            #           or more spaces
            pattern = re.compile(r'(^{0}(\s+|-+|_+))|((\s+|-+|_+){0}(\s+|-+|_+))+|((\s*|-*|_*){0}$)'.format(a_search))
            match = pattern.search(text)

            if match is not None:
                # print(f'contains exact: {a_search}, {text}')
                return True
        return False
    else:
        pattern = re.compile(r'(^{0}(\s+|-+|_+))|((\s+|-+|_+){0}(\s+|-+|_+))+|((\s*|-*|_*){0}$)'.format(search))
        match = pattern.search(text)
        # print(match)
        return match is not None


def contains_count(text, search_list):
    """
    Checks for an exact phrase match in the text and return the number of
    element in search_list found in text

    :param text: The text to be searched
    :param search_list: The phrase to search for in text. Can be of type str or list
    :return: integer
    """
    no_of_keywords_in_text = 0
    for keyword in search_list:
        if contains(text, keyword):
            no_of_keywords_in_text += 1

    return no_of_keywords_in_text


def starts_with(text, search):
    text = text.lower()
    if type(search).__name__ == 'list':
        for a_search in search:
            if text.startswith(a_search) or re.compile(r'(^{0}\s+)|{0}$'.format(a_search)).search(text) is not None:
                # print(f'Starts with exact: {a_search}, {text}')
                return True
        return False
    else:
        return text.startswith(search) or re.compile(r'(^{0}\s+)|{0}$'.format(search)).search(text) is not None


def rgba_ratio(red, green, blue, alpha):
    """
    :param red:
    :param green:
    :param blue:
    :param alpha:
    :return: tuple
    """
    red_ratio = int(red) / 255
    green_ratio = int(green) / 255
    blue_ratio = int(blue) / 255
    alpha_ratio = int(alpha) / 1
    print((red_ratio, green_ratio, blue_ratio, alpha_ratio))
    return red_ratio, green_ratio, blue_ratio, alpha_ratio


def ai_should_proceed_with_action():
    return random.choice([True, False, None]) is True


def get_most_similar_elements(keywords_list, target_list):
    """
    Finds elements in target_list that closely match list_1

    :param keywords_list:
    :param target_list:
    :return: list
    """
    similarity_list = []
    for i in range(len(target_list)):
        similarity_list.append((i, contains_count(target_list[i], keywords_list)))

    return similarity_list


def prefix_list_elements(prefix, list_):
    return list(map(lambda element: f"{prefix}{element}", list_))


def remove_list_elements(list_of_items, items_to_remove):
    for item in items_to_remove:
        if item in list_of_items:
            list_of_items.remove(item)
    return list_of_items


def remove_punctuations(sentence):
    """
    Removes all unnecessary punctuations in sentence

    :param sentence:
    :return:
    """
    for char in [',', '?', '.', '"', '`', '!']:
        sentence = sentence.replace(char, '')
    return sentence
