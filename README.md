# LUNA.Discourse

LUNA Corpus Discourse Data Set consists of 60 dialogs from Italian LUNA Human-Human Corpus 
in the hardware/software help desk domain annotated following Penn Discourse Treebank (PDTB) guideline. 
The data set contains a total of 1,606 discourse relations; 1,052 are explicit discourse relations. 

The dialogs are split into training ( section `02`), development ( section `01`), and test ( section `03`) sets as:
42, 6, and 12 respectively.

## Data Format

Each dialog (file) is stored as a JSON file that has the following structure:

```json
{
  "DOC_ID": "numeric part of a filename",
  "tokens": "flat list of tokens",
  "blocks": "list of token start & end indices",
  "relations": "list of relations"
}
```

For example (reduced):

```json
{
  "DOC_ID": "0703000001",
  "tokens": [
    "helpdesk",
    "buongiorno",
    "sono",
    "<PER>"
  ],
  "blocks": [
    [0, 1],
    [1, 4]
  ],
  "relations": [
    {
      "Conn": [[59, 60]],
      "Arg1": [[5, 7]],
      "Arg2": [[60, 63]],
      "Sup1": [],
      "Sup2": [],
      "type": "Explicit",
      "sense": [{"connective": null, "class": "Expansion.Restatement.Equivalence"}]
    },
    {
      "Conn": [],
      "Arg1": [[20, 31]],
      "Arg2": [[31, 31], [33, 37]],
      "Sup1": [],
      "Sup2": [],
      "type": "Implicit",
      "sense": [
        {"connective": "poi", "class": "Temporal.Asynchronous"},
        {"connective": "e", "class": "Expansion.Conjunction"}
      ]
    },
    {
      "Conn": [[159, 161]],
      "Arg1": [[141, 143], [151, 153], [169, 170]],
      "Arg2": [[157, 164]],
      "Sup1": [[137, 141]],
      "Sup2": [],
      "type": "AltLex",
      "sense": [{"connective": null, "class": "Expansion.Restatement"}]
    }
  ]
}
```

## Data Schemas
Below are the schemas for a relation and a dialog (in `dataclass` format).

```python
import typing as t

class Relation:
    conn: t.List[t.Tuple[int, int]]  # connective span
    arg1: t.List[t.Tuple[int, int]]  # arg1 span
    arg2: t.List[t.Tuple[int, int]]  # arg2 span
    sup1: t.List[t.Tuple[int, int]]  # sup1 span
    sup2: t.List[t.Tuple[int, int]]  # sup2 span
    type: str  # one of Explicit, Implicit, AltLex, and EntRel
    sense: t.List[t.Dict[str, t.Union[str, None]]]
    

class Dialog:
    doc_id: str  # numeric part of a filename
    tokens: t.List[str]
    blocks: t.List[t.Tuple[int, int]]
    relations: t.List[Relation]
```

All spans (for a **connective**, **Arg1** and **Arg2**, **Sup1** and **Sup2**) are lists of start & end indices
with respect to `tokens`. 

A relation can have several senses. 
Each sense has the `connective` & `sense` fields; where `connective` field is only populated for Implicit relations. 

## Anonymization

The data has been anonymized at token-level using the following conversions:

| Replacement | Description                                  |
|:------------|:---------------------------------------------|
| <ABBR>      | abbreviations (unknown); e.g. `HL`           |
| <BRAND>     | brands; e.g. `Fujitsu`                       |
| <DIGIT>     | digit-words; e.g. `due`                      |
| <LANG>      | language; e.g. `Italiano`                    |
| <LOC>       | locations; e.g. `Italia`                     |
| <NUM>       | number-words; e.g. `duomilasei`              |
| <ORD>       | ordinals; e.g. `quarto`                      | 
| <ORG>       | organizations; e.g. `CSI`                    |
| <PER>       | person names; e.g. `Monica`                  |
| <PROG>      | software and IT terms; e.g. `Windows`, `PIN` |
| <UNK>       | rest of capitalized & abbreviated tokens     |


## Known Issues, Peculiarities and TODOs

- relation spans contain empty segments that should be cleaned (e.g. `[31, 31]` see in example above)

- preposition & article contractions are merged into the following token; i.e. `l'anno`

- the number of anonymization "tags" could be reduced; since they are hard to distinguish.
  e.g. merging `<ABBR>`, `<LANG>`, `<PROG>`, `<BRAND>` and `<UNK>` as `<MISC>` 

- in the original dialog files several "blocks" appear on the same line; this could be used as an additional information