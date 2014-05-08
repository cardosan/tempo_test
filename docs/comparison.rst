Comparison with ESPA
====================

Didier Beloin-Saint-Pierre proposed an approach called `enhanced structural path analysis <http://link.springer.com/article/10.1007/s11367-014-0710-9>`_, which uses `power series <http://en.wikipedia.org/wiki/Power_series>`_ `expansion <http://en.wikipedia.org/wiki/Series_expansion>`_ and `convolution <http://en.wikipedia.org/wiki/Convolution>`_ to propagate relative temporal differences through the supply chain.

In the language of graph algorithm, the ESPA approach (power series expansion) is a `breadth-first search <http://en.wikipedia.org/wiki/Breadth-first_search>`_, while graph traversal (at least as implemented in Brightway2-temporalis) is a `depth-first search <http://en.wikipedia.org/wiki/Depth-first_search>`_.

Benefits of temporal graph traversal
------------------------------------

The first obvious benefit is that we can include both relative and absolute dates. Because we would manually traverse the supply chain graph, we can have certain activity datasets happen at absolute dates. This could be especially helpful for infrastructure built in the past.

Another advantage is that there is no fixed time steps. Each exchange has a relative time difference, but this difference can have arbitrary precision.

Finally, this approach more closely builds on the existing foundation of Brightway2, making it easier to program and test.

Drawbacks of temporal graph traversal
-------------------------------------

Graph traversal, like power series expansion, can only approximate the solution to a set of linear equations. An infinite number of graph traversal steps would be required to get the precise solution. However, in most cases graph traversal will converge on the precise answer relatively quickly.

Cut-off criteria
----------------

Suply chain graphs include loops (e.g. steel needed to generate electricity needed to make steel), and as such can be traversed without end. Cut-off criteria are needed to tell the traversal algorithm that no more work on this particular input is needed, as almost all of its impacts have already been accounted for. Similarly, power series expansion must stop after some number of calculations.

The default cutoff in Brightway2 is that inputs which, throughout their life cycle, contribute less than 0.5 percent of the total LCA score, are no longer traversed.

For temporal graph traversal, we need to be a bit more clever. First, we don't know beforehand what the total LCA score is, because the characterization factors will vary throughout time. In other words, we can't know the total LCA score before starting our calculation. However, we can estimate the *upper bound* of what that score could be, by doing a standard LCA calculation and applying the **highest** characterization factors. We can also lower the cut-off numeric criteria to 0.1 percent of the maximum possible LCA score to make sure we aren't prematurely excluding any supply chain branches.
