""" parse PDTB style annotation in xml (legacy format: RelXML) """

from xml.etree.ElementTree import parse

from collections import defaultdict

from dialog import Dialog, DiscourseRelation
from dialog import select_sense
from dialog import index_sequence, indices_to_span

import argparse


# XML parsing
def parse_xml(path: str):
    """
    parse xml document (custom format)
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

    return token, roles


def parse_relation_node(node):
    """
    parse <relation> XML node

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

        # connective string
        conn_type = conn_node.attrib.get("type")
        conn_type = None if conn_type == "VOID" else conn_type

        senses = []
        for sense_node in conn_node:
            if sense_node.tag != "sense":
                raise ValueError

            senses.append(sense_node.text)

        conns.append({"connective": conn_type, "senses": senses})

    return relation_idx, relation_type, conns


def parse_dialog(path: str) -> Dialog:
    """
    parse dialog file in xml format
    :param path:
    :return:
    """
    dialog_id, block_list, label_dict, sense_dict = parse_xml(path)

    # preprocess tokens
    new_block_list = []
    for block in block_list:
        new_block = []
        for token, roles in block:
            new_block.extend([(x, roles) for x in token.replace("'", "' ").split()])
        new_block_list.append(new_block)
    block_list = new_block_list

    # tokens
    token_list, roles = map(list, zip(*[token for block in block_list for token in block]))

    # slices: block begin & end indices as `tokens` slices
    slice_list = index_sequence(block_list)

    # validate slices
    for i, (b, e) in enumerate(slice_list):
        assert token_list[b: e] == [token[0] for token in block_list[i]]

    # process roles
    spans = defaultdict(lambda: {"conn": [], "arg1": [], "arg2": [], "sup1": [], "sup2": []})
    [[[spans[j][r.lower()].append(i) for r in rlist] for j, rlist in rdict.items()] for i, rdict in enumerate(roles)]
    spans = {idx: {role: indices_to_span(ids) for role, ids in rel.items()} for idx, rel in spans.items()}

    # process senses
    sense_dict = {idx: select_sense(sense_list) for idx, sense_list in sense_dict.items()}
    conns_dict = {idx: x[1] for idx, x in sense_dict.items()}
    sense_dict = {idx: x[0] for idx, x in sense_dict.items()}

    relations = [{**spans,
                  **{"label": label_dict.get(idx), "sense": sense_dict.get(idx), "conns": conns_dict.get(idx)}}
                 for idx, spans in spans.items()]

    return Dialog(doc_id=dialog_id,
                  tokens=token_list,
                  blocks=slice_list,
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


if __name__ == "__main__":
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()

    dialog = parse_dialog(args.data)

    dialog.dump(f"{args.odir}/{dialog.doc_id}.json")
