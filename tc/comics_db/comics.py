from __future__ import annotations

import datetime
import json
import os
import random
import re
import subprocess
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree

from natsort import natsorted

import tc.sqlite.manager as tcsql
import tc.subfiles
from tc.comics_db.text_search import compile_search


class Comic:
    def __init__(self, data: List[str], tags: List[str], playlists: List[str]):
        self.path = data[0]
        self.unique_identifier = data[1]
        self.title = data[2]
        self.author = data[3]
        self.category = data[4]
        self.display_title = data[5] or self.title
        self.loved = data[6] == 1
        self.date_added = data[7][:10]
        self.tags = tags
        self.playlists = playlists

    def __repr__(self):
        return f'<Comic {repr(self.unique_identifier)}>'

    def get_sort_key(self, primary_key: str) -> Iterable[Any]:
        if primary_key == 'title':
            return self.display_title.lower(), self.author.lower()
        if primary_key == 'category':
            return self.category.lower(), self.author.lower(), self.display_title.lower()
        if primary_key == 'random':
            return random.random(),
        if primary_key == 'date added':
            dt = datetime.datetime.strptime(self.date_added, '%Y-%m-%d')
            return -dt.toordinal(), self.author.lower(), self.display_title.lower()

        return self.author.lower(), self.display_title.lower()

class _Profile:
    name: str
    image_dimensions: Tuple[int, int]
    work_traversal_depth: int
    extensions: List[str]
    execution_arguments: List[str]
    default_application: Optional[str]

class XMLReadOnlyProfile(_Profile):
    @staticmethod
    def from_file(path: str) -> XMLReadOnlyProfile:
        return XMLReadOnlyProfile(ElementTree.parse(path).getroot())

    @staticmethod
    def from_string(string: str) -> XMLReadOnlyProfile:
        return XMLReadOnlyProfile(ElementTree.fromstring(string))

    @staticmethod
    def from_etree(tree: ElementTree.ElementTree) -> XMLReadOnlyProfile:
        return XMLReadOnlyProfile(tree.getroot())


    def __init__(self, root: ElementTree.Element):
        if root.tag != 'UserDefaults':
            raise MissingTagError(None, 'UserDefaults')

        self.name = str(get_element(root, 'ProfileName').text)
        self.image_dimensions = (
            int(str(get_element(root, 'ImageHeight').text)),
            int(str(get_element(root, 'ImageWidth').text))
        )

        self.work_traversal_depth = int(str(get_element(root, 'WorkTraversalDepth').text))
        # self.ignored_prefixes = [e.text for e in get_element(root, 'IgnoredPrefixes')]
        self.extensions = [str(e.text) for e in get_element(root, 'Extensions')]
        # self.combine_subdirectories = get_element(root, 'SubdirectoryAction').text == 'COMBINE'
        # self.do_ignore_prefixes = get_element(root, 'IgnoredPrefixAction').text == 'IGNORE'
        execution_argument = str(get_element(root, 'ExecutionArguments').text)
        self.execution_arguments = re.sub(r'\b(?={)|(?<=})\b', ' ', execution_argument).split()

        default_application_element = get_element(root, 'DefaultApplication')
        if get_element(default_application_element, 'Type').text == 'Custom':
            self.default_application = get_element(default_application_element, 'Path').text
        else:
            self.default_application = None

        # self.root_paths = {}
        # for p in get_element(root, 'RootPaths'):
        #     self.root_paths[get_element(p, 'Category').text] = get_element(p, 'Path').text

