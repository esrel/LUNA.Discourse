""" parse PDTB style annotation (text + pipe) """

import typing as t

from collections import defaultdict

from dialog import Slice, Dialog, DiscourseRelation
from dialog import index_sequence, index_tokens, parse_span, align_span
from dialog import select_sense

import os
import csv
import argparse


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
        [docs[row[0]].append(row[-1]) for row in rows]
        return docs


# raw text file parsing
def parse_raw(path: str) -> t.Tuple[str, t.List[str], t.List[Slice], t.List[Slice], t.List[Slice]]:
    """
    parse raw text file
    :param path:
    :return: text, tokens, blocks, groups, token indices
    """
    with open(path, 'r') as fh:  # encoding='utf-8-sig'
        text = fh.read()
        groups = tokenize(text, prep=True)
        merged = [[token for block in group for token in block] for group in groups]
        blocks = [block for group in groups for block in group]
        tokens = [token for block in blocks for token in block]

        return text, tokens, index_sequence(blocks), index_sequence(merged), index_tokens(text, tokens)


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
                    token_list.extend(token.replace("'", "' ").split())
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
        {"connective": data[7], "senses": [x for x in data[8:10] if x]},
        {"connective": data[10], "senses": [x for x in data[11:13] if x]},
    ]

    sense, conns = select_sense([sense for sense in senses if any(sense.values())], label=data[0])

    return {
        "label": data[0],
        "sense": sense,
        "conns": conns,
        "conn": parse_span(data[1]),
        "arg1": parse_span(data[14]),
        "arg2": parse_span(data[20]),
        "sup1": parse_span(data[13]),
        "sup2": parse_span(data[26]),
    }


def parse_dialog(raw_path: str, ann_path: str) -> Dialog:
    """
    parse raw text & annotation files
    :param raw_path: path to raw text file
    :param ann_path: path to annotation file
    :return:
    """
    spans = ["conn", "arg1", "arg2", "sup1", "sup2"]

    text, tokens, blocks, groups, token_index = parse_raw(raw_path)
    relation_list = parse_ann(ann_path)

    for i, relation in enumerate(relation_list):
        for span in spans:
            relation_list[i][span] = align_span(relation.get(span, []), token_index)

    relations = [DiscourseRelation(**relation) for relation in relation_list]

    return Dialog(doc_id=gen_id(raw_path),
                  tokens=tokens,
                  blocks=blocks,
                  groups=groups,
                  relations=relations)


def gen_id(path: str):
    """
    generate ID from file name
    :param path:
    :return:
    """
    base_name = os.path.basename(path)
    root_name, _ = os.path.splitext(base_name)
    return root_name.replace("_", "")


def create_argument_parser():
    parser = argparse.ArgumentParser(description="LUNA Discourse xml parser", prog='PROG')

    add_argument_group_io(parser)

    return parser


def add_argument_group_io(parser):
    argument_group = parser.add_argument_group("I/O Arguments")
    # argument_group.add_argument('-d', '--data', required=True, help="path to input  file")

    # file names are fixed, only extension changes
    argument_group.add_argument('-o', '--odir', required=False, default='.', help="path to output directory")

    argument_group.add_argument('-r', '--raw', required=True, help="path to raw text file")
    argument_group.add_argument('-a', '--ann', required=True, help="path to annotations")

    argument_group.add_argument('-m', '--mask', required=False, help="path to masked file")


if __name__ == "__main__":
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()

    dialog = parse_dialog(args.raw, args.ann)

    # update dialog.tokens using masked file tokens
    if args.mask:
        masker = parse_mask(args.mask)
        masker_tokens = masker.get(dialog.doc_id)

        assert len(masker_tokens) == len(dialog.tokens)

        dialog.tokens = masker_tokens

    dialog.dump(f"{args.odir}/{dialog.doc_id}.json")
