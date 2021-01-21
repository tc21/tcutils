from typing import Any, Optional, Sequence, Union


def format_dict(d: dict) -> str:
    ''' Formats a dictionary with a more beautiful format.
        (note: does not recursively format)
        input:
            {'key': 'item', 'otherkey': 'multiline\nitem'}
        output:
            {
                key: item
                otherkey: multiline
                          item
            }
    '''
    s = '{\n'
    for key, value in d.items():
        key_string = f'    {key}: '
        s += (key_string +
              ('\n' + ' ' * len(key_string)).join(str(value).split('\n')) +
              '\n')
    s += '}'
    return s


def print_dict(d: dict):
    ''' Prints a dictionary with a more beautiful format.
        input:
            {'key': 'item', 'otherkey': 'multiline\nitem'}
        output:
            {
                key: item
                otherkey: multiline
                          item
            }
    '''
    print(format_dict(d))


def format_list(l: list) -> str:
    if len(l) <= 1:
        return repr(l)

    fold_at = 78
    single_line_at = 18

    reprs = [repr(x) for x in l]

    if max(map(len, reprs)) > single_line_at:
        lines = reprs
    else:
        lines = [reprs[0]]

        for x in reprs[1:]:
            if len(lines[-1]) + len(x) > fold_at - 2:
                lines.append(x)
            else:
                lines[-1] += ', ' + x

    if len(lines) == 1:
        return '[' + lines[0] + ']'

    return (
        '[' + lines[0] + ',\n' +
        ''.join(' ' + x + ',\n' for x in lines[1:-1]) +
        ' ' + lines[-1] + ']'
    )


def print_list(l: list):
    print(format_list(l))


def format_table(
    t: list[list[Any]],
    max_width: Optional[Union[int, list[int]]] = None,
    spacing: Union[int, list[int]] = 1
) -> str:
    '''
    Formats a table (a 'list of lists') with a format similar to,
    well, tables.

    todo: probably smarter spacing such as
    with len(t[0]) = 5:
        [1, 2, 3] -> [1, 2, 3, 3]
        {0: 2, 3: 3} -> [2, 1, 1, 3]
        {0: 1, 3: 1, 'default': 5} -> [1, 5, 5, 1]
    (not implemented here due to questions about its intuitive-ness)
    '''

    # A. Input Validation

    # copy the list and convert to strings
    t = [[str(c) for c in r] for r in t]

    if len(t) == 0:
        return ''

    columns = len(t[0])

    if isinstance(max_width, int):
        max_width = [max_width] * columns

    if isinstance(spacing, int):
        spacing = [spacing] * (columns - 1)

    if max_width is not None:  # an incorrect type will simply throw an exception
        if len(max_width) != columns:
            raise ValueError(f'max_width: excepted {columns} items, got {len(max_width)}')

    if len(spacing) != columns - 1:
        raise ValueError(f'max_width: excepted {columns - 1} items, got {len(spacing)}')

    # a shortcut
    spacing.append(0)

    # B. Input Processing
    widths = [0] * columns
    for row in t:
        for i, col in enumerate(row):
            if max_width is not None and len(col) > max_width[i]:
                row[i] = col[:max_width[i]]
            if len(col) > widths[i]:
                widths[i] = len(col)

    # note: this list comprehension could be used if we didn't have max_width
    # widths = [max(len(row[i]) for row in t) for i in range(columns)]

    # C. Formatting
    # this list comprehension:
    # 1. formats each string in the list to be exactly widths[i] chars long
    # 2. appends spacing[i] spaces to the end
    t = [[f'{c:{widths[i]}}' + ' ' * spacing[i] for i, c in enumerate(r)] for r in t]

    return '\n'.join(''.join(col for col in row) for row in t)


def print_table(
    t: list[list[Any]],
    max_width: Optional[Union[int, list[int]]] = None,
    spacing: Union[int, list[int]] = 1
):
    print(format_table(t, max_width, spacing))


def shorten(text: str, length_including_ellipsis=20, fullwidth_aware=True, force_ellipsis=False) -> str:
    ''' shortens a string to a certain length (default=20), either by returning
        the string unmodified or by cutting off the string and adding ellipses
        to the end; by default, tries to be aware of full-width characters, and
        doesn't add ellipses if the text does not to be shortened '''

    length_before_ellipsis = length_including_ellipsis - 3
    if not fullwidth_aware:
        if not force_ellipsis and len(text) <= length_including_ellipsis:
            return text
        return text[:length_before_ellipsis] + '...'

    lengths_from_beginning = [0]

    for c in text:
        if lengths_from_beginning[-1] > length_including_ellipsis:
            break

        next_length = lengths_from_beginning[-1] + (2 if is_cjk_fullwidth(c, True) else 1)
        lengths_from_beginning.append(next_length)

    if not force_ellipsis and lengths_from_beginning[-1] <= length_including_ellipsis:
        return text

    for i, l in enumerate(lengths_from_beginning):
        if l > length_before_ellipsis:
            return text[:i-1] + '...'

    return text + '...'


