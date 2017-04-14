#!/usr/bin/env python3

import pytest
import logging
from aboutdb import AboutDB


# Logging
FORMAT = '%(asctime)s [%(threadName)s] %(filename)s +%(levelno)s ' + \
         '%(funcName)s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


@pytest.fixture(scope='function')
def db():
    db = AboutDB()
    yield db


@pytest.fixture(scope='function')
def a(db):
    db.store('A', 'a', 1)
    return db.get('A')


@pytest.fixture(scope='function')
def b(db):
    db.store('B', 'a', 2)
    return db.get('B')


def test_init(db):
    assert db is not None


def test_save(db, a):
    assert '_id' in a.keys()
    assert a['_id'] is not None
    assert a['_id'] == 'A'


def test_get(db, a):
    new_id = a['_id']
    assert new_id is not None
    a = db.get(new_id)
    assert a is not None
    assert a['a'] == 1
    assert '_id' in a.keys()
    assert a['_id'] == new_id
    # assert '_rev' in o.keys()


def test_get_2(db, a, b):
    id_a = a['_id']
    assert id_a is not None
    id_b = b['_id']
    assert id_b is not None
    oa = db.get(id_a)
    assert oa is not None
    assert oa['a'] == 1
    assert '_id' in oa.keys()
    assert oa['_id'] == id_a
    # assert '_rev' in oa.keys()
    ob = db.get(id_b)
    assert ob is not None
    assert ob['a'] == 2
    assert '_id' in ob.keys()
    assert ob['_id'] == id_b
    # assert '_rev' in ob.keys()


def test_get_non_existing(db):
    with pytest.raises(KeyError):
        db.get('does-not-exist')


def test_delete(db, a):
    db.delete(a['_id'])
    with pytest.raises(KeyError):
        db.get(a['_id'])


def test_update(db: AboutDB, a):
    db.store(a['_id'], 'a', 2)
    db.store(a['_id'], 'b', 3)
    a = db.get(a['_id'])
    assert(a['a'] == 2)
    assert(a['b'] == 3)


def test_view_just_save(db):
    db.define('b_by_a', lambda o: (o['a'], o['b']))
    db.save({'a': 2, 'b': 22})
    db.save({'a': 3, 'b': 33})
    db.save({'a': 1, 'b': 11})
    r = db.view('b_by_a')
    r = list(r)
    assert len(r) == 3
    assert r[0] == {'id': 2, 'key': 1, 'value': 11}
    assert r[1] == {'id': 0, 'key': 2, 'value': 22}
    assert r[2] == {'id': 1, 'key': 3, 'value': 33}


def test_view_save_and_update_value(db):
    db.define('b_by_a', lambda o: (o['a'], o['b']))
    db.save({'a': 2, 'b': 22})
    db.save({'a': 3, 'b': 33})
    o1 = db.save({'a': 1, 'b': 11})
    o1['b'] = 1111
    db.save(o1)
    r = db.view('b_by_a')
    r = list(r)
    assert len(r) == 3
    assert r[0] == {'id': 2, 'key': 1, 'value': 1111}
    assert r[1] == {'id': 0, 'key': 2, 'value': 22}
    assert r[2] == {'id': 1, 'key': 3, 'value': 33}


def test_view_save_and_delete(db):
    db.define('b_by_a', lambda o: (o['a'], o['b']))
    o2 = db.save({'a': 2, 'b': 22})
    db.save({'a': 3, 'b': 33})
    db.save({'a': 1, 'b': 11})
    db.delete(o2['_id'])
    r = db.view('b_by_a')
    r = list(r)
    assert len(r) == 2
    assert r[0] == {'id': 2, 'key': 1, 'value': 11}
    assert r[1] == {'id': 1, 'key': 3, 'value': 33}


def test_view_kickstart(db):
    db.save({'a': 2, 'b': 22})
    db.save({'a': 3, 'b': 33})
    db.save({'a': 1, 'b': 11})
    db.define('b_by_a', lambda o: (o['a'], o['b']))
    r = db.view('b_by_a')
    r = list(r)
    assert len(r) == 3
    assert r[0] == {'id': 2, 'key': 1, 'value': 11}
    assert r[1] == {'id': 0, 'key': 2, 'value': 22}
    assert r[2] == {'id': 1, 'key': 3, 'value': 33}


def test_view_by_key(db):
    db.save({'a': 2, 'b': 22})
    db.save({'a': 3, 'b': 33})
    db.save({'a': 1, 'b': 11})
    db.define('b_by_a', lambda o: (o['a'], o['b']))
    r = list(db.view('b_by_a', key=2))
    assert len(r) == 1
    assert r[0] == {'id': 0, 'key': 2, 'value': 22}


