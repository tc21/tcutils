# todo: comparison (equality)
#       operations (addition)
#       str and repr
#       save to file
import csv


class Csv:
    def __init__(self, header: list, rows: list = []):
        # validation:
        if len(header) != len(set(header)):
            raise ValueError('duplicate name in header')
        if any(len(row) != len(header) for row in rows):
            # some implementations can bypass this by filling empty strings
            raise ValueError('not all rows have same length as header')

        self.header = header.copy()
        self.rows = rows.copy()

    def add(self, row):
        l = list(row)
        if len(self.header) != len(l):
            raise ValueError('row does not have same length as header')
        self.rows.append(row)

    def get_column(self, name):
        return self.__getattr__(name)

    def __str__(self):
        s = ','.join(self.header)
        s += '\n' + '-' * len(s)
        for row in self.rows:
            s += '\n' + ','.join(row)

    def __getattr__(self, name):
        try:
            index = self.header.index(name)
        except ValueError:
            return object.__getattr__(self, name)

        return [row[index] for row in self.rows]

    def __setattr__(self, name, value):
        try:
            index = self.header.index(name)
        except ValueError:
            object.__setattr__(self, name, value)
            return

        try:
            if len(self.rows) != len(value):
                raise ValueError(f'incorrect number of rows (expected {len(self.rows)}, {len(value)} given)')
        except TypeError:
            raise TypeError(f"expected iterable, '{type(value)}' given")

        for i, v in enumerate(value):
            self.rows[i][index] = v

    def __delattr__(self, name):
        try:
            index = self.header.index(name)
        except ValueError:
            object.__delattr__(self, name)
            return

        del self.header[index]
        for row in self.rows:
            del self.row[index]

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, key):
        if type(key) == int:
            return CsvItem(self.header, self.rows[key])
        if type(key) == slice:
            return Csv(self.header, self.rows[key])

        raise TypeError('indice must be integers or slices')

    def __setitem__(self, key, value):
        if type(key) == int:
            self.rows[key] = list(value)
            return

        if type(key) == slice:
            inserted = []
            for row in value:
                inserted.append(list(row))

            self.rows[slice] = inserted
            return

        raise TypeError('indice must be integers or slices')

    def __delitem__(self, key):
        if type(key) in (int, slice):
            del self.rows[key]
            return

        raise TypeError('indice must be integers or slices')

    def __iter__(self):
        for row in self.rows:
            yield CsvItem(self.header, row)


class CsvItem:
    def __init__(self, header: list, row: list):
        if len(header) != len(set(header)):
            raise ValueError('duplicate name in header')
        if len(row) != len(header):
            raise ValueError('row does not have same length as header')

        self.header = header
        self.row = row

        for i, h in enumerate(header):
            object.__setattr__(self, h, row[i])

    def __str__(self):
        s = []
        for i, h in enumerate(self.header):
            s.append(f'{h}: {self.row[i]}')
        return '<' + ', '.join(s) + '>'

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)

        try:
            index = self.header.index(name)
        except ValueError:
            return

        self.row[index] = value

    def __delattr__(self, name):
        object.__delattr__(self, name)

        try:
            index = self.header.index(name)
        except ValueError:
            return

        del self.header[index]
        del self.row[index]

    def __len__(self):
        return len(self.row)

    def __getitem__(self, key):
        return self.row[key]

    def __setitem__(self, key, value):
        self.row[key] = value

    def __delitem__(self, key):
        del self.row[key]

    def __iter__(self):
        return iter(self.row)


def read(file, dialect='excel', **fmtparams):
    reader = csv.reader(file, dialect, **fmtparams)
    header, *rows = list(reader)
    return Csv(header, rows)
