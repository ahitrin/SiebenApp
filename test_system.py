# coding: utf-8
from mikado import Goals
from system import save, load
from tempfile import NamedTemporaryFile


def test_save_and_load():
    file_name = NamedTemporaryFile().name
    goals = Goals('Root')
    goals.add('Top')
    goals.add('Middle')
    goals.link(3, 2)
    goals.add('Closed')
    goals.close(4)
    save(goals, file_name)
    new_goals = load(file_name)
    assert goals.all(keys='open,name,edge') == new_goals.all(keys='open,name,edge')
