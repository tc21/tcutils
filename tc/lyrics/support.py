from .html import word, line, content, header, html, space


class Word:
    def __init__(self, text, ruby=None):
        self.text = text
        self.ruby = ruby

    def __str__(self):
        if self.ruby is None:
            return self.text
        return f'[{self.text}]({self.ruby})'

    def to_html(self):
        return word(self.text, self.ruby)


class Line:
    def __init__(self, words=None):
        if words is None:
            self.words = []
        else:
            self.words = words

    def __str__(self):
        return ''.join(str(w) for w in self.words)

    def to_html(self):
        if len(self.words) == 0:
            return space()
        return line(''.join(w.to_html() for w in self.words))


class Content:
    def __init__(self, lines=None):
        if lines is None:
            self.lines = []
        else:
            self.lines = lines

    def __str__(self):
        return '\n'.join(str(l) for l in self.lines)

    def to_html(self):
        return content('\n'.join(l.to_html() for l in self.lines))


class Header:
    def __init__(self, title, info=None):
        self.title = title
        self.info = info

    def __str__(self):
        if self.info is None:
            return f'{self.title}\n========'
        return f'{self.title}\n{self.info}\n========'

    def to_html(self):
        return header(self.title, self.info)


class Html():
    @staticmethod
    def generate(title, header, content):
        return html(title, header, content)


def is_ruby_base(char):
    """ Adapted from tc.utils.is_cjk_fullwidth """
    __codepoints = (
        # The following codepoints, compressed
        # 2E80 - 2EFF   CJK Radicals Supplement
        # 2F00 - 2FDF   Kangxi Radicals
        # 3400 - 4DBF   CJK Unified Ideographs Extension A
        # 4E00 - 9FFF   CJK Unified Ideographs
        # F900 - FAFF   CJK Compatibility Ideographs
        # 20000 - 2A6DF   CJK Unified Ideographs Extension B
        # 2A700 - 2B73F   CJK Unified Ideographs Extension C
        # 2B740 - 2B81F   CJK Unified Ideographs Extension D
        # 2B820 - 2CEAF   CJK Unified Ideographs Extension E
        # 2F800 - 2FA1F   CJK Compatibility Ideographs Supplement
        (0x2e80, 0x2fdf), (0x3400, 0x4dbf), (0x4e00, 0x9fff), (0xf900, 0xfaff),
        (0x20000, 0x2a6df), (0x2a700, 0x2ceaf), (0x2f800, 0x2fa1f)
    )
    return any(start <= ord(char) <= end for start, end in __codepoints)