def test_view_by_key_string(db):
    db.save({'a': '2', 'b': 22})
    db.save({'a': '3', 'b': 33})
    db.save({'a': '1', 'b': 11})
    db.define('b_by_a', lambda o: (o['a'], o['b']))
    r = list(db.view('b_by_a', key='2'))
    assert len(r) == 1
    assert r[0] == {'id': 0, 'key': '2', 'value': 22}


def test_view_by_key_two_values_same_key_before(db):
    db.define('b_by_a', lambda o: (o['a'], o['b']))
    db.save({'a': 2, 'b': 22})
    db.save({'a': 3, 'b': 33})
    db.save({'a': 1, 'b': 11})
    db.save({'a': 2, 'b': 44})
    r = list(db.view('b_by_a', key=2))
    assert len(r) == 2
    assert r[0] == {'id': 0, 'key': 2, 'value': 22}
    assert r[1] == {'id': 3, 'key': 2, 'value': 44}


def test_view_by_key_two_values_same_key_after(db):
    db.save({'a': 2, 'b': 22})
    db.save({'a': 3, 'b': 33})
    db.save({'a': 1, 'b': 11})
    db.save({'a': 2, 'b': 44})
    db.define('b_by_a', lambda o: (o['a'], o['b']))
    r = list(db.view('b_by_a', key=2))
    assert len(r) == 2
    assert r[0] == {'id': 0, 'key': 2, 'value': 22}
    assert r[1] == {'id': 3, 'key': 2, 'value': 44}


def test_view_by_startkey(db):
    db.save({'a': 2, 'b': 22})
    db.save({'a': 3, 'b': 33})
    db.save({'a': 1, 'b': 11})
    db.define('b_by_a', lambda o: (o['a'], o['b']))
    r = list(db.view('b_by_a', startkey=2))
    assert len(r) == 2
    assert r[0] == {'id': 0, 'key': 2, 'value': 22}
    assert r[1] == {'id': 1, 'key': 3, 'value': 33}


def test_view_by_startkey_after(db):
    db.save({'a': 3, 'b': 33})
    db.save({'a': 4, 'b': 44})
    db.save({'a': 1, 'b': 11})
    db.define('b_by_a', lambda o: (o['a'], o['b']))
    r = list(db.view('b_by_a', startkey=2))
    assert len(r) == 2
    assert r[0] == {'id': 0, 'key': 3, 'value': 33}
    assert r[1] == {'id': 1, 'key': 4, 'value': 44}


def test_view_by_endkey(db):
    db.save({'a': 2, 'b': 22})
    db.save({'a': 3, 'b': 33})
    db.save({'a': 1, 'b': 11})
    db.define('b_by_a', lambda o: (o['a'], o['b']))
    r = list(db.view('b_by_a', endkey=2))
    assert len(r) == 2
    assert r[0] == {'id': 2, 'key': 1, 'value': 11}
    assert r[1] == {'id': 0, 'key': 2, 'value': 22}


def test_view_by_endkey_after(db):
    db.save({'a': 2, 'b': 22})
    db.save({'a': 4, 'b': 44})
    db.save({'a': 1, 'b': 11})
    db.define('b_by_a', lambda o: (o['a'], o['b']))
    r = list(db.view('b_by_a', endkey=3))
    assert len(r) == 2
    assert r[0] == {'id': 2, 'key': 1, 'value': 11}
    assert r[1] == {'id': 0, 'key': 2, 'value': 22}


def test_add_with_custom_keys(db):
    db['a'] = {'a': 2, 'b': 22}
    db[1] = {'a': 3, 'b': 33}
    db[('a', 1)] = {'a': 1, 'b': 11}
    assert db['a'] == {'_id': 'a', '_rev': 0, 'a': 2, 'b': 22}
    assert db[1] == {'_id': 1, '_rev': 0, 'a': 3, 'b': 33}
    assert db[('a', 1)] == {'_id': ['a', 1], '_rev': 0, 'a': 1, 'b': 11}


def test_add_with_custom_keys_and_set_next_id(db):
    db[10] = {'a': 3, 'b': 33}
    db.set_next_id(20)
    db[None] = {'a': 1, 'b': 11}
    assert db[10] == {'_id': 10, '_rev': 0, 'a': 3, 'b': 33}
    assert db[20] == {'_id': 20, '_rev': 0, 'a': 1, 'b': 11}


