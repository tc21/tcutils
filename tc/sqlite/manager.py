import sqlite3

from typing import Tuple, List, Any, Dict, Iterable, Sequence


# you must be able to trust your table and column names! sanitization on
# table and column names is work-in-progress


class SQLiteManager:
    conn: sqlite3.Connection
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._cursor = conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def rollback(self, *args, **kwargs):
        self.conn.rollback(*args, **kwargs)

    def execute(self, sql: str, parameters: Iterable = []) -> List[Any]:
        self._cursor.execute(sql, parameters)
        return self._cursor.fetchall()

    def executemany(self, sql: str, seq_of_parameters: Iterable[Iterable]) -> int:
        self._cursor.executemany(sql, seq_of_parameters)
        return self._cursor.lastrowid

    def executescript(self, sql_script) -> int:
        self._cursor.executescript(sql_script)
        return self._cursor.lastrowid

    def select(self, table: str, rows: Iterable[str], **kwargs) -> List[Any]:
        select_clause = ', '.join(rows)
        kw_clauses, kw_arguments = SQLiteManager._parse_kwargs(kwargs)

        query = f'SELECT {select_clause} FROM {table}' + kw_clauses

        self._cursor.execute(query, kw_arguments)
        return self._cursor.fetchall()

    def update(self, table: str, set_: Dict[str, Any], **kwargs) -> int:
        kwargs['set'] = set_
        kw_clauses, kw_arguments = SQLiteManager._parse_kwargs(kwargs)

        query = f'UPDATE {table}' + kw_clauses
        arguments = [table] + kw_arguments

        self._cursor.execute(query, arguments)
        return self._cursor.rowcount

    def insert(self, table: str, rows: Sequence[str], values: Iterable[Any]) -> int:
        row_names = ', '.join(rows)
        question_marks = ', '.join(['?'] * len(rows))

        query = f'INSERT INTO {table} ({row_names}) VALUES ({question_marks})'

        self._cursor.execute(query, values)
        return self._cursor.lastrowid

    @staticmethod
    def _parse_kwargs(kwargs: dict) -> Tuple[str, List[str]]:
        arguments = []
        query = ''

        if 'where' in kwargs:
            q, a = SQLiteManager._build_clause('WHERE', kwargs['where'], 'AND')
            arguments.extend(a)
            query += ' ' + q

        if 'set' in kwargs:
            q, a = SQLiteManager._build_clause('SET', kwargs['set'])
            arguments.extend(a)
            query += ' ' + q

        return query, arguments

    @staticmethod
    def _build_clause(name: str, args: Dict[str, Any], sep=',') -> Tuple[str, List[str]]:
        query = f'{name} ' + f' {sep} '.join([f'{key} = ?' for key in args])
        arguments = list(args.values())

        return query, arguments


def connect(*args, **kwargs) -> SQLiteManager:
    connection = sqlite3.connect(*args, **kwargs)
    return SQLiteManager(connection)


def question_marks(count: int, parenthesized=True):
    return '(' + ', '.join(['?'] * count) + ')'
