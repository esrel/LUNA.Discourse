""" test correctness of extracted spans & labels """

from parser import parse_raw, parse_ann, parse_dialog, read_tabular
from dialog import slice_text, slice_sequence
from corpus import Corpus, read_dir

from collections import Counter

import os


def read_annotations(path: str):
    """
    read annotation
    :param path:
    :return:
    """
    dirs = ['01', '02', '03']
    data = []
    for dir_name in dirs:
        files = read_dir(os.path.join(path, dir_name))
        for file_path in files:
            data.extend(read_tabular(os.path.join(path, dir_name, file_path), delimiter="|"))
    return data


def annotation_stats(data):
    """
    process annotations & extract label & sense stats
    :param data:
    :return:
    """
    store = ['Expansion.Restatement.Equivalence', 'Expansion.Restatement.Specification']

    # filter tuples
    refs = [(x[0], x[8], x[9], x[11], x[12]) for x in data]
    labels, sense00, sense01, sense10, sense11 = map(list, zip(*refs))

    # senses = sorted(list(set(sense00 + sense01 + sense10 + sense11)))

    # generic sense info
    # bins = [(lbl, bool(s00), bool(s01), bool(s10), bool(s11)) for lbl, s00, s01, s10, s11 in refs]
    # print(dict(Counter(bins)))

    # reduce senses to L2+
    senses = [(sense if sense in store else ".".join(sense.split('.')[:2])) for sense in sense00]

    return {
        "labels": dict(Counter(labels)),
        "senses": dict(Counter(senses)),
        "paired": dict(Counter(zip(labels, senses)))
    }


def test_conversion(raw: str, ann: str):
    """
    test conversion
    :param raw: raw text file
    :param ann: annotation file
    :return:
    """
    def get_ann_text(span, txt):
        return "".join(slice_text(span, txt).replace('"', '').split())

    def get_tok_text(span, tok):
        return "".join([t for b in slice_sequence(tok, span) for t in b])

    spans = ["conn", "arg1", "arg2", "sup1", "sup2"]

    dialog = parse_dialog(raw, ann)
    text, tokens, blocks, groups, token_index = parse_raw(raw)
    relations = parse_ann(ann)

    # compare span text
    for i, rel in enumerate(relations):

        for span_key in spans:
            tok_txt = get_tok_text(getattr(dialog.relations[i], span_key), tokens)
            ann_txt = get_ann_text(rel.get(span_key), text)

            assert tok_txt == ann_txt


def test_corpus_senses(path: str, ann: str):
    """
    load corpus & get label & sense counts
    :param path:
    :return:
    """
    # json file stats
    data = Corpus(path)
    stats = data.stats()

    dst_senses = {('' if k is None else k): v for k, v in stats.get("senses").items()}
    dst_paired = {(x, ('' if k is None else k)): v for (x, k), v in stats.get("paired").items()}

    # annotation files stats
    relations = read_annotations(ann)
    ann_stats = annotation_stats(relations)
    ann_senses = ann_stats.get("senses")
    ann_paired = ann_stats.get("paired")

    assert ann_stats.get("labels") == stats.get("labels")

    assert dst_senses == ann_senses
    assert dst_paired == ann_paired


def test_corpus_spans(raw: str, ann: str):
    """
    test conversion w.r.t. span texts
    :param raw:
    :param ann:
    :return:
    """
    dirs = ['01', '02', '03']
    for dir_name in dirs:
        files = read_dir(os.path.join(raw, dir_name))
        for file_name in files:
            test_conversion(os.path.join(raw, dir_name, file_name), os.path.join(ann, dir_name, file_name))


if __name__ == "__main__":
    data_path = 'data'
    ann_path = 'wdir/ann'
    raw_path = 'wdir/raw'

    test_corpus_senses(data_path, ann_path)
    test_corpus_spans(raw_path, ann_path)
