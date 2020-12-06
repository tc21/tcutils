''' The subfiles module provides the ability to iterate through all
    files or folders in a directory and its subdirectories. '''
from .webinterface import get_info as _get_info, find_code, get_search_suggestions
from .caching import cached_get_info as _cached_get_info
from .organizer import organize

from typing import Union

def get_info(rj_number: Union[int, str], caching=True, update=False, offline=False):
    '''
    ```
    {
        code: <copy of argument rj_number>
        title: str
        maker: str
        image_link: str
        release_date: str = '%Y年%m月%d日'
        age_restriction: int in (0, 15, 18)
        tags: List[str]
        description: str
    }
    ```

    note: only the non-cached version returns a full list of images

    TODO: implement caching of full sample image list
    '''
    rj_code = _formalize(rj_number)

    if caching:
        return _cached_get_info(rj_code, update, offline)

    if offline:
        raise ValueError('cannot run in offline mode if caching is disabled')

    return _get_info(rj_code)


def info(rj_number: Union[int, str], caching=True):
    from tc.utils import print_dict
    print_dict(get_info(_formalize(rj_number), caching))


def _formalize(rj_number: Union[int, str]) -> str:
    rj_str = str(rj_number)
    if len(rj_str) < 6:
        rj_str = f'{rj_str:0>6}'

    if rj_str.lower().startswith('rj'):
        rj_str = rj_str[2:]

    if len(rj_str) != 6 or not all(c.isdigit() for c in rj_str):
        raise ValueError('expected a 6-digit code!')

    return rj_str
