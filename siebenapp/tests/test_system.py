# coding: utf-8
import pytest

from siebenapp.system import split_long


@pytest.mark.parametrize('source,result', [
    ('short', 'short'),
    ('10: Example multi-word Sieben label', '10: Example multi-word\nSieben label'),
    ('123: Example very-very long multi-word Sieben label', '123: Example very-very\nlong multi-word Sieben\nlabel'),
    ('43: Manual-placed\nnewlines\nare ignored', '43: Manual-placed\nnewlines\nare\nignored'),
])
def test_split_long_labels(source, result):
    assert split_long(source) == result
