from hypothesis import given, assume
from hypothesis.strategies import (data, dictionaries, just,
                                   integers, tuples)
from segpy.catalog import CatalogBuilder


class TestCatalogBuilder:

    @given(dictionaries(integers(), integers()))
    def test_arbitrary_mapping(self, mapping):
        builder = CatalogBuilder(mapping)
        catalog = builder.create()
        shared_items = set(mapping.items()) & set(catalog.items())
        assert len(shared_items) == len(mapping)

    @given(dictionaries(integers(), just(42)))
    def test_constant_mapping(self, mapping):
        builder = CatalogBuilder(mapping)
        catalog = builder.create()
        shared_items = set(mapping.items()) & set(catalog.items())
        assert len(shared_items) == len(mapping)

    @given(start=integers(),
           num=integers(0, 1000),
           step=integers(-1000, 1000),
           value=integers())
    def test_regular_constant_mapping(self, start, num, step, value):
        assume(step != 0)
        mapping = {key: value for key in range(
            start, start + num * step, step)}
        builder = CatalogBuilder(mapping)
        catalog = builder.create()
        shared_items = set(mapping.items()) & set(catalog.items())
        assert len(shared_items) == len(mapping)

    @given(start=integers(),
           num=integers(0, 1000),
           step=integers(-1000, 1000),
           values=data())
    def test_regular_mapping(self, start, num, step, values):
        assume(step != 0)
        mapping = {key: values.draw(integers())
                   for key
                   in range(start, start + num * step, step)}
        builder = CatalogBuilder(mapping)
        catalog = builder.create()
        shared_items = set(mapping.items()) & set(catalog.items())
        assert len(shared_items) == len(mapping)

    @given(num=integers(0, 1000),
           key_start=integers(),
           key_step=integers(-1000, 1000),
           value_start=integers(),
           value_step=integers(-1000, 1000))
    def test_linear_regular_mapping(self, num, key_start, key_step, value_start, value_step):
        assume(key_step != 0)
        assume(value_step != 0)
        mapping = {key: value for key, value in zip(range(key_start, key_start + num * key_step, key_step),
                                                    range(value_start, value_start + num * value_step, value_step))}
        builder = CatalogBuilder(mapping)
        catalog = builder.create()
        shared_items = set(mapping.items()) & set(catalog.items())
        assert len(shared_items) == len(mapping)

    @given(dictionaries(tuples(integers(), integers()), integers()))
    def test_arbitrary_mapping_2d(self, mapping):
        builder = CatalogBuilder(mapping)
        catalog = builder.create()
        shared_items = set(mapping.items()) & set(catalog.items())
        assert len(shared_items) == len(mapping)

    @given(i_start=integers(0, 10),
           i_num=integers(1, 10),
           i_step=just(1),
           j_start=integers(0, 10),
           j_num=integers(1, 10),
           j_step=just(1),
           c=integers(1, 10))
    def test_linear_regular_mapping_2d(self, i_start, i_num, i_step, j_start, j_num, j_step, c):
        assume(i_step != 0)
        assume(j_step != 0)

        def v(i, j):
            return (i - i_start) * ((j_start + j_num * j_step) - j_start) + (j - j_start) + c

        mapping = {(i, j): v(i, j)
                   for i in range(i_start, i_start + i_num * i_step, i_step)
                   for j in range(j_start, j_start + j_num * j_step, j_step)}

        builder = CatalogBuilder(mapping)
        catalog = builder.create()
        shared_items = set(mapping.items()) & set(catalog.items())
        assert len(shared_items) == len(mapping)
