#!/usr/bin/env python3


from pprint import pprint as pp

import logging
import re
import sqlite3


class colors:
    reset = '\033[0m'
    bold = '\033[01m'
    disable = '\033[02m'
    underline = '\033[04m'
    reverse = '\033[07m'
    strikethrough = '\033[09m'
    invisible = '\033[08m'

    class fg:
        black = '\033[30m'
        red = '\033[31m'
        green = '\033[32m'
        orange = '\033[33m'
        blue = '\033[34m'
        purple = '\033[35m'
        cyan = '\033[36m'
        lightgrey = '\033[37m'
        darkgrey = '\033[90m'
        lightred = '\033[91m'
        lightgreen = '\033[92m'
        yellow = '\033[93m'
        lightblue = '\033[94m'
        pink = '\033[95m'
        lightcyan = '\033[96m'

    class bg:
        black = '\033[40m'
        red = '\033[41m'
        green = '\033[42m'
        orange = '\033[43m'
        blue = '\033[44m'
        purple = '\033[45m'
        cyan = '\033[46m'
        lightgrey = '\033[47m'


class Item:
    def __init__(self, identity, field, value):
        self.identity = identity
        self.field = field
        self.value = value

    def as_bytes(self):
        result = b''
        if type(self.value) is str:
            result = self.value.encode('utf-8')
        elif type(self.value) is int:
            result = self.value.to_bytes(4, "big")
        logging.debug("Converted '%s' to %s", self.value, result)
        return result

    def from_bytes(type, data):
        if type is str:
            return data.decode('utf-8')
        elif type is int:
            return int.from_bytes(data, "big")

    def __repr__(self):
        return "<%s::%s = '%s'>" % (self.identity, self.field, self.value)


class List:
    def __init__(self, identity, field, value):
        self.identity = identity
        self.field = field
        self.value = value

    def __repr__(self):
        return "<%s::%s = %s>" % (self.identity, self.field, self.value)


class Link:
    def __init__(self, identity, field, target_identity):
        self.identity = identity
        self.field = field
        self.target_identity = target_identity

    def __repr__(self):
        return "<%s::%s -> '%s'>" % (self.identity, self.field, self.target_identity)


class Delete:
    def __init__(self, identity):
        self.identity = identity

    def __repr__(self):
        return "<Delete %s>" % (self.identity)


class Pointer:
    def __init__(self, chunk: int, type: type, position: int, size: int):
        self.chunk = chunk
        self.type = type
        self.position = position
        self.size = size

    def __repr__(self):
        return "<Pnt [%s:%d] %s:%d>" % (self.type.__name__, self.size, self.chunk, self.position)


class Register:
    def __init__(self):
        self._objects = {}

    def store(self, object_id: str, field: str, pointer: Pointer):
        if object_id in self._objects.keys():
            self._objects[object_id][field] = pointer
        else:
            self._objects[object_id] = {field: pointer}

    def get(self, identity):
        return self._objects[identity]

    def delete(self, identity):
        del self._objects[identity]


