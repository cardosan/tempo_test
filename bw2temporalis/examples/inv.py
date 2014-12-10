db_data = {
    (u'temp-example-db', "CO2"): {
        "type": "emission"
    },
    (u'temp-example-db', "CH4"): {
        "type": "emission"
    },
    (u'temp-example-db', u'Functional Unit'): {
        u'exchanges': [
            {
                u'amount': 5,
                u'input': (u'temp-example-db', u'EOL'),
                u'temporal distribution': [
                    (0, 1),
                    (1, 1),
                    (2, 1),
                    (3, 1),
                    (4, 1)
                ],
                u'type': u'technosphere'
            },
        ],
        u'name': u'Functional Unit',
        'type': 'process'
    },
    (u'temp-example-db', u'EOL'): {
        u'exchanges': [
            {
                u'amount': 0.8,
                u'input': (u'temp-example-db', u'Waste'),
                u'type': u'technosphere'
            },
            {
                u'amount': 0.2,
                u'input': (u'temp-example-db', u'Landfill'),
                u'type': u'technosphere'
            },
            {
                u'amount': 1,
                u'input': (u'temp-example-db', u'Use'),
                u'type': u'technosphere'
            },
        ],
        u'name': u'EOL',
        'type': 'process'
    },
    (u'temp-example-db', u'Use'): {
        u'exchanges': [
            {
                u'amount': 1,
                u'input': (u'temp-example-db', u'Production'),
                u'temporal distribution': [(-0.5, 1)],
                u'type': u'technosphere'
            },
        ],
        u'name': u'Use',
        'type': 'process'
    },
    (u'temp-example-db', u'Production'): {
        u'exchanges': [
            {
                u'amount': 1,
                u'input': (u'temp-example-db', u'Transport'),
                u'temporal distribution': [(-0.1, 1)],
                u'type': u'technosphere'
            },
        ],
        u'name': u'Production',
        'type': 'process'
    },
    (u'temp-example-db', u'Transport'): {
        u'exchanges': [
            {
                u'amount': 1,
                u'input': (u'temp-example-db', u'Sawmill'),
                u'type': u'technosphere'
            },
            {
                u'amount': 0.1,
                u'input': (u'temp-example-db', u'CO2'),
                u'type': u'biosphere'
            },
        ],
        u'name': u'Production',
        'type': 'process'
    },
    (u'temp-example-db', u'Sawmill'): {
        u'exchanges': [
            {
                u'amount': 1.2,
                u'input': (u'temp-example-db', u'Forest'),
                u'temporal distribution': [(-0.5, 1.2)],
                u'type': u'technosphere'
            },
            {
                u'amount': 0.1,
                u'input': (u'temp-example-db', u'CO2'),
                u'type': u'biosphere'
            },
        ],
        u'name': u'Sawmill',
        'type': 'process'
    },
    (u'temp-example-db', u'Forest'): {
        u'exchanges': [
            {
                u'amount': -.2 * 6,
                u'input': (u'temp-example-db', u'CO2'),
                u'temporal distribution': [(x, -.2) for x in (0, 5, 10, 15, 20, 30)],
                u'type': u'biosphere'
            },
            {
                u'amount': 1.5,
                u'input': (u'temp-example-db', u'Thinning'),
                u'temporal distribution': [
                    (5, .5),
                    (10, .5),
                    (15, .5),
                ],
                u'type': u'technosphere'
            },
        ],
        u'name': u'Forest',
        'type': 'process'
    },
    (u'temp-example-db', u'Thinning'): {
        u'exchanges': [
            {
                u'amount': 1,
                u'input': (u'temp-example-db', u'Thinning'),
                u'type': u'production'
            },
            {
                u'amount': 1,
                u'input': (u'temp-example-db', u'Avoided impact - thinnings'),
                u'type': u'production'
            },
        ],
        u'name': u'Thinning',
        'type': 'process'
    },
    (u'temp-example-db', u'Landfill'): {
        u'exchanges': [
            {
                u'amount': 0.1,
                u'input': (u'temp-example-db', u'CH4'),
                u'temporal distribution': [
                    (20, 0.025),
                    (30, 0.025),
                    (40, 0.025),
                    (50, 0.025)
                ],
                u'type': u'biosphere'
            },
        ],
        u'name': u'Landfill',
        'type': 'process'
    },
    (u'temp-example-db', u'Waste'): {
        u'exchanges': [
            {
                u'amount': 1,
                u'input': (u'temp-example-db', u'Waste'),
                u'type': u'production'
            },
            {
                u'amount': 1,
                u'input': (u'temp-example-db', u'Avoided impact - waste'),
                u'type': u'production'
            },
        ],
        u'name': u'Waste',
        'type': 'process'
    },
    (u'temp-example-db', u'Avoided impact - waste'): {
        u'exchanges': [
            {
                u'amount': -0.6,
                u'input': (u'temp-example-db', u'CO2'),
                u'type': u'biosphere'
            },
            {
                u'amount': 1,
                u'input': (u'temp-example-db', u'Avoided impact - waste'),
                u'type': u'production'
            },
        ],
        u'name': u'Avoided impact - waste',
        'type': 'process'
    },
    (u'temp-example-db', u'Avoided impact - thinnings'): {
        u'exchanges': [
            {
                u'amount': -0.2,
                u'input': (u'temp-example-db', u'CO2'),
                u'type': u'biosphere'
            },
            {
                u'amount': 1,
                u'input': (u'temp-example-db', u'Avoided impact - thinnings'),
                u'type': u'production'
            },
        ],
        u'name': u'Avoided impact - thinnings',
        'type': 'process'
    }
}
