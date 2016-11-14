# coding: utf-8
import pickle

DEFAULT_DB = 'sieben.db'


def save(obj, filename=DEFAULT_DB):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)


def load(filename=DEFAULT_DB):
    with open(filename, 'rb') as f:
        return pickle.load(f)
