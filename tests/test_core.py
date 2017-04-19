#!/usr/bin/env python3

import pytest
from aboutdb import AboutDB
from .fixtures import *  # NOQA


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
