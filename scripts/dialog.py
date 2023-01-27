""" Basic Reader for LUNA Discourse Data """

__author__ = "Evgeny A. Stepanov"
__email__ = "stepanov.evgeny.a@gmail.com"
__status__ = "dev"
__version__ = "0.1.0"


import typing as t
import warnings as w

import numpy as np

from dataclasses import dataclass, asdict
from collections import defaultdict

import json
import argparse


RELATION_TYPES = ["Explicit", "Implicit", "AltLex", "EntRel", "NoRel"]
RELATION_SENSE = ["Explicit", "Implicit", "AltLex"]

# defaults for sense selection
CONNS_INDEX = 0
SENSE_INDEX = 0
SENSE_LEVEL = 2
SENSE_STORE = ['Expansion.Restatement.Equivalence', 'Expansion.Restatement.Specification']

# continuous slice of a sequence as (begin, end)
Slice = t.Tuple[int, int]
# argument span: consists of 0 or more Slices
Span = t.List[Slice]


@dataclass
class DiscourseRelation:
    # label(s)
    label: str  # discourse relation type from RELATION_TYPES
    sense: str = None  # discourse relation sense
    conns: str = None  # discourse connective string (for Implicit relations)
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
        # set warnings to repeat
        w.simplefilter('always', UserWarning)

        # validate label (relation type)
        if self.label not in RELATION_TYPES:
            raise ValueError(f"Unknown Discourse Relation Type: '{self.label}'")

        # validate sense
        if not self.sense and self.label in RELATION_SENSE:
            w.warn(f"{self.label} Discourse Relation has no 'sense': {self.sense}")

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
    group: t.Union[int, str] = None  # group index within dialog (from raw text)


@dataclass
class Dialog:
    doc_id: str
    tokens: t.List[str]
    blocks: t.List[Slice] = None
    groups: t.List[Slice] = None
    relations: t.List[DiscourseRelation] = None

    @property
    def info(self) -> t.Dict[str, t.Union[str, int]]:
        """ return basic info as dict """
        return {
            "doc_id": self.doc_id,
            "tokens": len(self.tokens) if self.tokens else None,
            "blocks": len(self.blocks) if self.blocks else None,
            "groups": len(self.groups) if self.groups else None,
            "relations": len(self.relations) if self.relations else None
        }

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

        # group info
        if self.groups:
            for i, (b, e) in enumerate(self.groups):
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


def parse_span(span: str) -> Span:
    """
    parse span string into list of indices: '2288..2301;2305..2322' -> [(2288, 2301), (2305, 2322)]
    :param span:
    :return:
    """
    if not span:
        return []

    # slices = [tuple(int(ind) for ind in part.split('..')) for part in span.split(';')]
    slices = []
    for part in span.split(';'):
        bos, eos = part.split('..')
        slices.append((int(bos), int(eos)))

    if any(len(part) != 2 for part in slices):
        raise ValueError(f"Invalid Span: {span}")

    return sanitize_span(slices)


# Slice & Span Methods
def slice_sequence(seq: t.List[t.Any], ref: t.List[Slice]) -> t.List[t.List[t.Any]]:
    """
    chunk a sequence w.r.t. a list of slices
    :param seq:
    :param ref: reference nested sequence
    :return:
    """
    return [seq[b: e] for b, e in ref]


def index_sequence(seq: t.List[t.List[t.Any]]) -> Span:
    """
    return list of begin & end tuples for a list-of-lists (w.r.t. flat list)
    :param seq:
    :return:
    """
    counts = list(map(len, seq))  # block token counts

    b_list = [(sum(counts[:i])) for i, count in enumerate(counts)]
    e_list = b_list[1:] + [sum(counts)]  # shift by 1 & add token length

    slices = list(zip(b_list, e_list))

    return slices


