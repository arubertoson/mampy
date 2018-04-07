

name = 'mampy'

version = '0.2.1'

authors = [
    'malbertsson',
]

requires = [
    '~python',
    'maya',
    'contextlib2',
]


tests = {
    'unit': {
        'command': 'mayapy -m pytest -s test/unit',
        'requires': ['pytest']
    }
}


def commands():
    appendenv('PYTHONPATH', '{root}/mampy')
