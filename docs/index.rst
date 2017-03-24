Dynamic LCA through temporal graph traversal: brightway2-temporalis
*******************************************************************

A library for the `Brightway2 LCA calculation framework <http://brightwaylca.org/>`_ that allows for a specific kind of dynamic life cycle assessments.

Brightway2-temporalis is open source. `Source code is available on bitbucket <https://bitbucket.org/cmutel/brightway2-temporalis>`_, and `documentation is available on read the docs <http://example.com>`_.

Brightway2-temporalis has the following abilities:

* Exchanges (technosphere inputs, and biosphere outputs) can be offset in time.
* Individual exchanges can be split into multiple time steps, creating a temporal distribution for each exchange.
* Inventory datasets can be given either relative or absolute dates and times.
* Characterization factors can vary as a function of time.
* Characterization factors can spread impact over time.

However, Brightway2-temporalis has the following limitations:

* Inventory datasets cannot change their inputs as a function of time. This limitation is necessary for the graph traversal to converge.
* Exchanges must be linear, as in normal matrix-based LCA.

See the example ipython notebook (`nbviewer <http://nbviewer.ipython.org/url/brightwaylca.org/examples/brightway2-temporalis.ipynb>`_, `html <https://brightwaylca.org/examples/brightway2-temporalis.html>`_) for a real usage example.

Table of contents
=================

.. toctree::
   :maxdepth: 2

   strategy
   comparison
   formats
   gotchas
   technical