def chunk_sequence(seq: t.List[int], step: int = 1) -> t.List[t.List[int]]:
    """
    chunk a list of ints into chunks w.r.t. continuity
    :param seq:
    :param step:
    :return:
    """
    if len(seq) == 0:
        return []

    if min(seq) - max(seq) + 1 == len(seq):
        return [seq]

    seq = sorted(seq)
    chunks = np.split(np.array(seq), np.where(np.diff(seq) != step)[0] + 1)
    return [chunk.tolist() for chunk in chunks]


def indices_to_span(indices: t.List[int]) -> Span:
    """
    convert list of token indices to a list of slices
    :param indices:
    :return:
    """
    chunks = chunk_sequence(indices)
    slices = [((min(ch), max(ch) + 1) if ch else ch) for ch in chunks]
    return slices


# text & tokens
def slice_text(span: Span, text: str) -> str:
    """
    slice text w.r.t. span
    :param span:
    :param text:
    :return:
    """
    parts = [text[b: e] for b, e in span]
    return " ".join(parts)


def index_tokens(text: str, tokens: t.List[str]) -> t.List[Slice]:
    """
    index tokens by character being - end in text
    :param text:
    :param tokens:
    :return:
    """
    indices = []
    pointer = 0
    for i, token in enumerate(tokens):
        idx = text.index(token, pointer)
        pointer = idx + len(token)
        indices.append((idx, pointer))

    # assert [text[b:e] for b, e in indices] == tokens

    return indices


def align_span(span: Span, tokens: t.List[Slice]) -> Span:
    """
    convert character span to token-level span, aligning the indices
    :param span:
    :param tokens:
    :return:
    """
    if not span:
        return span

    token_ids = [[i for i, (bot, eot) in enumerate(tokens) if (bot >= b and eot <= e)] for b, e in span]
    token_ids = [i for s in token_ids for i in s]

    if not token_ids:
        w.warn(f"Empty Character Span: {span}")

    return indices_to_span(token_ids)


# sense decision
def select_sense(senses: t.List[t.Dict[str, t.Union[None, t.List[str]]]],
                 conns: int = CONNS_INDEX,
                 sense: int = SENSE_INDEX,
                 level: int = SENSE_LEVEL,
                 store: t.List[str] = None,
                 label: str = None,
                 ) -> t.Tuple[t.Union[str, None], t.Union[str, None]]:
    """
    select sense from a list of senses & return sense & connective
    [{"connective": None, "senses": [str, str, ...]}]
    :param senses:
    :param conns: connective index to select
    :param sense: sense index to select
    :param level: sense level to provide
    :param store: list of senses to return as is
    :param label: relation type (label)
    :return:
    """
    # set warnings to repeat
    w.simplefilter('always', UserWarning)

    conns_idx = conns  # connective to select
    sense_idx = sense  # sense of connective to select
    sense_lvl = level  # max sense level to consider

    store = SENSE_STORE if store is None else store

    sense_text = None
    conns_text = None

    if not senses:
        w.warn(f"{label} Discourse Relation has no sense: {senses}")
    else:
        if len(senses) > 1:
            w.warn(f"Discourse Relation has {len(senses)} connective candidates: {senses}")

        if any(len(y) > 1 for y in [x.get("senses") for x in senses]):
            w.warn(f"Discourse Relation has multi-sense connective: {senses}")

        # select connective
        sense_dict = senses[0] if len(senses) - 1 < conns_idx else senses[conns_idx]

        # store connective string
        conns_text = sense_dict.get("connective")
        sense_list = sense_dict.get("senses", [])

        # select connective sense: could be empty
        if sense_list:
            sense_text = sense_list[0] if len(sense_list) - 1 < sense_idx else sense_list[sense_idx]

            # reduce connective sense to a level
            sense_text = ".".join(sense_text.split('.')[:sense_lvl]) if sense_text not in store else sense_text

    return sense_text, conns_text


def load(path: str) -> Dialog:
    """
    load a dialog from file
    :param path: path to a dialog file
    :return: dialog as a dict
    """
    data = json.load(open(path, 'r'))
    return Dialog(
        doc_id=data.get("doc_id"),
        tokens=data.get("tokens"),
        blocks=data.get("blocks"),
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

    print(dialog.info)