class ReadOnlyProfile(_Profile):
    @staticmethod
    def from_file(path: str) -> ReadOnlyProfile:
        with open(path, encoding='utf-8') as infile:
            return ReadOnlyProfile(json.load(infile))


    def __init__(self, json: dict):
        ''' we'll just throw keyerror for invalid data '''
        self.name = json['Name']

        self.image_dimensions = (
            json.get('ImageHeight', 240),
            json.get('ImageWidth', 240)
        )

        self.extensions = json.get('FileExtensions', ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif'])

        # these properties are deprecated, but they're here to make ComicsManager work
        self.work_traversal_depth = 2
        self.default_application = None
        self.execution_arguments = []


default_appdata = r'C:\Users\lanxia\AppData\Local\Packages\7417df09-6e90-4c8e-94f9-82950aaef08b_jh3a8zm8ky434\LocalState'

class ReadOnlyManager:
    profile: _Profile
    database_path: str
    thumbnail_folder: str

    def __init__(self, profile_path: str, database_path: str,
                 thumbnail_folder: str):
        self.profile = ReadOnlyProfile.from_file(profile_path)
        self.thumbnail_folder = thumbnail_folder
        self.database_path = database_path

    @staticmethod
    def try_open(profile_name: str, appdata: str = default_appdata) -> ReadOnlyManager:
        profile_path = os.path.join(appdata, 'Profiles', f'{profile_name}.profile.json')
        db_path = os.path.join(appdata, 'Databases', f'{profile_name}.library.db')
        thumbnails_dir = os.path.join(appdata, 'Thumbnails')

        if not (os.path.isfile(profile_path) and os.path.isfile(db_path) and os.path.isdir(thumbnails_dir)):
            raise ValueError(f'Could not find profile {profile_name} in {appdata}')

        return ReadOnlyManager(profile_path, db_path, thumbnails_dir)


    SearchResult = Tuple[List[Comic], Dict[str, int], Dict[str, int], Dict[str, int]]

    def text_search(
        self,
        search_string: str,
        override_categories: Optional[List[str]] = None,
        override_authors: Optional[List[str]] = None,
        override_tags: Optional[List[str]] = None,
        override_playlists: Optional[List[str]] = None
    ) -> SearchResult:
        ''' The overrides serve the comics_db webapp for now. Perhaps we should figure out a better way. '''
        search, categories, authors, tags, playlists, loved = compile_search(search_string)

        search_string = search[0] if len(search) > 0 else None
        loved_only = (loved is True)

        categories = override_categories or categories
        authors = override_authors or authors
        tags = override_tags or tags
        playlists = override_playlists or playlists

        return self.search_comics(search_string, categories, authors, tags, playlists, loved_only)

    def search_comics(
        self,
        search_string: Optional[str] = None,
        categories: List[str] = [],
        authors: List[str] = [],
        tags: List[str] = [],
        playlists: List[str] = [],
        loved_only=False
    ) -> SearchResult:
        ''' returns a 4-tuple ([comics], {category_name: id}, {author_name: id}, {tag_name: id})
            Note that authors, tags, categories need to be exact matches, but search string doesn't.'''
        with tcsql.connect(self.database_path) as manager:
            query = f"""
                SELECT
                    comics.path,
                    comics.unique_identifier,
                    comics.title,
                    comics.author,
                    comics.category,
                    comics.display_title,
                    comics.loved,
                    comics.date_added,
                    group_concat(comic_tags.tag),
                    group_concat(playlist_items.playlist)
                FROM
                    comics
                LEFT OUTER JOIN
                    comic_tags ON comic_tags.comic = comics.unique_identifier
                LEFT OUTER JOIN
                    playlist_items ON playlist_items.comic = comics.unique_identifier
                WHERE
            {     f'comics.category IN {tcsql.question_marks(len(categories))} AND ' if categories != [] else '' }
            {     f'comics.author IN {tcsql.question_marks(len(authors))} AND ' if authors != [] else '' }
            {     f'comic_tags.tag IN {tcsql.question_marks(len(tags))} AND ' if tags != [] else ''}
            {     f'playlist_items.playlist IN {tcsql.question_marks(len(playlists))} AND ' if playlists != [] else ''}
            {      'loved = 1 AND ' if loved_only else '' }
            {   '''(comics.display_title COLLATE UTF8_GENERAL_CI LIKE ? OR
                       (comics.display_title IS NULL AND comics.title COLLATE UTF8_GENERAL_CI LIKE ?) OR
                        comics.author COLLATE UTF8_GENERAL_CI LIKE ? OR
                        comic_tags.tag = ?) AND '''
                    if search_string is not None else '' }
                    active = 1
                GROUP BY comics.unique_identifier
            """

            arguments = categories + authors + tags + playlists
            if search_string is not None:
                arguments += [f'%{search_string}%'] * 3 + [search_string]

            result = manager.execute(query, arguments)

            comics = []
            category_dict: Counter = Counter()
            author_dict: Counter = Counter()
            tag_dict: Counter = Counter()

            for *data, tag_string, playlist_string in result:
                assert len(data) == 8
                tags = sorted(set(tag_string.split(','))) if tag_string is not None else []
                playlists = sorted(set(playlist_string.split(','))) if playlist_string is not None else []
                comic = Comic(data, tags, playlists)

                comics.append(comic)
                category_dict[comic.category] += 1
                author_dict[comic.author] += 1
                for tag in comic.tags:
                    tag_dict[tag] += 1

            return comics, category_dict, author_dict, tag_dict

    def get_comic(self, unique_identifier: str) -> Optional[Comic]:
        with tcsql.connect(self.database_path) as manager:
            result = manager.execute(
                f'''SELECT path, unique_identifier, title, author, category,
                           display_title, loved, date_added
                    FROM comics WHERE unique_identifier = ?''',
                [unique_identifier]
            )

            if len(result) == 0:
                return None

            return Comic(result[0], self._get_tags(unique_identifier), self._get_playlists(unique_identifier))

    def _get_tags(self, unique_identifier: str) -> List[str]:
        with tcsql.connect(self.database_path) as manager:
            tags = manager.execute(
                f'SELECT tag FROM comic_tags WHERE comic = ?',
                [unique_identifier]
            )

            return [t[0] for t in tags]

    def _get_playlists(self, unique_identifier: str) -> List[str]:
        with tcsql.connect(self.database_path) as manager:
            tags = manager.execute(
                'SELECT playlist FROM playlist_items WHERE comic = ?',
                [unique_identifier]
            )

            return [t[0] for t in tags]

    def get_all_tags(self) -> Dict[str, int]:
        with tcsql.connect(self.database_path) as manager:
            return dict(manager.execute(
                'SELECT tag, COUNT(*) FROM comic_tags GROUP BY tag'
            ))

    def get_all_authors(self) -> Dict[str, int]:
        with tcsql.connect(self.database_path) as manager:
            return dict(manager.execute(
                'SELECT author, COUNT(*) FROM comics GROUP BY author'
            ))

    def get_all_categories(self) -> Dict[str, int]:
        with tcsql.connect(self.database_path) as manager:
            return dict(manager.execute(
                'SELECT category, COUNT(*) FROM comics GROUP BY category'
            ))

    def get_subworks(self, comic: Comic) -> List[Tuple[str, str]]:
        ''' Returns a list of tuples (subwork_path, first_file_path) '''
        subworks = []
        for path in tc.utils.listdir(comic.path):
            files = self.get_files_from_folder(os.path.join(comic.path, path))
            if (len(files)) > 0:
                subworks.append((path, files[0]))
        return subworks

    def get_files(self, comic: Comic) -> List[str]:
        return self.get_files_from_folder(comic.path)

    def get_files_from_folder(self, path: str) -> List[str]:
        return list(tc.subfiles.get_elements(
            path,
            depth=self.profile.work_traversal_depth,
            filter=lambda f: f.endswith(tuple(self.profile.extensions)),
            sort=natsorted
        ))

    def open(self, comic: Comic):
        files = self.get_files(comic)
        if self.profile.default_application is None:
            os.startfile(files[0])
        else:
            args = [self.profile.default_application]
            for arg in self.profile.execution_arguments:
                if arg == '{first}':
                    args.append(files[0])
                elif arg == '{all}':
                    args.extend(files)
                elif arg == '{folder}':
                    args.append(comic.path)
                elif arg == '{firstname}':
                    args.append(os.path.basename(files[0]))
                elif arg == '{allname}':
                    args.extend([os.path.basename(x) for x in files])
                else:
                    args.append(arg)
            subprocess.Popen(args)


class MissingTagError(Exception):
    def __init__(self, element: Optional[ElementTree.Element], expected_tag: str):
        message = f"expected element '{expected_tag}' not found"

        if element is None:
            message = f'Incorrect root: {message}'
        else:
            message = f"Missing element in element '{element.tag}': {message}"

        super().__init__(message)


def get_element(element: ElementTree.Element, name: str) -> ElementTree.Element:
    r = element.find(name)
    if r is None:
        raise MissingTagError(element, name)
    return r
