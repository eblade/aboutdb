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
