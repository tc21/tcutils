from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple, Union

import tc.utils
from .comic import Comic


PageSpec = Union[Tuple[int, int], int, str]
SubcomicSpec = Union[List[Union[PageSpec, str]],
                     List[Tuple[PageSpec, str]],
                     str]


@dataclass
class SubcomicInfo:
    name: str
    start: int
    end: Optional[int] = None

    @classmethod
    def parse(cls, page_spec: PageSpec, name: str) -> SubcomicInfo:
        if isinstance(page_spec, str):
            pages = page_spec.split('-')
            return cls(name, *(int(p) for p in pages))

        if isinstance(page_spec, int):
            return cls(name, page_spec)

        return cls(name, *page_spec)

    def range(self, *, upper_limit: int) -> range:
        '''note: `upper_limit` is bounds-inclusive, and so is the returned range'''
        if self.end is not None and self.end < upper_limit:
            upper_limit = self.end

        return range(self.start, 1 + upper_limit)


class SubcomicSpecification:
    def __init__(self, spec: Iterable[SubcomicInfo]):
        '''Internal-only init function.

        This function finishes initialization by correctly assigning the `end`
        property to each `SubcomicInfo` object, and is a required part of initialization.
        '''

        spec = list(spec)
        for i in range(len(spec) - 1):
            if spec[i].end is None:
                spec[i].end = spec[i+1].start - 1

        self.spec = [s for s in spec if s.name != '']

        # verification
        v_set = set()
        v_max = None
        for s in self.spec:
            if v_max is not None and s.start > v_max:
                raise ValueError(f'page {s.start} repeated in specification')

            if s.end is None:
                if v_max is not None:
                    raise ValueError(f'page <infinity> repeated in specification')
                v_max = s.start - 1

            for page in s.range(upper_limit=0):
                if page in v_set:
                    raise ValueError(f'page {page} repeated in specification')
                v_set.add(page)


    def __iter__(self):
        return iter(self.spec)

    def __repr__(self):
        return f'<{self.__class__.__name__} {repr(self.spec)}>'

    def pretty_print(self):
        def format_page(info: SubcomicInfo) -> str:
            if info.end is None:
                return f'P{info.start}...'
            return f'P{info.start}-{info.end}'

        return tc.utils.format_table([[format_page(s), s.name] for s in self.spec])

    @classmethod
    def parse(cls, spec: SubcomicSpec) -> SubcomicSpecification:
        '''Parses a specification into a SubcomicSpecification object.

        Accepted specifictation syntaxes:
        - A list of 2-tuples, where the first item in each tuple is a page
          specification and the second item is a name.
        - A flattened list of 2-tuples, where each odd-numbered item in the list
          if a page specification and each even-numbered item is a name.
        - A newline-separated string, where each line is a page specification
          (options 3 or 4), followed by a space, followed by a name.

        A page specification can be:
        - An `int` indicating the starting page (option 1)
        - A 2-tuple of `int`s indicating the starting page and ending page (inclusive) (option 2)
        - `str(Option 1)` (option 3)
        - `'-'.join(Option 2)` (option 4)

        Restrictions:
        - Pages must be listed in order from small to large.
        - Each page can only be contained in the specification once.
        - An item with an empty name is removed from the final result, allowing
          you to ignore pages in that way.

        Some examples are given in the example script comic_map_subfolders.py
        '''
        if isinstance(spec, str):
            lines = []

            for line in spec.split('\n'):
                stripped_line = line.strip()
                if stripped_line == '':
                    continue
                split_line = stripped_line.split(' ', 1)
                if len(split_line) == 1:
                    raise ValueError(f"line '{line}' is malformed")
                lines.append(split_line)

            return cls(SubcomicInfo.parse(page_spec, name) for page_spec, name in lines)

        # detect if the list is flattened or not by checking if it contains a string
        # note: mypy: the types here aren't statically guaranteed, but by convention
        if len(spec) >= 2 and isinstance(spec[1], str):
            # spec: List[PageSpec, str, PageSpec, str, ...]
            return cls(SubcomicInfo.parse(spec[i], spec[i+1]) for i in range(0, len(spec), 2))  # type: ignore

        spec_: List[Tuple[PageSpec, str]] = spec  # type: ignore
        return cls(SubcomicInfo.parse(page_spec, name) for page_spec, name in spec_)


def organize_subcomics(
    folder: str,
    spec: Union[SubcomicSpec, SubcomicSpecification],
    offset: int = 0,
    naming_offset: Optional[int] = None,
    dry_run=False
):
    '''Organizes items in a folder to indexed subfolders.

    For documentation, see `SubcomicSpecification.parse(spec: SubcomicSpec)`
    '''
    if naming_offset is None:
        naming_offset = offset

    if not isinstance(spec, SubcomicSpecification):
        spec = SubcomicSpecification.parse(spec)

    file_list = tc.utils.listdir(folder)

    for info in spec:
        new_folder_name = tc.utils.sanitize_filename(f'{info.start + naming_offset} - {info.name}')
        new_folder = os.path.join(folder, new_folder_name)
        if dry_run:
            print(f'will create folder {new_folder_name}')
        else:
            os.mkdir(new_folder)

        for i in info.range(upper_limit=len(file_list) - offset):
            i -= 1  # account for 1-indexedness
            if dry_run:
                print(f'will move file {file_list[i+offset]} into folder {new_folder_name}')
            else:
                origin_file = os.path.join(folder, file_list[i+offset])
                tc.utils.move(origin_file, folder=new_folder)

def organize_subcomics_with_artists(
    folder: str,
    spec: Union[SubcomicSpec, SubcomicSpecification],
    offset: int = 0,
    universal_suffix: str = '',
    dry_run=False
):
    '''Organizes items in a folder into a hierarchical structure.

    List names in Comic standard format (see `tc.comics.Comic`)

    For documentation, see `tc.comics.SubcomicSpecification.parse(spec: SubcomicSpec)`
    '''
    if not isinstance(spec, SubcomicSpecification):
        spec = SubcomicSpecification.parse(spec)

    file_list = tc.utils.listdir(folder)

    for info in spec:
        comic = Comic(info.name)

        if comic.author is None:
            comic.author = '~unspecified author'

        author_name = tc.utils.sanitize_filename(comic.author)
        title = tc.utils.sanitize_filename(comic.suggested_name() + universal_suffix)

        author_folder_name = os.path.join(folder, author_name)
        if not os.path.isdir(author_folder_name):
            if dry_run:
                print(f'will create folder {author_name}')
            else:
                os.mkdir(author_folder_name)


        new_folder_name = os.path.join(author_name, title)
        new_folder = os.path.join(folder, new_folder_name)
        if dry_run:
            print(f'will create folder {new_folder_name}')
        else:
            os.mkdir(new_folder)

        for i in info.range(upper_limit=len(file_list) - offset):
            i -= 1  # account for 1-indexedness
            if dry_run:
                print(f'will move file {file_list[i+offset]} into folder {new_folder_name}')
            else:
                origin_file = os.path.join(folder, file_list[i+offset])
                tc.utils.move(origin_file, folder=new_folder)
