#!/usr/bin/env python3

import pytest
from aboutdb import AboutDB
from pprint import pprint as pp
from .fixtures import *


def test_init(db):
    assert db is not None


def test_set(db, a):
    assert ID in a.keys()
    assert a[ID] is not None
    assert a[ID] == 'A'


def test_set_string(db, a):
    db.set(a[ID], 's', 'this is a string')
    a = db.get(a[ID])
    assert 's' in a.keys()
    assert a['s'] is not None
    assert a['s'] == 'this is a string'


def test_get(db, a):
    new_id = a[ID]
    assert new_id is not None
    a = db.get(new_id)
    assert a is not None
    assert a['a'] == 1
    assert ID in a.keys()
    assert a[ID] == new_id
    # assert '_rev' in o.keys()


def test_get_2(db, a, b):
    id_a = a[ID]
    assert id_a is not None
    id_b = b[ID]
    assert id_b is not None
    oa = db.get(id_a)
    assert oa is not None
    assert oa['a'] == 1
    assert ID in oa.keys()
    assert oa[ID] == id_a
    # assert '_rev' in oa.keys()
    ob = db.get(id_b)
    assert ob is not None
    assert ob['a'] == 2
    assert ID in ob.keys()
    assert ob[ID] == id_b
    # assert '_rev' in ob.keys()


def test_get_non_existing(db):
    with pytest.raises(KeyError):
        db.get('does-not-exist')


def test_delete(db, a):
    db.delete(a[ID])
    with pytest.raises(KeyError):
        db.get(a[ID])


def test_update(db: AboutDB, a):
    db.set(a[ID], 'a', 2)
    db.set(a[ID], 'b', 3)
    a = db.get(a[ID])
    assert a['a'] == 2
    assert a['b'] == 3


def test_unset(db: AboutDB, a: dict):
    db.unset(a[ID], 'a')
    updated_a = db.get(a[ID])
    assert 'a' not in updated_a.keys()


def test_link(db: AboutDB, a, b):
    db.link(a[ID], 'b', b[ID])
    a = db.get(a[ID])
    assert a['b'][ID] == b[ID]
    assert a['b']['a'] == b['a']


def test_unlink(db: AboutDB, a, b):
    db.link(a[ID], 'b', b[ID])
    db.unset(a[ID], 'b')
    a = db.get(a[ID])
    assert 'b' not in a.keys()
