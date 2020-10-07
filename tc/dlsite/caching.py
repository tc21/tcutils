import os.path
import sqlite3
from . import webinterface

from typing import Dict, Any, Optional, List, Tuple

_cache_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'infocache.db')
_main_table = 'work_info'
_tag_table = 'tags'
_sample_images_table = 'sample_images'
_voice_table = 'voice_actors'
_code = 'code'
_maker = 'maker'
_title = 'title'
_releasedate = 'release_date'
_imagelink = 'image_link'
_agerestriction = 'age_restriction'
_description = 'description'
_taglist = 'tags'
_tag = 'tag'
_sample_image_url = 'image_url'
_sampleimages = 'sample_images'
_voice = 'voice'


_query_primary_key = _code
_query_fields: List[str] = [
    _title, _maker, _imagelink, _releasedate, _agerestriction, _description
]
_query_columns: List[str] = [_query_primary_key] + _query_fields

_auxiliary_info: List[Tuple[str, str, str]] = [
    # local_key_name, database_table_name, database_field_name
    (_taglist, _tag_table, _tag),
    (_sampleimages, _sample_images_table, _sample_image_url),
    (_voice, _voice_table, _voice),
]

def cached_get_info(code: str, reset_cached=False) -> Dict[str, Any]:
    result = fetch_info(code)
    if reset_cached or result is None:
        info = webinterface.get_info(code)
        if info:
            update = result is not None
            write_info_to_cache(info, update)
        return info
    else:
        info = dict()

        for key, value in zip(_query_columns, result):
            info[key] = value

        for local_key, table_name, field_name in _auxiliary_info:
            info[local_key] = fetch_auxiliary_info(code, table_name, field_name)

        return info


def fetch_auxiliary_info(code: str, table_name: str, field_name: str) -> List[Any]:
    database = sqlite3.connect(_cache_file)
    c = database.cursor()
    query = f'SELECT {field_name} FROM {table_name} WHERE {_code} = ?'
    c.execute(query, [code])
    return [i[0] for i in c.fetchall()]


def fetch_info(code: str) -> Optional[List[Any]]:
    database = sqlite3.connect(_cache_file)
    c = database.cursor()
    query = f'SELECT {", ".join(_query_columns)} FROM {_main_table} WHERE {_code} = ?'
    c.execute(query, [code])
    return c.fetchone()


def write_info_to_cache(info: Dict[str, Any], update=False):
    database = sqlite3.connect(_cache_file)
    c = database.cursor()

    key = info[_query_primary_key]

    update_columns = {}

    for field_name in _query_fields:
        if field_name in info:
            update_columns[field_name] = info[field_name]

    if update:
        set_fields = (f'{key} = ?' for key in update_columns)
        query = f'''UPDATE {_main_table}
                       SET {', '.join(set_fields)}
                     WHERE {_query_primary_key} = ?'''
        args = list(update_columns.values()) + [key]
        c.execute(query, args)
    else:
        columns = [_query_primary_key] + list(update_columns.keys())
        query = f'''INSERT INTO {_main_table}
                        ({', '.join(columns)})
                    VALUES ({', '.join('?' for _ in columns)})'''
        args = [key] + list(update_columns.values())
        c.execute(query, args)

        for local_key, table_name, field_name in _auxiliary_info:
            if local_key in info:
                write_auxiliary_info_to_cache(
                    c, info[_code], info[local_key], table_name, field_name)

    database.commit()
    database.close()


def write_auxiliary_info_to_cache(
    cursor: sqlite3.Cursor,
    code: str,
    info_list: List[Any],
    table_name: str,
    field_name: str
):
    query = f'INSERT INTO {table_name} ({_code}, {field_name}) VALUES (?, ?)'
    for item in info_list:
        cursor.execute(query, [code, item])
