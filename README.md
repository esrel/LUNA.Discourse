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
  "blocks": "list of token start & end indices for blocks from parser",
  "chunks": "list of token start & end indices for blocks in text file (tab-separated)",
  "groups": "list of token start & end indices for groups in text file (nl-separated)",
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
  "chunks": [
    [0, 4]
  ],
  "groups": [
    [0, 4]
  ],
  "relations": [
    {
      "label": "Explicit",
      "sense": [{"connective": null, "sense": "Expansion.Restatement.Equivalence"}],
      "conn": [[59, 60]],
      "arg1": [[5, 7]],
      "arg2": [[60, 63]],
      "sup1": [],
      "sup2": []
    },
    {
      "label": "Implicit",
      "sense": [
        {"connective": "poi", "class": "Temporal.Asynchronous"},
        {"connective": "e", "class": "Expansion.Conjunction"}
      ], 
      "conn": [],
      "arg1": [[20, 31]],
      "arg2": [[31, 32], [33, 38]],
      "sup1": [],
      "sup2": []
    },
    {
      "label": "AltLex",
      "sense": [{"connective": null, "sense": "Expansion.Restatement"}],
      "conn": [[159, 161]],
      "arg1": [[141, 144], [151, 154], [169, 171]],
      "arg2": [[157, 164]],
      "sup1": [[137, 141]],
      "sup2": []
    }
  ]
}
```

## Data Schemas
Below are the schemas for a relation and a dialog (in `dataclass` format).

```python
import typing as t

class DiscourseRelation:
    # label(s)
    label: str  # type
    sense: t.List[t.Dict[str, str]] = None
    # spans
    conn: t.List[t.Tuple[int, int]] = None
    arg1: t.List[t.Tuple[int, int]] = None
    arg2: t.List[t.Tuple[int, int]] = None
    sup1: t.List[t.Tuple[int, int]] = None
    sup2: t.List[t.Tuple[int, int]] = None
    

class Dialog:
    doc_id: str
    tokens: t.List[str]
    blocks: t.List[t.Tuple[int, int]]= None
    chunks: t.List[t.Tuple[int, int]] = None
    groups: t.List[t.Tuple[int, int]] = None
    relations: t.List[DiscourseRelation] = None
```

All spans (for a **connective**, **Arg1** and **Arg2**, **Sup1** and **Sup2**) are lists of start & end indices
with respect to `tokens`. 

A relation can have several senses. 
Each sense has the `connective` & `sense` fields; where `connective` field is only populated for Implicit relations. 

## Anonymization

The data has been anonymized at token-level using the following conversions:

| Replacement   | Freq | Description                                     |
|:--------------|-----:|:------------------------------------------------|
| `<NUM>`       |  337 | number-words; e.g. `duomilasei`                 |
| `<ORD>`       |   29 | ordinals; e.g. `quarto`                         | 
| `<DIGIT>`     |  740 | digit-words; e.g. `due`                         |
| `<CHAR>`      |   86 | letter; e.g. `C`                                |
| `<PUNC>`      |   18 | punctuation; e.g. `barra`                       |
| `<WORD>`      |   11 | a word to be masked; e.g. password, spelling    |
| `<CHARS>`     |    5 | a sequence of letters (abbreviation); e.g. `SG` |
| `<BRAND>`     |   36 | brands (hardware); e.g. `Fujitsu`               |
| `<SW>`        |  159 | software; e.g. `Windows`                        |
| `<PER>`       |  278 | person names; e.g. `Monica`                     |
| `<ORG>`       |   54 | named organizations; e.g. `CSI`                 |
| `<LOC>`       |  126 | locations; e.g. `Italia`                        |
| `<LOC.SPELL>` |   25 | locations for spelling; e.g. `Ancona`           |
| `<WD>`        |   13 | week days; e.g. `domenica`                      |
| `<MM>`        |   13 | month names; e.g. `gennaio`                     |
| `<MISC>`      |    2 | other; not covered above                        |


## Known Issues, Peculiarities and TODOs

- `070400_0020`: `conn` and `arg2` spans overlap in `Explicit` relation

- 2 sense relations (3):

  - Relation Types
    - Implicit: 3
  
  - IDs
    - `0703000001`: 2
    - `0704000001`: 1

- 0 sense relations (8):

  - Relation Types
    - Explicit: 4
    - Implicit: 3
    - AltLex: 1

  - IDs 
    - `0703000006`: 1
    - `0704000001`: 1
    - `0704000025`: 1
    - `0704000031`: 1
    - `0704000034`: 1
    - `0704000051`: 2
    - `0705000003`: 1


## References

If you use this dataset for publication, please cite the following papers:

- Sara Tonelli, Giuseppe Riccardi, Rashmi Prasad, and Aravind K. Joshi, 
  "Annotation of discourse relations for conversational spoken dialogs.",
  In Proceedings of the International Conference on Language Resources and Evaluation (LREC), 2010.

- Giuseppe Riccardi, Evgeny A. Stepanov, and Shammur Absar Chowdhury. 
  "Discourse connective detection in spoken conversations.",
  IEEE International Conference on Acoustics Speech and Signal Processing (ICASSP), 2016.
