import sys
import io
import re
from .support import Word, Line, Content, Header, Html, is_ruby_base


def convert_ruby(source=None, dest=None):
    # This function should be delegated to other code
    if source is None:
        source_str = sys.stdin.read()
    elif isinstance(source, str):
        source_str = source
    else:
        source_str = source.read()
    if len(source_str) == 0:
        print('source is empty')
        return

    result = parse_str(source_str)

    if dest is None:
        sys.stdout.write(result)
    else:
        dest.write(result)


def parse_str(s):
    """ This function generally requires a file with valid syntax. More
        specific requirements (that may be temporary) are described in this
        function """
    # preparation - requires s to not only contain whitespace
    lines = [l.strip() for l in s.split('\n')]

    # first pass - requires one line to contain only "="
    split = -1
    for i in range(len(lines)):
        line = lines[i]
        if len(line) > 0 and all(c == '=' for c in line):
            split = i
            break

    header_lines = lines[:split]
    content_lines = lines[split+1:]

    while len(header_lines[0]) == 0:
        header_lines = header_lines[1:]
    while len(header_lines[-1]) == 0:
        header_lines = header_lines[:-1]
    while len(content_lines[0]) == 0:
        content_lines = content_lines[1:]
    while len(content_lines[-1]) == 0:
        content_lines = content_lines[:-1]

    # second pass - requires len(header_lines) >= 1, len(content_lines) >= 1
    title = header_lines[0]
    info = '\n'.join(header_lines[1:])
    header_str = Header(title, info).to_html()

    content = Content()
    for content_line in content_lines:
        line = Line()
        # needs to be in another function
        for word in parse_words(content_line):
            line.words.append(word)  # accounts for when parse_words is empty
        content.lines.append(line)

    content_str = content.to_html()

    return Html.generate(title, header_str, content_str)


def parse_words(line):
    saved = ''  # completely processed
    cache = ''  # processed but may be needed later
    while len(line) != 0:
        next_char, line = line[0], line[1:]
        if next_char == '[':
            saved += cache
            cache = ''
            if saved != '':
                yield Word(saved)
                saved = ''
            match = re.match(r'([^)]+)\]\(([^)]+)\)', line)
            if match is None:
                raise SyntaxError()
            text, ruby = match.groups()
            yield Word(text, ruby)
            line = line[match.end():]
        elif next_char == '(':
            if cache == '':
                raise SyntaxError()
            if saved != '':
                yield Word(saved)
                saved = ''
            end = line.find(')')
            if end == -1:
                raise SyntaxError('Unmatched parenthesis')
            ruby, line = line[:end], line[end+1:]
            yield Word(cache, ruby)
            cache = ''

        elif next_char == ']' or next_char == ')':
            raise SyntaxError('Unmatched parenthesis')
        elif is_ruby_base(next_char):
            cache += next_char
        else:
            saved += cache + next_char
            cache = ''

    saved += cache
    if saved != '':
        yield Word(saved)
