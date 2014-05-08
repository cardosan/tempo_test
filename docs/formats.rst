Data formats
============

Inventory datasets with absolute dates
--------------------------------------

Inventory datasets by default can occur at any time. To force a dataset to occur at a certain date, use the key ``absolute date``:

.. code-block:: python

    ("example", "foo"): {
        "name": "a long while ago",
        "absolute date": "1970",
    },

``absolute date`` takes any string that can be parsed by `arrow <crsmithdev.com/arrow/>`_ into a datetime. The following are all acceptable:

.. code-block:: python

    In [1]: import arrow

    In [2]: arrow.get("1970-1-1")
    Out[2]: <Arrow [1970-01-01T00:32:50+00:00]>

    In [3]: arrow.get("1970-01-01")
    Out[3]: <Arrow [1970-01-01T00:00:00+00:00]>

    In [4]: arrow.get("1970-01-01T12:00")
    Out[4]: <Arrow [1970-01-01T12:00:00+00:00]>

When in doubt, test your string in the python shell.

Exchanges with temporal distributions
-------------------------------------

Both inventory dataset inputs and biosphere flows (i.e. exchanges) can be distributed in time, and can occur both before and after the inventory dataset itself. This distribution is specified in the new key ``temporal distribution``:

.. code-block:: python

    "exchanges": [
        {
            "amount": 1e4,
            "temporal distribution": [
                (0, 100),
                (10, 50),
                (20, 20)
            ]
        }
    ]

Each tuple in ``temporal distribution`` has the format ``(relative temporal difference (in years), amount)``. Temporal differences can be positive or negative, and give the difference between when the inventory dataset and the exchange occur.

The sum of all amounts in the temporal distribution should equal the total exchange amount, though this is **not** checked automatically.

Dynamic characterization factors
--------------------------------

Instead of some weird formula language, dynamic characterization factors are realized with pure python functions, e.g.

.. code-block:: python

    def declining_co2_importance(dt):
        """Importance of CO2 halves every twenty years from 2010"""
        CF = 1.
        dt = arrow.get(dt)
        cutoff = arrow.get(2010, 1, 1)
        if dt < cutoff:
            return 1. * CF
        else:
            return 0.5 ** ((dt - cutoff).days / 365.24 / 20) * CF

Dynamic impact assessment methods
---------------------------------

The data format for dynamic IA methods is simply:

.. code-block:: python

    {
        ("biosphere", "flow"): python_function
    }

Each ``python_function`` must take a datetime as its first argument, and should require only one argument.

.. note:: Because of the way that `pickling works <https://docs.python.org/2/library/pickle.html#relationship-to-other-python-modules>`_, python functions cannot be defined in the shell or in an ipython notebook, but must be in a module (i.e. a file) that can be imported.

Static characterization factors
-------------------------------

Requiring a function makes static characterization factors a little more difficult. However, we can use ``functools.partial`` to `curry <http://en.wikipedia.org/wiki/Currying>`_ a dummy function to always return the same value:

.. code-block:: python

    from functools import partial

    STATIC_CFS = {
        ("biosphere", "n2o"): 296,
        ("biosphere", "chloroform"): 30,
    }

    def static_cf(datetime, cf):
        return cf

    boring_cfs = {
        key: partial(static_cf, cf=value)
        for key, value in STATIC_CFS.iteritems()
    }

.. code-block:: python

    In [1]: boring_cfs[("biosphere", "n2o")](1)
    Out[1]: 296

    In [2]: boring_cfs[("biosphere", "n2o")](1000)
    Out[2]: 296

    In [3]: boring_cfs[("biosphere", "n2o")](-1e6)
    Out[3]: 296
