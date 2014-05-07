Dynamic LCA through temporal graph traversal: brightway2-temporalis
*******************************************************************

Basic strategy
==============

The basic strategy is to create another LCIA method, which has the worst case values for each dynamic CF. We do this to screen out processes deep in the supply chain which we calculate could not be important even with the highest CF values applied.

We then apply the `graph traversal algorithm <https://brightway2-calc.readthedocs.org/en/latest/graph_traversal.html>`_ using the worst case IA method and ignoring temporal data to get a list of inventory datasets and edges that should be further investigated.

We then re-traverse this smaller supply chain graph, locating inventory datasets and biosphere flows in time. We create a timeline of flows to and from the environment. We can also apply dynamic CFs to get a picture of environmental impact through time.

Unit of time
============

The default unit of time is **years**, but fractional years are allowed.

Input data formats
==================

Inventory datasets with absolute dates
--------------------------------------

Inventory datasets by default can occur at any time. To force a dataset to occur at a certain date, use the key ``absolute date``:

.. code-block:: python

    ("example", "foo"): {
        "name": "a long while ago",
        "absolute date": "1970",
    },

``absolute date`` takes a string that can be parsed by `arrow <crsmithdev.com/arrow/>`_ into a datetime. The following are acceptable:

.. code-block:: python

    In [1]: import arrow

    In [2]: arrow.get("1970-1-1")
    Out[2]: <Arrow [1970-01-01T00:32:50+00:00]>

    In [3]: arrow.get("1970-01-01")
    Out[3]: <Arrow [1970-01-01T00:00:00+00:00]>

    In [4]: arrow.get("1970-01-01T12:00")
    Out[4]: <Arrow [1970-01-01T12:00:00+00:00]>

When in doubt, test your string in the python shell.

Inventory datasets relative inputs
----------------------------------

Both inventory dataset inputs and biosphere flows (i.e. exchanges) can be distributed in time, and can occur both before and after the inventory dataset itself. Exchanges can have a new key, ``temporal distribution``,

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

Each tuple in ``temporal distribution`` has the format ``(relative temporal difference (in years), amount)``. The sum of all amounts in the temporal distribution should equal the total exchange amount, though this is **not** checked automatically.

Dynamic characterization factors
--------------------------------

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

Gotchas
=======

* The sum of all amounts in a ``temporal distribution`` is not check to sum to the total ``amount``.
* The initial graph traversal could exclude some nodes which have important temporal dynamics, but whose total demanded amount was small. For example, the following exchange would be excluded as having no impact:

.. code-block:: python

    {
        "amount": 0,
        "temporal distribution": [
            (0, -1e6),
            (10, 1e6)
        ]
    }

The best way around this software feature/bug is to create two separate sub-processes, one with the positive amounts and the other with the negative.


Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

