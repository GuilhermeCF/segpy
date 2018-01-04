from collections import namedtuple, deque
from itertools import accumulate, starmap, product

import sys
from hypothesis import assume
from hypothesis.strategies import integers, just, fixed_dictionaries, lists, text, composite, sampled_from
from segpy.util import batched

PRINTABLE_ASCII_RANGE = (32, 127)
PRINTABLE_ASCII_ALPHABET = ''.join(map(chr, range(*PRINTABLE_ASCII_RANGE)))


def multiline_ascii_encodable_text(min_num_lines, max_num_lines):
    """A Hypothesis strategy to produce a multiline Unicode string.

    Args:
        min_num_lines: The minimum number of lines in the produced strings.
        max_num_lines: The maximum number of lines in the produced strings.

    Returns:
        A strategy for generating Unicode strings containing only newlines
        and characters which are encodable as printable 7-bit ASCII characters.
    """

    return integers(min_num_lines, max_num_lines) \
           .flatmap(lambda n: lists(integers(*PRINTABLE_ASCII_RANGE), min_size=n, max_size=n))  \
           .map(lambda xs: '\n'.join(bytes(x).decode('ascii') for x in xs))


def spaced_ranges(min_num_ranges, max_num_ranges, min_interval, max_interval):
    """A Hypothesis strategy to produce separated, non-overlapping ranges.

    Args:
        min_num_ranges: The minimum number of ranges to produce. TODO: Correct?
        max_num_ranges: The maximum number of ranges to produce.
        min_interval: The minimum interval used for the lengths of the alternating ranges and spaces.
        max_interval: The maximum interval used for the lengths of the alternating ranges and spaces.
    """
    return integers(min_num_ranges, max_num_ranges)               \
           .map(lambda n: 2*n)                                                       \
           .flatmap(lambda n: lists(integers(min_interval, max_interval), min_size=n, max_size=n))  \
           .map(list).map(lambda lst: list(accumulate(lst)))                         \
           .map(lambda lst: list(batched(lst, 2)))                                   \
           .map(lambda pairs: list(starmap(range, pairs)))


def header(header_class, **kwargs):
    """Create a strategy for producing headers of a specific class.

    Args:
        header_class: The type of header to be produced. This class will be
            introspected to determine suitable strategies for each named
            field.

        **kwargs: Any supplied keyword arguments can be used to fix the value
            of particular header fields.
    """

    field_strategies = {}
    for field_name in header_class.ordered_field_names():
        if field_name in kwargs:
            field_strategy = just(kwargs.pop(field_name))
        else:
            value_type = getattr(header_class, field_name).value_type
            if hasattr(value_type, 'VALUES'):
                field_strategy = sampled_from(sorted(value_type.VALUES))
            else:
                field_strategy = integers(value_type.MINIMUM, value_type.MAXIMUM)
        field_strategies[field_name] = field_strategy

    if len(kwargs) > 0:
        raise TypeError("Unrecognised binary header field names {} for {}".format(
            ', '.join(kwargs.keys()),
            header_class.__name__))

    return fixed_dictionaries(field_strategies) \
           .map(lambda kw: header_class(**kw))


def fixed_dict_of_printable_strings(keys, **overrides):
    """Create a strategy for producing a dictionary of strings with specific keys.

    Args:
        keys: A list of keys which the strategy will associate with arbitrary strings.

        **overrides: Specific keywords arguments can be supplied to associate certain keys
            with specific values.  The values supplied via kwargs override any supplied
            through the keys argument.
    """
    d = {key: text(alphabet=PRINTABLE_ASCII_ALPHABET) for key in keys}
    for keyword in overrides:
        d[keyword] = just(overrides[keyword])
    return fixed_dictionaries(d)


@composite
def ranges(draw,
           min_start_value=None, max_start_value=None,
           min_size=None, max_size=None,
           min_step_value=None, max_step_value=None):
    if min_size is None:
        min_size = 0
    if min_size < 0:
        raise ValueError("Value of {} as min_size for ranges() is negative.".format(min_size))
    if (max_size is not None) and (max_size < min_size):
        raise ValueError("Value of {} as max_size for ranges() is less than min_size={}".format(max_size, min_size))
    start = draw(integers(min_value=min_start_value, max_value=max_start_value))
    length = draw(integers(min_value=min_size, max_value=max_size))
    step = draw(integers(min_value=min_step_value, max_value=max_step_value))
    assume(step != 0)
    stop = start + step * length
    return range(start, stop, step)


Items2D = namedtuple('Items2D', ['i_range', 'j_range', 'items'])


@composite
def items2d(draw, i_size, j_size):
    i_range = draw(ranges(min_size=1, max_size=i_size, min_step_value=1))
    j_range = draw(ranges(min_size=1, max_size=j_size, min_step_value=1))
    size = len(i_range) * len(j_range)
    values = draw(lists(integers(), min_size=size, max_size=size))
    items = {(i, j): v for (i, j), v in zip(product(i_range, j_range), values)}
    return Items2D(i_range, j_range, items)

SEQUENCE_TYPES = [
    list, tuple
]

if sys.version_info > (3, 5):
    SEQUENCE_TYPES.append(deque)

@composite
def sequences(draw, elements=None, min_size=None, max_size=None, average_size=None, unique_by=None, unique=False):
    """A Hypthesis strategy to produce arbitrary sequences.

    Currently produces list, tuple or deque objects.
    """
    seq_type = draw(sampled_from(SEQUENCE_TYPES))  # Work ranges and string and bytes in here
    elements = integers() if elements is None else elements
    items = draw(lists(elements=elements, min_size=min_size, max_size=max_size,
                       average_size=average_size, unique_by=unique_by, unique=unique))
    return seq_type(items)
