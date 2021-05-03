import json
import os
import os.path
import tc.utils
from tc.utils.fileutils import surface, is_common_image as is_image
from typing import Tuple, Optional, List
import sys
import unicodedata


class Token:
    start_tokens = '([{【'
    end_tokens = ')]}】'
    chinese_indicators = ('中国翻訳', '汉化', '大報社', '漢化', '翻译')

    start_delimiter: str
    end_delimiter: str
    name: str
    _is_chinese: Optional[bool]

    def __init__(self, start_delimiter: str, name: str):
        self.start_delimiter = start_delimiter
        self.end_delimiter = self.end_tokens[self.start_tokens.find(start_delimiter)]
        self.name = name
        self._is_chinese = None

    @property
    def is_chinese(self) -> bool:
        if self._is_chinese is None:
            self._is_chinese = False
            for indicator in Token.chinese_indicators:
                if indicator in self.name:
                    self._is_chinese = True
                    break

        return self._is_chinese

    def __str__(self) -> str:
        return self.start_delimiter + self.name + self.end_delimiter


class Comic:
    raw_name: str
    tokens: List[Token]
    is_chinese: bool
    author: Optional[str]
    name: str

    def __init__(self, raw_name: str):
        '''Parses comic information based on a raw name.

        A raw name is a raw string surrounded by any number or tags.

        A tag is a raw string surrounded by one of the following matching sets
        of brackets:
            () [] {} 【】

        Tags cannot be nested, so the tag `[outer(inner)]` get parsed as a
        single tag with the content `outer(inner)`, and the tag `[outer[inner]]`
        gets parsed as a single tag with the content `outer[inner` followed by
        a raw `]` character.
        '''
        self.raw_name = raw_name
        self.tokens, self.name = Comic.pop_tokens(unicodedata.normalize('NFKC', raw_name))
        self.is_chinese = False
        self.author = None

        for token in self.tokens:
            if not self.is_chinese and token.is_chinese:
                self.is_chinese = True
            elif not self.author and token.start_delimiter == '[':
                self.author = token.name
            elif self.author and self.is_chinese:
                break

        self.name = self.name and self.name.strip()
        self.author = self.author and self.author.strip()

    def suggested_name(self) -> str:
        return self.name + (' (CN)' if self.is_chinese else '')

    @staticmethod
    def has_token(name: str, front=True) -> bool:
        if front:
            return bool(name and name[0] in Token.start_tokens)
        else:
            return bool(name and name[-1] in Token.end_tokens)

    @staticmethod
    def pop_token(name: str, front=True) -> Tuple[Token, str]:
        if front:
            start_token = name[0]
            end_token = Token.end_tokens[Token.start_tokens.find(start_token)]
            end = name.find(end_token)
            token = name[1:end]
            remainder = name[end+1:]
        else:
            start_token = Token.start_tokens[Token.end_tokens.find(name[-1])]
            start = -(name[::-1].find(start_token)) - 1
            token = name[start+1:-1]
            remainder = name[:start]
        return Token(start_token, token), remainder

    @staticmethod
    def pop_tokens(name: str) -> Tuple[List[Token], str]:
        tokens: List[Token] = []

        while True:
            name = name.strip()
            new_token = False
            if Comic.has_token(name, front=True):
                token, name = Comic.pop_token(name, front=True)
                tokens.insert(0, token)
                new_token = True
            if Comic.has_token(name, front=False):
                token, name = Comic.pop_token(name, front=False)
                tokens.append(token)
                new_token = True
            if not new_token:
                break

        return tokens, name

    def __str__(self):
        return self.name + ': ' + ''.join(map(str, self.tokens))


def get_info(path: str) -> Tuple[Optional[str], Optional[str]]:
    '''Attempts to get author and title information from a comic.

    Currently supports the following:
     - `info.json` and `info.txt` from ex-hentai downloaders
     - the folder's basename in standard format (refer to the `Comic` class)

    Also adds language information, but only for Chinese
    '''
    if os.path.isdir(path):
        if 'info.json' in os.listdir(path):
            info_path = os.path.join(path, 'info.json')
            info = json.load(open(info_path, encoding='utf-8'))
            gallery_info = info['gallery_info']
            title = gallery_info['title_original']
            language = gallery_info['language']
            comic = Comic(title)
            formatted_name = comic.name + (' (CN)' if language.lower() == 'chinese' else '')
            return comic.author, formatted_name
        elif 'info.txt' in os.listdir(path):
            info_path = os.path.join(path, 'info.txt')
            title = ''
            with open(info_path, encoding='utf-8') as info_file:
                for line in info_file:
                    if line.startswith('http'):
                        break
                    title = line.strip()
                    break
            comic = Comic(title)
            formatted_name = comic.suggested_name()
            return comic.author, formatted_name
        elif any(is_image(f) for f in os.listdir(path)):
            title = os.path.basename(path)
            comic = Comic(title)
            formatted_name = comic.suggested_name()
            return comic.author, formatted_name
        else:
            return None, None
    else:
        basename = os.path.basename(path)
        title, _ = os.path.splitext(basename)
        comic = Comic(title)
        formatted_name = comic.suggested_name()
        return comic.author, formatted_name


def organize(path: str = os.path.curdir, force_all=False):
    '''Organizes all items identified as a comic in the current directory.

    To be successfully identified as a comic, it must contain an `info.json` or
    `info.txt` file in its root folder, or have a folder name conforming to the
    standard format (refer to the `Comic` class)

    Unlike `tc.dlsite.organize`, organized items stay in the current directory.
    '''
    for item in os.listdir(path):
        if force_all:
            surface(item)
        full_path = os.path.join(path, item)
        author, name = get_info(full_path)
        if author and name:
            author = tc.utils.sanitize_filename(author)
            name = tc.utils.sanitize_filename(name)
            parent_path = os.path.join(path, author)

            if not os.path.isdir(parent_path):
                os.mkdir(parent_path)

            renamed = tc.utils.move(full_path, folder=parent_path, filename=name)
            success = os.path.exists(renamed)  # in theory this should always be true

            if success:
                final_path = os.path.join(parent_path, name)
                print(f'{full_path}\n\t> {final_path}', file=sys.stderr)
                surface(final_path)
                continue

            print(f'{full_path}\n\tunsuccessful', file=sys.stderr)
        else:
            print(f'{full_path}\n\tskipped', file=sys.stderr)
