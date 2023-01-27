""" apply fixes to loaded dialog """

from dialog import load


def fix_0704000020():
    # Token 410 has roles: ['conn', 'arg2'] in Explicit relation
    # last relation --> reduce arg2 span to start from 411
    sec = 'data/02'
    did = '0704000020'

    dialog = load(f"{sec}/{did}.json")
    dialog.relations[-1].arg2 = [(411, 414)]
    dialog.dump(f"{sec}/{did}.json")


if __name__ == "__main__":
    fix_0704000020()
