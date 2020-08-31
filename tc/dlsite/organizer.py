''' This file defines functions used to organize an existing folder. '''
import tc.subfiles
from .webinterface import get_info as uncached_get_info
from .caching import cached_get_info
import os
import re
from typing import Union, Optional, List, Callable, Dict, Any
import tc.utils

def rj_folder(pathname: str) -> bool:
    ''' Given a pathname, returns `True` if the path contains a root file named
        [RJ123456], which indicates the folder was organized by this organizer.
    '''
    return (
        os.path.isdir(pathname) and
        re.search(r'[Rr][Jj]\d{6}', os.path.basename(pathname)) is not None
    )


def get_number(pathname: str) -> str:
    ''' Given a pathname, attempts to find the 6-digit rj-number from its basename '''
    basename = os.path.basename(pathname)
    start = basename.lower().find('rj')
    return basename[start + 2:start + 8]

# main logic

def organize(root_dir: str=os.path.curdir,
             caching: bool=True,
             info_file: Optional[str]='dlsite.txt',
             download_artwork: Union[str, bool]='auto'):
    '''
    download_artwork: if 'auto', downloads artwork if:
        there are no artwork equivalent to False if using cached info, and True if otherwise
    note: there should be a 3 x 3 of configurations:
        retrieve artwork list: always, never, automatically if not cached
        download and save artwork files: always, never, automatically if no images exist
        currently, True/False/'auto' does both at the same time
    '''
    if isinstance(download_artwork, str) and download_artwork != 'auto':
        raise ValueError('download_artwork must be a bool or \'auto\'')

    if caching and (download_artwork is True):
        raise ValueError('caching must be True when download_artwork is True')

    organized_dir = os.path.join(root_dir, 'organized')
    deleted_dir = os.path.join(root_dir, 'deleted')
    unsuccessful_dir = os.path.join(root_dir, 'unsuccessful')

    if not os.path.exists(organized_dir):
        os.mkdir(organized_dir)

    if not os.path.exists(deleted_dir):
        os.mkdir(deleted_dir)

    if not os.path.exists(unsuccessful_dir):
        os.mkdir(unsuccessful_dir)

    for element in tc.subfiles.get_elements(root_dir, depth=range(1), filter=rj_folder):
        final_dir = tc.utils.traverse_to_contents(element)
        rj_number = get_number(element)

        if caching:
            work_info = cached_get_info(rj_number)
        else:
            work_info = uncached_get_info(rj_number)

        if not work_info:
            work_dir = os.path.join(unsuccessful_dir, f'RJ{rj_number}')
            os.rename(final_dir, work_dir)
            print(f'could not find information for RJ{rj_number}')
            continue  # could not get work info, ignore and skip to next one

        maker_dir = os.path.join(organized_dir, normalize(work_info['maker']))
        work_title = normalize(work_info['title'])
        work_dir = os.path.join(maker_dir, work_title)

        # ensure an identifier (and empty file) exists
        open(os.path.join(final_dir, f'[RJ{rj_number}]'), 'a').close()

        if info_file is not None:
            info_filename = tc.utils.alternative_filename(os.path.join(final_dir, 'dlsite.txt'))
            with open(info_filename, 'w') as f:
                f.write(work_info['description'])

        if 'sample_images' in work_info:
            sample_images: List[str] = work_info['sample_images']

            if download_artwork == 'auto':
                download_artwork = not any(tc.subfiles.get_elements(final_dir, filter=tc.utils.is_image))

            if download_artwork:
                for sample_image in sample_images:
                    resulting_image = download_file(sample_image, folder=final_dir)
                    print(f'downloaded {resulting_image}')

        if not os.path.isdir(maker_dir):
            os.mkdir(maker_dir)
        tc.utils.move(final_dir, name=work_dir)

        if element != final_dir:
            tc.utils.move(element, folder=deleted_dir)


def download_file(url: str, *,
                  folder: Optional[str] = None,
                  name: Optional[str] = None,
                  auto_rename=True) -> str:
    ''' Note: identical signature to tc.utils.move
        since this function is designed to be moved elsewhere, imports only
        required by this function appear here, not at the beginning of this source file. '''
    import requests
    import urllib.parse
    import posixpath

    if name is None:
        name = posixpath.basename(urllib.parse.urlparse(url).path)

    if folder is None:
        if os.path.isabs(name):
            target_name = name
        else:
            target_name = os.path.join(os.path.curdir, name)
    else:
        if os.path.dirname(name) != '':
            raise ValueError('name cannot contain path separators when folder is provided')
        target_name = os.path.join(folder, name)

    target_name = tc.utils.alternative_filename(target_name)

    response = requests.get(url)

    with open(target_name, 'wb') as out_file:
        out_file.write(response.content)

    return target_name


def normalize(s: str) -> str:
    ''' Supposed to remove and replace all illegal path characters.
        Currently just added on a case-by-case basis.
        Very much in TODO territory. For a more basic but
        complete implementation see the regex in line 70. '''
    base = s.replace('*', ' ').replace('"', '\'').replace(':', '-').replace('/', '-').strip()

    return tc.utils.sanitize_filename(base)
