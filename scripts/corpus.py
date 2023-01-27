""" Basic Reader for LUNA Discourse Data: all dialogs """

__author__ = "Evgeny A. Stepanov"
__email__ = "stepanov.evgeny.a@gmail.com"
__status__ = "dev"
__version__ = "0.1.0"


import typing as t

from collections import defaultdict, Counter

from dialog import load

import os
import argparse


DATA_DIRS = {"dev": "01", "trn": "02", "tst": "03"}


class Corpus:

    def __init__(self, path: str, dirs: t.Dict[str, str] = None):
        """
        init (load) dialogs from files
        :param path:
        :param dirs:
        """
        dirs = DATA_DIRS if dirs is None else dirs

        data = {}
        sets = defaultdict(list)
        for key, directory in dirs.items():
            files = read_dir(os.path.join(path, directory))
            for file_path in files:
                dialog = load(os.path.join(path, directory, file_path))
                data[dialog.doc_id] = dialog
                sets[key].append(dialog.doc_id)

        self.data = data
        self.sets = dict(sets)

    @property
    def trn(self):
        return [d for k, d in self.data.items() if k in self.sets.get("trn")]

    @property
    def dev(self):
        return [d for k, d in self.data.items() if k in self.sets.get("dev")]

    @property
    def tst(self):
        return [d for k, d in self.data.items() if k in self.sets.get("tst")]

    def stats(self, part: str = None) -> t.Dict[str, t.Dict[str, int]]:
        """
        basic data stats either for whole data or part
        :param part: split of data to get stats for
        :return:
        """
        if part:
            if part not in self.sets:
                raise ValueError(f"Unknown Corpus Part: {part}")
            data = getattr(self, part)
        else:
            data = list(self.data.values())

        # label & sense tuples
        paired = [[(r.label, r.sense) for r in d.relations] for d in data]
        paired = [ref for dialog in paired for ref in dialog]

        labels, senses = map(list, zip(*paired))

        info_list = [d.info for d in data]

        return {
            "dialog": len(data),
            "tokens": sum([x.get("tokens", 0) for x in info_list]),
            "blocks": sum([x.get("blocks", 0) for x in info_list]),
            "groups": sum([x.get("groups", 0) for x in info_list]),
            "relations": sum([x.get("relations", 0) for x in info_list]),
            "labels": dict(Counter(labels)),
            "senses": dict(Counter(senses)),
            "paired": dict(Counter(paired)),
        }


def read_dir(path: str) -> t.List[str]:
    """
    read directory files
    :param path:
    :return:
    """
    data = []
    if os.path.isfile(path):
        # path is a file
        data.append(os.path.basename(path))
    elif os.path.isdir(path):
        # path is a dir
        for root, dirs, files in os.walk(path):
            # remove hidden files
            files = [f for f in files if not f.startswith('.')]
            data.extend(files)
    else:
        raise ValueError('No directory or file provided...')
    return data


def create_argument_parser():
    parser = argparse.ArgumentParser(description="LUNA Discourse Corpus Reader", prog='PROG')

    add_argument_group_io(parser)

    return parser


def add_argument_group_io(parser):
    argument_group = parser.add_argument_group("I/O Arguments")
    argument_group.add_argument('-d', '--data', help="path to data")


if __name__ == "__main__":
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()

    corpus = Corpus(args.data)
