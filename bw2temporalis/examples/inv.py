# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *


db_data = {
    ('temp-example-db', "CO2"): {
        "type": "emission"
    },
    ('temp-example-db', "CH4"): {
        "type": "emission"
    },
    ('temp-example-db', 'Functional Unit'): {
        'exchanges': [
            {
                'amount': 5,
                'input': ('temp-example-db', 'EOL'),
                'temporal distribution': [
                    (0, 1),
                    (1, 1),
                    (2, 1),
                    (3, 1),
                    (4, 1)
                ],
                'type': 'technosphere'
            },
        ],
        'name': 'Functional Unit',
        'type': 'process'
    },
    ('temp-example-db', 'EOL'): {
        'exchanges': [
            {
                'amount': 0.8,
                'input': ('temp-example-db', 'Waste'),
                'type': 'technosphere'
            },
            {
                'amount': 0.2,
                'input': ('temp-example-db', 'Landfill'),
                'type': 'technosphere'
            },
            {
                'amount': 1,
                'input': ('temp-example-db', 'Use'),
                'type': 'technosphere'
            },
        ],
        'name': 'EOL',
        'type': 'process'
    },
    ('temp-example-db', 'Use'): {
        'exchanges': [
            {
                'amount': 1,
                'input': ('temp-example-db', 'Production'),
                'temporal distribution': [(-0.5, 1)],
                'type': 'technosphere'
            },
        ],
        'name': 'Use',
        'type': 'process'
    },
    ('temp-example-db', 'Production'): {
        'exchanges': [
            {
                'amount': 1,
                'input': ('temp-example-db', 'Transport'),
                'temporal distribution': [(-0.1, 1)],
                'type': 'technosphere'
            },
        ],
        'name': 'Production',
        'type': 'process'
    },
    ('temp-example-db', 'Transport'): {
        'exchanges': [
            {
                'amount': 1,
                'input': ('temp-example-db', 'Sawmill'),
                'type': 'technosphere'
            },
            {
                'amount': 0.1,
                'input': ('temp-example-db', 'CO2'),
                'type': 'biosphere'
            },
        ],
        'name': 'Production',
        'type': 'process'
    },
    ('temp-example-db', 'Sawmill'): {
        'exchanges': [
            {
                'amount': 1.2,
                'input': ('temp-example-db', 'Forest'),
                'temporal distribution': [(-0.5, 1.2)],
                'type': 'technosphere'
            },
            {
                'amount': 0.1,
                'input': ('temp-example-db', 'CO2'),
                'type': 'biosphere'
            },
        ],
        'name': 'Sawmill',
        'type': 'process'
    },
    ('temp-example-db', 'Forest'): {
        'exchanges': [
            {
                'amount': -.2 * 6,
                'input': ('temp-example-db', 'CO2'),
                'temporal distribution': [(x, -.2) for x in (0, 5, 10, 15, 20, 30)],
                'type': 'biosphere'
            },
            {
                'amount': 1.5,
                'input': ('temp-example-db', 'Thinning'),
                'temporal distribution': [
                    (5, .5),
                    (10, .5),
                    (15, .5),
                ],
                'type': 'technosphere'
            },
        ],
        'name': 'Forest',
        'type': 'process'
    },
    ('temp-example-db', 'Thinning'): {
        'exchanges': [
            {
                'amount': 1,
                'input': ('temp-example-db', 'Thinning'),
                'type': 'production'
            },
            {
                'amount': 1,
                'input': ('temp-example-db', 'Avoided impact - thinnings'),
                'type': 'production'
            },
        ],
        'name': 'Thinning',
        'type': 'process'
    },
    ('temp-example-db', 'Landfill'): {
        'exchanges': [
            {
                'amount': 0.1,
                'input': ('temp-example-db', 'CH4'),
                'temporal distribution': [
                    (20, 0.025),
                    (30, 0.025),
                    (40, 0.025),
                    (50, 0.025)
                ],
                'type': 'biosphere'
            },
        ],
        'name': 'Landfill',
        'type': 'process'
    },
    ('temp-example-db', 'Waste'): {
        'exchanges': [
            {
                'amount': 1,
                'input': ('temp-example-db', 'Waste'),
                'type': 'production'
            },
            {
                'amount': 1,
                'input': ('temp-example-db', 'Avoided impact - waste'),
                'type': 'production'
            },
        ],
        'name': 'Waste',
        'type': 'process'
    },
    ('temp-example-db', 'Avoided impact - waste'): {
        'exchanges': [
            {
                'amount': -0.6,
                'input': ('temp-example-db', 'CO2'),
                'type': 'biosphere'
            },
            {
                'amount': 1,
                'input': ('temp-example-db', 'Avoided impact - waste'),
                'type': 'production'
            },
        ],
        'name': 'Avoided impact - waste',
        'type': 'process'
    },
    ('temp-example-db', 'Avoided impact - thinnings'): {
        'exchanges': [
            {
                'amount': -0.2,
                'input': ('temp-example-db', 'CO2'),
                'type': 'biosphere'
            },
            {
                'amount': 1,
                'input': ('temp-example-db', 'Avoided impact - thinnings'),
                'type': 'production'
            },
        ],
        'name': 'Avoided impact - thinnings',
        'type': 'process'
    }
}
