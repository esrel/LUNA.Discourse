""" Basic Reader for LUNA Discourse Data """

__author__ = "Evgeny A. Stepanov"
__email__ = "stepanov.evgeny.a@gmail.com"
__status__ = "dev"
__version__ = "0.1.0"


import typing as t
import warnings as w

from dataclasses import dataclass, asdict
from collections import defaultdict

import json
import argparse


RELATION_TYPES = ["Explicit", "Implicit", "AltLex", "EntRel", "NoRel"]


# continuous slice of a sequence as (begin, end)
Slice = t.Tuple[int, int]
# argument span: consists of 0 or more Slices
Span = t.List[Slice]


@dataclass
class DiscourseRelation:
    # label(s)
    label: str  # type in RELATION_TYPES
    sense: t.List[t.Dict[str, str]] = None
    # spans
    conn: Span = None
    arg1: Span = None
    arg2: Span = None
    sup1: Span = None
    sup2: Span = None

    @property
    def type(self):
        return self.label

    def __post_init__(self):
        self.conn = [] if self.conn is None else sanitize_span(self.conn)
        self.arg1 = [] if self.arg1 is None else sanitize_span(self.arg1)
        self.arg2 = [] if self.arg2 is None else sanitize_span(self.arg2)
        self.sup1 = [] if self.sup1 is None else sanitize_span(self.sup1)
        self.sup2 = [] if self.sup2 is None else sanitize_span(self.sup2)

        self.validate()

    def validate(self):
        """ basic validation for a relation element values """
        # validate label (relation type)
        if self.label not in RELATION_TYPES:
            raise ValueError(f"Unknown Discourse Relation Type: '{self.label}'")

        # validate sense
        if self.sense:
            if len(self.sense) > 1:
                w.warn(f"Discourse Relation has {len(self.sense)} senses: {self.sense}")

            if not all(x.get("sense") for x in self.sense):
                w.warn(f"Discourse Relation has no sense label: {self.sense}")

        # validate token roles
        for index, roles in self.astokens().items():
            if len(roles) > 1:
                w.warn(f"Token {index} has roles: {roles} in {self.label} relation.")

    def astokens(self) -> t.Dict[int, t.List[str]]:
        """
        return relation as a list of token role lists
        :return:
        """
        roles = ["conn", "arg1", "arg2", "sup1", "sup2"]
        tokens = defaultdict(list)
        [[tokens[i].append(role) for i in expand_span(getattr(self, role))] for role in roles]
        return dict(tokens)


@dataclass
class Token:
    token: str
    index: t.Union[int, str] = None  # token index within dialog
    roles: t.Dict[str, Span] = None

    block: t.Union[int, str] = None  # block index within dialog (from parses)
    chunk: t.Union[int, str] = None  # chunk index within dialog (from raw text)
    group: t.Union[int, str] = None  # group index within dialog (from raw text)


@dataclass
class Dialog:
    doc_id: str
    tokens: t.List[str]
    blocks: t.List[Slice] = None
    chunks: t.List[Slice] = None
    groups: t.List[Slice] = None
    relations: t.List[DiscourseRelation] = None

    def dump(self, path: str = None):
        if not path:
            return asdict(self)
        else:
            json.dump(asdict(self), open(path, 'w'), indent=2)

    def astokens(self) -> t.List[Token]:
        """ convert dialog to token-level """
        # token info
        tokens = [Token(token, index=i) for i, token in enumerate(self.tokens)]

        # block info
        if self.blocks:
            for i, (b, e) in enumerate(self.blocks):
                for j in range(b, e):
                    tokens[j].block = i

        # chunk info
        if self.chunks:
            for i, (b, e) in enumerate(self.chunks):
                for j in range(b, e):
                    tokens[j].chunk = i

        # group info
        if self.groups:
            for i, (b, e) in enumerate(self.blocks):
                for j in range(b, e):
                    tokens[j].group = i

        # roles info
        if self.relations:
            roles = defaultdict(dict)
            [[roles[j].update({i: r}) for j, r in rel.astokens().items()] for i, rel in enumerate(self.relations)]

            for j, roles_dict in roles.items():
                tokens[j].roles = roles_dict

        return tokens


def expand_span(span: Span) -> t.List[int]:
    """
    expand Span to list of ints
    :param span:
    :return:
    """
    return sorted([i for s in [list(range(b, e)) for b, e in span] for i in s])


def sanitize_span(span: Span) -> Span:
    """
    sanitize span: removing empty slices
    :param span:
    :return:
    """
    def validate_part(bos: int, eos: int) -> t.Tuple[int, int]:
        if bos == eos:
            w.warn(f"Empty Slice: {bos} == {eos}")
        elif bos > eos:
            raise ValueError(f"Invalid Slice: {bos} > {eos}")

        return bos, eos

    return [validate_part(b, e) for b, e in span if b != e]


def load(path: str) -> Dialog:
    """
    load a dialog from file
    :param path: path to a dialog file
    :return: dialog as a dict
    """
    data = json.load(open(path, 'r'))
    return Dialog(
        doc_id=data.get("DOC_ID"),
        tokens=data.get("tokens"),
        blocks=data.get("blocks"),
        chunks=data.get("chunks"),
        groups=data.get("groups"),
        relations=[DiscourseRelation(**{k.lower(): v for k, v in rel.items()}) for rel in data.get("relations", [])]
    )


def create_argument_parser():
    parser = argparse.ArgumentParser(description="LUNA Discourse Reader", prog='PROG')

    add_argument_group_io(parser)

    return parser


def add_argument_group_io(parser):
    argument_group = parser.add_argument_group("I/O Arguments")
    argument_group.add_argument('-d', '--data', help="path to dialog file")


if __name__ == "__main__":
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()

    dialog = load(args.data)
    print(dialog)
