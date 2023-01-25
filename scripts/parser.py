""" parse for PDTB style annotation (text + pipe) & RelXML (legacy format) """

from xml.etree.ElementTree import parse

from dialog import Dialog, DiscourseRelation

import typing as t
import warnings as w

import numpy as np

from collections import defaultdict

import csv

import argparse


# Types
Roles = t.Dict[str, t.List[str]]
Token = t.Tuple[str, Roles]
Block = t.List[Token]

Slice = t.Tuple[int, int]
Span = t.List[Slice]
RelSpans = t.Dict[str, t.Union[t.List[int], Span]]


# mask file parsing
def parse_mask(path: str) -> t.Dict[str, t.List[str]]:
    """
    parse masking file
    :param path:
    :return: dict of document token lists
    """
    with open(path, 'r') as fh:
        reader = csv.reader(fh, delimiter="\t")
        rows = [tuple([c.strip() for c in row]) for row in reader]
        docs = defaultdict(list)
        [docs[doc_id].append(text) for (doc_id, _, _, _, text) in rows]
        return docs


# raw text file parsing
def parse_raw(path: str) -> t.Tuple[str, t.List[str], t.List[Slice], t.List[Slice]]:
    """
    parse raw text file
    :param path:
    :return: text, list of group lengths w.r.t. blocks
    """
    with open(path, 'r', encoding='utf-8-sig') as fh:
        text = fh.read()
        groups = tokenize(text, prep=True)
        merged = [[token for block in group for token in block] for group in groups]
        blocks = [block for group in groups for block in group]
        tokens = [token for block in blocks for token in block]

        return text, tokens, get_slices(blocks), get_slices(merged)


# annotation file parsing
def parse_ann(path: str) -> t.List[t.Dict]:
    """
    parse annotation file

    :param path:
    :return:
    """
    with open(path, 'r') as fh:
        reader = csv.reader(fh, delimiter="|")
        rows = [tuple([c.strip() for c in row]) for row in reader]
        return [annotation(row) for row in rows]


def parse_span(span: str) -> t.List[t.Tuple[int, ...]]:
    """
    parse span string into list of indices: '2288..2301;2305..2322' -> [(2288, 2301), (2305, 2322)]
    :param span:
    :return:
    """
    if not span:
        return []

    slices = [tuple(int(ind) for ind in part.split('..')) for part in span.split(';')]

    if any(len(part) > 2 for part in slices):
        raise ValueError(f"Invalid Span: {span}")

    return slices


def slice_text(span: Span, text: str) -> str:
    """
    slice text w.r.t. span
    :param span:
    :param text:
    :return:
    """
    parts = [text[b: e] for b, e in span]
    return " ".join(parts)


def tokenize(text: str, prep: bool = False) -> t.List[t.List[t.List[str]]]:
    """
    tokenize text w.r.t. white text & preprocessing
    :param text:
    :param prep: preprocessor flag
    :return:
    """
    groups = text.strip().split("\n")
    blocks = [group.strip().split("\t") for group in groups]
    tokens = [[block.strip('"').split() for block in group] for group in blocks]

    # preprocessing
    if prep:
        group_list = []
        for group in tokens:
            block_list = []
            for block in group:
                token_list = []
                for token in block:
                    token_list.extend([x[0] for x in preprocess_token(token, {})])
                block_list.append(token_list)
            group_list.append(block_list)
        return group_list

    return tokens


def annotation(data: t.Tuple[str, ...]) -> t.Dict[str, t.Any]:
    """
    convert annotation row to dict

    0	RelationType	Explicit,Implicit,AltLex,EntRel,NoRel
    1	Connective:SpanList	Explicit,AltLex
    7	ConnType:1	Implicit
    10	ConnType:2	Implicit
    8	SemanticClass:1.1	Explicit,Implicit,AltLex
    9	SemanticClass:1.2	Explicit,Implicit,AltLex
    11	SemanticClass:2.1	Implicit
    12	SemanticClass:2.2	Implicit
    14	Arg1:SpanList	Explicit,Implicit,AltLex,EntRel,NoRel
    20	Arg2:SpanList	Explicit,Implicit,AltLex,EntRel,NoRel
    13	Sup1:SpanList	Explicit,Implicit,AltLex
    26	Sup2:SpanList	Explicit,Implicit,AltLex

    :param data:
    :return:
    """

    data = tuple([(e if e not in ['Null', ''] else None) for e in data])

    senses = [
        {"conn": data[7], "sense": [x for x in data[8:10] if x]},
        {"conn": data[10], "sense": [x for x in data[11:13] if x]},
    ]

    senses = [sense for sense in senses if any(sense.values())]

    return {
        "label": data[0],
        "sense": senses,
        "conn": parse_span(data[1]),
        "arg1": parse_span(data[14]),
        "arg2": parse_span(data[20]),
        "sup1": parse_span(data[13]),
        "sup2": parse_span(data[26]),
    }


