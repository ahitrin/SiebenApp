# coding: utf-8
import sqlite3


def test_initial_migration():
    conn = sqlite3.connect(':memory:')
    cur = conn.cursor()
    cur.execute('create table migrations (version integer)')
    cur.execute('insert into migrations values (0)')
    conn.commit()
    cur.execute('select version from migrations')
    version = cur.fetchone()[0]
    assert version == 0