def test_include_docs(db):
    db.define('by_id', lambda o: (o['_id'], 1))
    db[1] = {1: 11}
    db[2] = {2: 12}
    db[5] = {5: 15}
    db[7] = {7: 17}
    r = list(db.view('by_id', include_docs=True))
    assert r[0] == {'id': 1, 'key': 1, 'value': 1,
                    'doc': {'_id': 1, '_rev': 0, '1': 11}}
    assert r[1] == {'id': 2, 'key': 2, 'value': 1,
                    'doc': {'_id': 2, '_rev': 0, '2': 12}}
    assert r[2] == {'id': 5, 'key': 5, 'value': 1,
                    'doc': {'_id': 5, '_rev': 0, '5': 15}}
    assert r[3] == {'id': 7, 'key': 7, 'value': 1,
                    'doc': {'_id': 7, '_rev': 0, '7': 17}}


def test_yielding_mapping_function(db):
    def yielder(o):
        yield (o['a'], 1), o['b']
        yield (o['a'], 2), o['b'] * 2
        yield (o['a'], 3), o['b'] * 3

    db.save({'a': 2, 'b': 22})
    db.save({'a': 3, 'b': 33})
    db.save({'a': 1, 'b': 11})
    db.define('b_by_a', yielder)
    r = db.view('b_by_a')
    r = list(r)
    assert len(r) == 9
    assert r[0] == {'id': 2, 'key': (1, 1), 'value': 11}
    assert r[1] == {'id': 2, 'key': (1, 2), 'value': 22}
    assert r[2] == {'id': 2, 'key': (1, 3), 'value': 33}
    assert r[3] == {'id': 0, 'key': (2, 1), 'value': 22}
    assert r[4] == {'id': 0, 'key': (2, 2), 'value': 44}
    assert r[5] == {'id': 0, 'key': (2, 3), 'value': 66}
    assert r[6] == {'id': 1, 'key': (3, 1), 'value': 33}
    assert r[7] == {'id': 1, 'key': (3, 2), 'value': 66}
    assert r[8] == {'id': 1, 'key': (3, 3), 'value': 99}


def test_reduce_by_group(db):
    def sum_per(field, values):
        result = {}
        for value in values:
            v = value.get(field)
            if v in result:
                result[v] += 1
            else:
                result[v] = 1
        return result

    db.define('test',
              lambda o: (o['category'], {'state': o['state']}),
              lambda keys, values, rereduce: sum_per('state', values))
    db.save({'category': 'a', 'state': 'new'})
    db.save({'category': 'b', 'state': 'new'})
    db.save({'category': 'a', 'state': 'old'})
    db.save({'category': 'b', 'state': 'new'})
    db.save({'category': 'a', 'state': 'old'})
    db.save({'category': 'a', 'state': 'new'})
    db.save({'category': 'c', 'state': 'new'})
    db.save({'category': 'c', 'state': 'old'})
    db.save({'category': 'a', 'state': 'new'})
    db.save({'category': 'a', 'state': 'new'})
    r = list(db.view('test', group=True))
    print(r)
    assert r[0] == {'key': 'a', 'value': {'new': 4, 'old': 2}}
    assert r[1] == {'key': 'b', 'value': {'new': 2}}
    assert r[2] == {'key': 'c', 'value': {'new': 1, 'old': 1}}


def test_skip(db):
    db.define('by_id', lambda o: (o['_id'], 1))
    db[1] = {1: 11}
    db[2] = {2: 12}
    db[5] = {5: 15}
    db[7] = {7: 17}
    r = list(db.view('by_id', include_docs=True, skip=2))
    assert r[0] == {'id': 5, 'key': 5, 'value': 1,
                    'doc': {'_id': 5, '_rev': 0, '5': 15}}
    assert r[1] == {'id': 7, 'key': 7, 'value': 1,
                    'doc': {'_id': 7, '_rev': 0, '7': 17}}


def test_limit(db):
    db.define('by_id', lambda o: (o['_id'], 1))
    db[1] = {1: 11}
    db[2] = {2: 12}
    db[5] = {5: 15}
    db[7] = {7: 17}
    r = list(db.view('by_id', include_docs=True, limit=2))
    assert r[0] == {'id': 1, 'key': 1, 'value': 1,
                    'doc': {'_id': 1, '_rev': 0, '1': 11}}
    assert r[1] == {'id': 2, 'key': 2, 'value': 1,
                    'doc': {'_id': 2, '_rev': 0, '2': 12}}


def test_skip_and_limit(db):
    db.define('by_id', lambda o: (o['_id'], 1))
    db[1] = {1: 11}
    db[2] = {2: 12}
    db[5] = {5: 15}
    db[7] = {7: 17}
    r = list(db.view('by_id', include_docs=True, skip=1, limit=2))
    assert r[0] == {'id': 2, 'key': 2, 'value': 1,
                    'doc': {'_id': 2, '_rev': 0, '2': 12}}
    assert r[1] == {'id': 5, 'key': 5, 'value': 1,
                    'doc': {'_id': 5, '_rev': 0, '5': 15}}