# RelXML parsing (token-level)
def parse_xml(path: str):
    """
    parse RelXML document (custom format)
    :param path:
    :return:
    """
    doc_id = None
    blocks = []
    labels = {}  # relation types
    senses = {}  # relation senses

    tree = parse(path)
    root = tree.getroot()

    if root.tag != "section":
        raise ValueError(f"XML root should be '<section>'!")

    if len(root) != 1:
        raise ValueError(f"there should be only one element in section!")

    for doc in root:
        if doc.tag != "doc" and [child.tag for child in doc] != ["sentences", "relations"]:
            raise ValueError

        doc_id = doc.attrib.get("id")

        for part in doc:
            if part.tag == "sentences":
                blocks = [parse_block_node(block_node) for block_node in part]
            elif part.tag == "relations":

                idx_list, label_list, sense_list = map(list, zip(*[parse_relation_node(rel_node) for rel_node in part]))

                labels = dict(zip(idx_list, label_list))
                senses = dict(zip(idx_list, sense_list))

    return doc_id, blocks, labels, senses


def parse_block_node(node):
    """
    parse <sent> XML node

    <sent sid="4">
        <parse>...</parse>
        <tokens>
            <token tid="0" surf="PC" pos="...">
                <rel rid="1" role="Arg2"/>
                <rel rid="2" role="Arg1"/>
            </token>
        </tokens>
    </sent>

    :param node:
    :return:
    """
    if node.tag != "sent":
        raise ValueError

    tokens = []
    for e in node:
        if e.tag == "tokens":
            for token_node in e:
                token, roles = parse_token_node(token_node)
                tokens.append((token, roles))
    return tokens


def parse_token_node(node):
    """
    parse <token> XML node

    <token tid="0" surf="PC" pos="...">
        <rel rid="1" role="Arg2"/>
        <rel rid="2" role="Arg1"/>
    </token>

    :param node:
    :return:
    """
    if node.tag != "token":
        raise ValueError

    token = node.attrib.get("surf")
    roles = defaultdict(list)

    for e in node:
        if e.tag != "rel":
            raise ValueError(f"{e.tag} != rel")

        roles[e.attrib.get("rid")].append(e.attrib.get("role")[:4])

    roles = dict(roles)

    # if any(len(roles_list) > 1 for idx, roles_list in roles.items()):
    #     w.warn(f"token '{token}' has more than 1 role: {roles}")

    return token, roles


def parse_relation_node(node):
    """
      <relation rid="9" class="Implicit">
        <conn id="9_0" type="ma">
          <sense id="9_0_0">Comparison.Contrast.Semantic contrast</sense>
        </conn>
        <conn id="9_1" type="e">
          <sense id="9_1_0">Expansion.Conjunction</sense>
        </conn>
      </relation>
      <relation rid="8" class="Explicit">
        <conn id="8_0" type="VOID">
          <sense id="8_0_0">Expansion.Restatement</sense>
        </conn>
      </relation>
      <relation rid="16" class="AltLex">
        <conn id="16_0" type="VOID">
          <sense id="16_0_0">Expansion.Restatement</sense>
        </conn>
      </relation>
    :param node:
    :return:
    """
    if node.tag != "relation":
        raise ValueError

    relation_idx = node.attrib.get("rid")
    relation_type = node.attrib.get("class")

    conns = []
    for conn_node in node:
        if conn_node.tag != "conn":
            raise ValueError

        conn_type = conn_node.attrib.get("type")
        conn_type = None if conn_type == "VOID" else conn_type

        senses = []
        for sense_node in conn_node:
            if sense_node.tag != "sense":
                raise ValueError

            senses.append(sense_node.text)

        conns.append({"connective": conn_type,
                      "sense": (senses[0] if len(senses) == 1 else None if not senses else senses)})

    return relation_idx, relation_type, conns


# Text Pre-Processing
def preprocess(blocks: t.List[Block]) -> t.List[Block]:
    """
    preprocess blocks (token lists)
    :param blocks:
    :return:
    """
    return [preprocess_block(block) for block in blocks]


def preprocess_block(block: Block) -> Block:
    """
    preprocess block
    :param block:
    :return:
    """
    tokens = [preprocess_token(token, roles) for i, (token, roles) in enumerate(block)]
    # flatten list of tokens
    tokens = [token for part in tokens for token in part]
    return tokens


def preprocess_token(token: str, roles: Roles) -> t.List[Token]:
    """
    preprocess token
    .. note:: returns a list
    :param token: token text
    :param roles: token roles dict
    :return: list of token tuples
    """
    # split contractions
    token = token.replace("'", "' ")

    return [(x, roles) for x in token.split()]


