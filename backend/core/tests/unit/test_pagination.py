import pytest

from core.services.pagination import paginar, paginar_desde_queryset


class DummyQuerySet:
    def __init__(self, data):
        self.data = list(data)
        self.slices = []

    def count(self):
        return len(self.data)

    def __getitem__(self, item):
        self.slices.append(item)
        return self.data[item]


def test_paginar_basic_window():
    qs = DummyQuerySet(range(10))
    result = paginar(qs, page=2, page_size=3)
    assert result['items'] == [3, 4, 5]
    assert result['total'] == 10
    assert result['page'] == 2
    assert result['page_size'] == 3
    assert result['total_pages'] == 4


def test_paginar_handles_invalid_inputs_and_max_page_size():
    qs = DummyQuerySet(range(5))
    result = paginar(qs, page='x', page_size=999)
    assert result['items'] == list(range(5))
    assert result['page'] == 1
    assert result['page_size'] == 100
    assert result['total_pages'] == 1


def test_paginar_from_queryset_empty_and_bounded_page():
    qs = DummyQuerySet([])
    result = paginar_desde_queryset(qs, page=5, page_size='bad')
    assert result['items'] == []
    assert result['page'] == 1
    assert result['page_size'] == 20
    assert result['total_pages'] == 1
