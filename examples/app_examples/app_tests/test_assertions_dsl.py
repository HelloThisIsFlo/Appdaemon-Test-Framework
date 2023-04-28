from functools import partial
from types import SimpleNamespace

## Custom Assertions DSL #################
def assert_that(expected):
    class Wrapper:
        def equals(self, actual):
            assert expected == actual
    return Wrapper()


def assert_that_partial(expected):
    def equals(expected, actual):
        assert expected == actual
    return partial(equals, expected)


def assert_that_sn(expected):
    assert_that = SimpleNamespace()

    def equals(actual):
        assert expected == actual
    assert_that.equals = equals
    return assert_that

##########################################


def test_assertions_dsl():
    assert_that(44).equals(44)
    assert_that_partial(44)(44)
    assert_that_sn(44).equals(44)
    # the_function
