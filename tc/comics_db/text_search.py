# This is a copy of ComicsViewer..Search.cs
from enum import Enum, auto
from typing import List, Optional, Tuple

Tokens = List[Tuple[str, str]]
SplitTokensResult = Tuple[Tokens, Optional[str]]

class ParserMode(Enum):
    Initial = auto()
    String = auto()
    StringEnd = auto()
    Argument = auto()

def compile_search(search_term: str) -> Tuple[List[str], List[str], List[str], List[str], Optional[bool]]:
    tokens, _ = split_tokens(search_term, correct_errors=True)

    names = []
    authors = []
    categories = []
    tags = []
    loved = None

    for key, value in tokens:
        if key == 'title':
            # we don't have the ability to search separately for titles yet
            names.append(value)
        elif key == 'author':
            authors.append(value)
        elif key == 'category':
            categories.append(value)
        elif key == 'tag':
            tags.append(value)
        elif key == 'loved':
            if value.lower().startswith('t'):
                loved = True
        else:
            # we won't throw an error, we'll just let it search
            names.append(value)

    return names, authors, categories, tags, loved


def split_tokens(search_term: str, correct_errors=False) -> SplitTokensResult:
    ''' Returns a tuple (result, error) '''

    result = []

    last_token = ''
    parser_cache = ''
    parser_mode = ParserMode.Initial
    parser_index = 0

    def push_token():
        nonlocal last_token, parser_cache, parser_mode

        result.append((last_token, parser_cache))
        last_token = ''
        parser_cache = ''
        parser_mode = ParserMode.Initial

    def error(message: str) -> SplitTokensResult:
        if correct_errors:
            remaining_search_term = parser_cache + search_term[parser_index:].replace('"', '')
            result.append((last_token, remaining_search_term))

        return result, message

    while parser_index < len(search_term):
        next_char = search_term[parser_index]

        if parser_mode == ParserMode.String:
            if next_char == '"':
                parser_mode = ParserMode.StringEnd
            else:
                parser_cache += next_char

        elif parser_mode == ParserMode.StringEnd and next_char not in ': ':
            return error('Cannot mix quoted and non-quoted strings')

        elif next_char == '"':
            if parser_cache != '':
                return error('Cannot mix quoted and non-quoted strings')

            parser_mode = ParserMode.String

        elif next_char == ':':
            if parser_mode == ParserMode.Argument:
                return error("Argument indicator ':' cannot appear twice in an argument")

            last_token = parser_cache
            parser_cache = ''
            parser_mode = ParserMode.Argument

        elif next_char == ' ':
            if parser_cache != '':
                push_token()
        else:
            parser_cache += next_char

        parser_index += 1

    if parser_cache != '':
        push_token()

    return result, None
