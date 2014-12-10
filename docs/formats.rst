Data formats
************

Inventory
=========

Exchanges with temporal distributions
-------------------------------------

Both inventory dataset inputs and biosphere flows (i.e. exchanges) can be distributed in time, and can occur both before and after the inventory dataset itself. This distribution is specified in the new key ``temporal distribution``:

.. code-block:: python

    "exchanges": [
        {
            "amount": 1000,
            "temporal distribution": [
                (0,  500),
                (7.5, 250),
                (15, 250)
            ]
        }
    ]

Each tuple in ``temporal distribution`` has the format ``(relative temporal difference (in years), amount)``. Temporal differences can be positive or negative, and give the difference between when the inventory dataset and the exchange occur.

The default unit of time is years, but fractional years are allowed.

The sum of all amounts in the temporal distribution should equal the total exchange amount. This is **not** checked automatically, but can be checked using the ``utils.check_temporal_distribution_totals`` function.

Impact Assessment
=================

Dynamic impact assessment methods
---------------------------------

Brightway2-temporalis supports three types of characterization factors for use in dynamic LCA:

#. Static characterization factors, i.e. those which do not change over time.
#. Dynamic characterization factors, i.e. those whose value changes over time, but whose impact still occurs at the time of emission.
#. Extended dynamic characterization factors, i.e. CFs whose impact is allocated over time using something like atmospheric decay rates.

Impact assessment methods must be defined as a ``DynamicIAMethod``, not a normal LCIA Method, even if all CFs are static (see :ref:`dynamic-lcia`).

The data format for dynamic IA methods is:

.. code-block:: python

    {
        ("biosphere", "flow"): number or python_function_as_string
    }

.. note:: This data format is different than the normal method data; it is a dictionary, not a list.

Static characterization factors
-------------------------------

Static characterization factors can be defined as usual, e.g.

.. code-block:: python


    {
        ("biosphere", "n2o"): 296,
        ("biosphere", "chloroform"): 30,
    }

Dynamic characterization factors
--------------------------------

Dynamic characterization factors are realized with pure python functions, e.g.

.. code-block:: python

    def silly_random_cf(datetime):
        import random
        return random.random()

    def increasing_co2_importance(datetime):
        """Importance of CO2 doubles every twenty years from 2010"""
        CF = 1.
        dt = arrow.get(datetime)
        cutoff = arrow.get(2010, 1, 1)
        return max(1, 2 ** ((dt - cutoff).days / 365.24 / 20) * CF)

    def days_since_best_movie_evar(datetime):
        """http://en.wikipedia.org/wiki/Transformers:_Dark_of_the_Moon"""
        return (arrow.get(dt) - arrow.get(2011, 6, 23)).days

However, there are some things to bear in mind with dynamic characterization functions:

* Dynamic characterization functions must take a datetime as the single input, and return a single numeric characterization factor.
* * You will need to import whatever you need in the body of the function; don't assume anything other than the standard library is in the current namespace.
* Functions have to be defined in a slightly funny way. They should not be defined by name. Instead, they should have a name of "``%s``" that can be generated automatically and substituted by the temporalis library, i.e. ``def %s(datetime)``. This dynamicity is needed to avoid name conflicts.
* These functions must be stored as **unicode strings**, not actual python code:

.. code-block:: python

    {
        ("omg", "wtf-bbq"): """def %s(datetime):
    return (arrow.get(datetime) - arrow.get(2011, 6, 23)).days"""
    }

This can be a bit confusing. See `the examples <https://bitbucket.org/cmutel/brightway2-temporalis/src/default/bw2temporalis/examples/ia.py?at=default#cl-76>`__ for a real-world implementation.

These function strings will be executed using ``exec``. Don't accept dynamic characterization function code from strange men in dark alleyways.

Extended dynamic characterization factors
-----------------------------------------

Extended dynamic characterization functions don't return a single number, but rather a list of characterization factors allocated over time.

Returned CFs must be `named tuples <https://docs.python.org/2/library/collections.html#collections.namedtuple>`_ with field names ``dt``, and ``amount``.

.. code-block:: python

    def spread_over_a_week(datetime):
        """Spread impact over a week"""
        from datetime import timedelta
        import collections
        return_tuple = collections.namedtuple('return_tuple', ['dt', 'amount'])
        return [return_tuple(datetime + timedelta(days=x), 1 / 7.) for x in range(7)]

See also `functions in the examples <https://bitbucket.org/cmutel/brightway2-temporalis/src/default/bw2temporalis/examples/ia.py?at=default#cl-99>`__.

Aside from the return format, they are identical to normal dynamic characterization factors, and have the same restrictions.