def is_cjk_fullwidth(char: str, check_fully=False):
    ''' Returns True if char is a full-width CJK chararcter. '''
    # todo: apparently characters such as ï½ž: FULLWIDTH TILDE were missed
    #
    __cjk_reduced_codepoints = (
        # The following codepoints, compressed
        # 3040 - 309F   Hiragana
        # 30A0 - 30FF   Katakana
        # 3130 - 318F   Hangul Compatibility Jamo
        # 3190 - 319F   Kanbun
        # 31F0 - 31FF   Katakana Phonetic Extensions
        # 3400 - 4DBF   CJK Unified Ideographs Extension A
        # 4E00 - 9FFF   CJK Unified Ideographs
        # F900 - FAFF   CJK Compatibility Ideographs
        # FE30 - FE4F   CJK Compatibility Forms
        (0x3040, 0x30ff), (0x3130, 0x319f), (0x31f0, 0x3fff),
        (0x3400, 0x4dbf), (0x4e00, 0x9fff), (0xf900, 0xfaff),
        (0xfe30, 0xfe4f)
    )
    __cjk_codepoints = (
        # The following codepoints, compressed
        # 1100 - 11FF   Hangul Jamo
        # 2E80 - 2EFF   CJK Radicals Supplement
        # 2F00 - 2FDF   Kangxi Radicals
        # 2FF0 - 2FFF   Ideographic Description Characters
        # 3000 - 303F   CJK Symbols and Punctuation
        # 3040 - 309F   Hiragana
        # 30A0 - 30FF   Katakana
        # 3100 - 312F   Bopomofo
        # 3130 - 318F   Hangul Compatibility Jamo
        # 3190 - 319F   Kanbun
        # 31A0 - 31BF   Bopomofo Extended
        # 31C0 - 31EF   CJK Strokes
        # 31F0 - 31FF   Katakana Phonetic Extensions
        # 3200 - 32FF   Enclosed CJK Letters and Months
        # 3300 - 33FF   CJK Compatibility
        # 3400 - 4DBF   CJK Unified Ideographs Extension A
        # 4E00 - 9FFF   CJK Unified Ideographs
        # AC00 - D7AF   Hangul Syllables
        # F900 - FAFF   CJK Compatibility Ideographs
        # FE30 - FE4F   CJK Compatibility Forms
        # FF00 - FFEF   Halfwidth and Fullwidth Forms
        # 1F200 - 1F2FF   Enclosed Ideographic Supplement
        # 20000 - 2A6DF   CJK Unified Ideographs Extension B
        # 2A700 - 2B73F   CJK Unified Ideographs Extension C
        # 2B740 - 2B81F   CJK Unified Ideographs Extension D
        # 2B820 - 2CEAF   CJK Unified Ideographs Extension E
        # 2F800 - 2FA1F   CJK Compatibility Ideographs Supplement
        (0x1100, 0x11ff), (0x2e80, 0x2fdf), (0x2ff0, 0x4dbf),
        (0x4e00, 0x9fff), (0xac00, 0xd7af), (0xf900, 0xfaff),
        (0xfe30, 0xfe4f), (0xfe00, 0xffef), (0x1f200, 0x1f2ff),
        (0x20000, 0x2a6df), (0x2a700, 0x2ceaf), (0x2f800, 0x2fa1f)
    )

    cp: Sequence[tuple[int, int]] = __cjk_reduced_codepoints

    if check_fully:
        cp = __cjk_codepoints

    return any(start <= ord(char) <= end for start, end in cp)


def color(s: str, color='default') -> str:
    ''' returns a string that will be colored in linux terminals '''
    colors = {
        'default': '0',
        'black': '00;30',
        'red': '00;31',
        'green': '00;32',
        'yellow': '00;33',
        'blue': '00;34',
        'purple': '00;35',
        'cyan': '00;36',
        'lightgray': '00;37',
        'darkgray': '01;30',
        'boldred': '01;31',
        'boldgreen': '01;32',
        'boldyellow': '01;33',
        'boldblue': '01;34',
        'boldpurple': '01;35',
        'boldcyan': '01;36',
        'white': '01;37'
    }

    aliases = {
        '': 'white',
        'k': 'black',
        'r': 'red',
        'g': 'green',
        'y': 'yellow',
        'b': 'blue',
        'magenta': 'purple',
        'm': 'purple',
        'c': 'cyan',
        'gray': 'darkgray',
        'w': 'white'
    }

    sanitized_input = ''.join(color.lower().split())
    color_name = aliases.get(sanitized_input, sanitized_input)
    color_code = colors[color_name]
    default = colors['default']

    return f'\033[{color_code}m{s}\033[{default}m'
