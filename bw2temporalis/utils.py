import arrow


def get_maximum_value(func, lower=arrow.get(2000, 1, 1), upper=arrow.get(2100, 1, 1)):
    """Get maximum CF values by calculating each week for 100 years. Poor computers."""
    return max([func(x) for x in arrow.Arrow.range('week', lower, upper)])