# Utilities
def slice_sequence(seq: t.List[t.Any], ref: t.List[t.List[t.Any]]) -> t.List[t.List[t.Any]]:
    """
    chunk a sequence w.r.t. another sequence
    :param seq:
    :param ref: reference nested sequence
    :return:
    """
    slices = get_slices(ref)
    return [seq[b: e] for b, e in slices]


def get_slices(seq: t.List[t.List[t.Any]]) -> t.List[t.Tuple[int, int]]:
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


# Process Blocks to Indices
def convert(blocks: t.List[Block]
            ) -> t.Tuple[t.List[str],
                         t.List[t.Tuple[int, int]],
                         t.Dict[str, RelSpans]
                         ]:
    """
    convert to indices
    :param blocks:
    :return:
    """
    # tokens
    tokens, roles = map(list, zip(*[token for block in blocks for token in block]))

    # slices: block begin & end indices as `tokens` slices
    slices = get_slices(blocks)

    # validate slices
    for i, (b, e) in enumerate(slices):
        assert tokens[b: e] == [token[0] for token in blocks[i]]

    # argument spans
    spans = process_roles(roles)

    return tokens, slices, spans


def process_roles(roles: t.List[t.Dict[str, t.List[str]]]):
    """
    convert token-roles to relation span dict

    [{'1': ['Arg1'], '7': ['Arg1']}, ...]

    :param roles:
    :return:
    """
    spans = defaultdict(lambda: {"conn": [], "arg1": [], "arg2": [], "sup1": [], "sup2": []})

    [[[spans[j][r.lower()].append(i) for r in rlist] for j, rlist in rdict.items()] for i, rdict in enumerate(roles)]

    spans = {idx: {role: process_span(ids) for role, ids in rel.items()} for idx, rel in spans.items()}

    return spans


def process_span(indices: t.List[int]) -> Span:
    """
    convert list of token indices to a list of slices
    :param indices:
    :return:
    """
    chunks = chunk_sequence(indices)
    slices = [((min(ch), max(ch) + 1) if ch else ch) for ch in chunks]
    return slices


def chunk_sequence(sequence: t.List[int], step: int = 1) -> t.List[t.List[int]]:
    """
    chunk a list of ints into chunks w.r.t. continuity
    :param sequence:
    :param step:
    :return:
    """
    if len(sequence) == 0:
        return []

    if min(sequence) - max(sequence) + 1 == len(sequence):
        return [sequence]

    sequence = sorted(sequence)
    chunks = np.split(np.array(sequence), np.where(np.diff(sequence) != step)[0] + 1)
    return [chunk.tolist() for chunk in chunks]


def process_dialog(path: str):
    """
    process dialog file in RelXML format
    :param path:
    :return:
    """
    dialog_id, blocks_list, labels_dict, senses_dict = parse_xml(path)

    blocks_list = preprocess(blocks_list)
    tokens_list, slices_list, spans_dict = convert(blocks_list)

    relations = [{**spans, **{"label": labels_dict.get(idx), "sense": senses_dict.get(idx)}}
                 for idx, spans in spans_dict.items()]

    return Dialog(doc_id=dialog_id,
                  tokens=tokens_list,
                  blocks=slices_list,
                  relations=[DiscourseRelation(**{k.lower(): v for k, v in rel.items()}) for rel in relations])


def create_argument_parser():
    parser = argparse.ArgumentParser(description="LUNA Discourse RelXML parser", prog='PROG')

    add_argument_group_io(parser)

    return parser


def add_argument_group_io(parser):
    argument_group = parser.add_argument_group("I/O Arguments")
    argument_group.add_argument('-d', '--data', required=True, help="path to input  file")

    # file names are fixed, only extension changes
    argument_group.add_argument('-o', '--odir', required=False, default='.', help="path to output directory")

    argument_group.add_argument('-t', '--text', required=False, help="path to raw text file")
    argument_group.add_argument('-a', '--anno', required=False, help="path to annotations")

    argument_group.add_argument('-m', '--mask', required=False, help="path to masked file")


if __name__ == "__main__":
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()

    dialog = process_dialog(args.data)

    if args.text:
        txt, string_tokens, string_blocks, string_groups = parse_raw(args.text)

        assert len(dialog.tokens) == len(string_tokens)

        dialog.chunks = string_blocks
        dialog.groups = string_groups

    # todo: verify dialog.relations using annotations
    if args.anno:
        ann = parse_ann(args.anno)

        assert len(dialog.relations) == len(ann)

    if args.mask:
        masker = parse_mask(args.mask)
        masker_tokens = masker.get(dialog.doc_id)

        assert len(masker_tokens) == len(dialog.tokens)

        dialog.tokens = masker_tokens

    dialog.dump(f"{args.odir}/{dialog.doc_id}.json")