class Index:
    clean = re.compile('[^A-Z_]')

    def __init__(self, schema, name, field=None, fn=None, field_type=str):
        self.schema = schema
        self.name = name
        self.field = field or name
        self.fn = fn
        self.field_type = field_type

    @property
    def table_name(self):
        if self.schema is None:
            return Index.clean.sub('', self.field.upper())
        else:
            return Index.clean.sub('', '%s_%s' % (self.schema.upper(), self.name.upper()))

    @property
    def value_type(self):
        return {
            str: "TEXT",
            int: "INTEGER",
        }[self.field_type]

    def build(self, conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE %s (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                OBJECT_ID VARCHAR(64) NOT NULL,
                VALUE %s
            )
            """ % (self.table_name, self.value_type))
        conn.commit()
        logging.debug("Initialized index %s", self.table_name)
        return self

    def handles(self, schema: str, item: Item):
        if self.schema is None:
            return item.field == self.field and schema is None
        else:
            return item.field == self.field and schema == self.schema

    def handles_field(self, field: str):
        return self.schema is None and field == self.field

    def handles_schema_and_field(self, schema: str, field: str):
        return self.schema == schema and field == self.field

    def run(self, conn: sqlite3.Connection, item: Item):
        logging.debug('Index %s', repr(item))

        if type(item) is Item:
            values = [item.value]
        else:
            values = item.value

        if callable(self.fn):
            for value in values:
                conn.execute("""
                    INSERT INTO %s (OBJECT_ID, VALUE)
                    VALUES (?, ?)
                    """ % self.table_name, (item.identity, self.field_type(self.fn(value))))
        else:
            for value in values:
                conn.execute("""
                    INSERT INTO %s (OBJECT_ID, VALUE)
                    VALUES (?, ?)
                    """ % self.table_name, (item.identity, self.field_type(value)))

        conn.commit()

    def lookup(self, conn: sqlite3.Connection, value: str):
        cur = conn.execute("SELECT OBJECT_ID FROM %s WHERE VALUE = ?"
                           % self.table_name, self.field_type(value))
        return (x[0] for x in cur)

    def get_value_by_id(self, conn, identity):
        return (conn.execute("""
            SELECT VALUE FROM %s WHERE OBJECT_ID = ?
            """ % self.table_name, (identity,)).fetchone() or (None,))[0]


class Chunk:
    def __init__(self, identity, size=2 << 16):
        self.identity = identity
        self.size = size
        self._data = bytearray(size)
        self._position = 0

    def store(self, data: bytes):
        assert type(data) is bytes
        size = len(data)
        if self._position + size > self.size:
            raise ValueError("Not enough space left in chunk")
        self._data[self._position:self._position+size] = data
        start = self._position
        self._position += size
        return (start, size)

    def get(self, position, size):
        return self._data[position:position+size]


class AboutDB:
    def __init__(self):
        self._chunk = [Chunk(0)]
        self._index = []
        self._index_db_conn = sqlite3.connect(':memory:')
        self._register = Register()
        self.index(None, '*schema')

    def index(self, schema, name, field=None, fn=None):
        self._index.append(
            Index(schema, name, field=field, fn=fn)
            .build(self._index_db_conn))

    def store(self, identity, field, value):
        if type(value) is list:
            item = List(identity, field, value)
        else:
            item = Item(identity, field, value)

        logging.debug("Store %s", repr(item))
        chunk = self._chunk[0]
        position, size = chunk.store(item.as_bytes())
        self._register.store(identity, field, Pointer(0, type(value), position, size))
        # self._run_indexing_on(item)

    def link(self, identity, field, target_identity):
        self._data.append(Link(identity, field, target_identity))

    def get(self, identity):
        logging.debug("Get %s", identity)
        result = {}
        obj = self._register.get(identity)
        pp(obj)
        for field, pointer in obj.items():
            if hasattr(pointer, 'identity'):
                result[field] = self.get(pointer.identity)
            else:
                result[field] = self._unpoint(pointer)

        if not result:
            raise KeyError

        return dict(result, _id=identity)

    def delete(self, identity):
        logging.debug("Delete %s", identity)
        self._register.delete(identity)

    def lookup(self, schema, field, value):
        logging.debug("Lookup %s::%s = %s", schema, field, value)
        for index in self._index:
            if index.handles_schema_and_field(schema, field):
                return index.lookup(self._index_db_conn, value)

    def get_field_by_id(self, identity, field):
        logging.debug("Get %s::%s", identity, field)
        for index in self._index:
            if index.handles_field(field):
                return index.get_value_by_id(self._index_db_conn, identity)

        pointer = self._objects[identity][field]
        return self._unpoint(pointer)

    def _unpoint(self, pointer):
        logging.debug("Unpoint %s", pointer)
        chunk = self._chunk[pointer.chunk]
        data = chunk.get(pointer.position, pointer.size)
        logging.debug(data)
        return Item.from_bytes(pointer.type, data)

    def _run_indexing_on(self, item: Item):
        schema = self.get_field_by_id(item.identity, '*schema')
        for index in self._index:
            if index.handles(schema, item):
                index.run(self._index_db_conn, item)


if __name__ == '__main__':
    FORMAT = colors.disable + '%(asctime)s [%(threadName)s] %(filename)s +%(levelno)s ' + \
             '%(funcName)s %(levelname)s' + colors.reset + '\n  %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    db = AboutDB()

    db.index('Entry', 'taken_ts')
    db.index('Entry', 'date', field='taken_ts', fn=lambda x: x[:10])
    db.index('Entry', 'tags')

    db.store('A', '*schema', 'Entry')
    db.store('A', 'title', 'my title for A')
    db.store('A', 'taken_ts', '2017-04-08 10:00:00')
    db.store('F1', '*schema', 'Variant')
    db.store('F1', 'variant', 'original')
    db.store('F1', 'mimetype', 'image/jpeg')
    db.store('F1', 'width', '1024')
    db.store('F1', 'height', '768')
    db.store('F1', 'filename', '/home/johan/test.jpg')
    db.link('A', 'file', 'F1')
    db.store('A', 'tags', ['a', 'b'])

    db.store('B', '*schema', 'Entry')
    db.store('B', 'title', 'my title for B')
    db.store('B', 'taken_ts', '2017-04-08 10:00:00')
    db.store('B', 'tags', ['b', 'c'])

    pp(db._data)
    pp(db.get('A'))

    pp(db._index_db_conn.execute("SELECT * FROM SCHEMA").fetchall())
    pp(db._index_db_conn.execute("SELECT * FROM ENTRY_TAKEN_TS").fetchall())
    pp(db._index_db_conn.execute("SELECT * FROM ENTRY_DATE").fetchall())
    pp(db._index_db_conn.execute("SELECT * FROM ENTRY_TAGS").fetchall())

    pp(list(db.lookup('Entry', 'tags', 'a')))
    pp(list(db.lookup('Entry', 'tags', 'b')))
