Gotchas
=======

Temporal distributions sums are not checked
-------------------------------------------

The sum of all amounts in a ``temporal distribution`` is not check to sum to the total ``amount``.

Processes with specific temporal distributions could be incorrectly excluded
----------------------------------------------------------------------------

The initial graph traversal could exclude some nodes which have important temporal dynamics, but whose total demanded amount was small. For example, the following exchange would be excluded as having no impact:

.. code-block:: python

    {
        "amount": 0,
        "temporal distribution": [
            (0, -1e6),
            (10, 1e6)
        ]
    }

The best way around this software feature/bug is to create two separate sub-processes, one with the positive amounts and the other with the negative.

Dynamic CF functions must be pickleable
---------------------------------------

Each function defined in a dynamic LCIA method must be pickleable, i.e. it must be importable from a python module (file). The easiest way to meet this requirement is to create a python file in the same path that you are working, and to define your dynamic CF functions there.
