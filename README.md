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
  "blocks": "list of token start & end indices for blocks in text file (tab-separated)",
  "groups": "list of token start & end indices for groups in text file (newline-separated)",
  "relations": "list of discourse relations"
}
```

For example (reduced):

```json
{
  "DOC_ID": "0703000001",
  "tokens": [
    "helpdesk", "buongiorno", "sono", "<PER>",
    "s\u00ec", "sono", "<PER>", "un", "collega",
    "ho", "il",
    "PC",
    "che", "presumibilmente", "non", "funziona", "da",
    "s\u00ec", "stamattina"
  ],
  "blocks": [[0, 4], [4, 9], [9, 11], [11, 12], [12, 17]],
  "groups": [[0, 4], [4, 17]],
  "relations": [
    {
      "label": "Implicit",
      "sense": "Expansion.Conjunction",
      "conns": "e",
      "conn": [],
      "arg1": [[5, 9]],
      "arg2": [[9, 17], [18, 19]],
      "sup1": [],
      "sup2": []
    },
    {
      "label": "Explicit",
      "sense": "Expansion.Restatement.Equivalence",
      "conn": [[59, 60]],
      "arg1": [[5, 7]],
      "arg2": [[60, 63]],
      "sup1": [],
      "sup2": []
    },
    {
      "label": "AltLex",
      "sense": "Expansion.Restatement",
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
    sense: str  # relation sense
    conns: str  # connective string (for Implicit)
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
    groups: t.List[t.Tuple[int, int]] = None
    relations: t.List[DiscourseRelation] = None
```

## Spans

A Discourse Relation can contain 5 spans: a discourse **connective** (`conn`), 
its **arguments** (`arg1` and `arg2`), and supplementary materials to the arguments (`sup1` and `sup2`).
Each span can be composed of 0 or more non-adjacent segments. 
Consequently, all spans are lists of start & end indices with respect to `tokens`;
e.g. `[[141, 144], [151, 154], [169, 171]],`

## LUNA Relation Types (Labels)

Since LUNA is following PDTB format, Discourse Relation types are the same.
The distribution is given below.

| Type     |   ALL |   TRN |   DEV |   TST |
|:---------|------:|------:|------:|------:|
| Explicit | 1,052 |   659 |   135 |   258 |
| Implicit |   490 |   294 |    74 |   122 |
| AltLex   |    11 |     8 |     2 |     1 |
| EntRel   |    56 |    33 |     7 |    16 |


## LUNA Relation Senses 

A Discourse Relation can have several senses with respect to the Relation Type:

- `Explicit` relations can have only 2 senses.
- `Implicit` relations can have up to 4 senses: 2 connectives with 2 senses each.
- `AltLex` relations are as `Explicit` relations.
- `EntRel` relations have no senses.

The observed sense counts are the following:

- `0` - no sense (errors)
- `1s` - 1 sense
- `2s` - 2 senses
- `2c` - 2 connectives, 1 sense each

| Type     |   ALL |   0 |    1s |  2s |  2c |
|:---------|------:|----:|------:|----:|----:|
| Explicit | 1,052 |   4 | 1,045 |   3 |  NA |
| Implicit |   490 |   3 |   481 |   3 |   3 |
| AltLex   |    11 |   1 |    10 |  NA |  NA |
| EntRel   |    56 |  NA |    NA |  NA |  NA | 


### Relation Sense Selection

Since the amount of discourse relations having a second sense is very little 
(3 `Explicit` & 3 `Implicit` with a second sense and 3 `Implicit` with a second connective);
all the discourse relations have been "simplified" to have exactly 1 sense (or 0, if missing).

In case more than 1 sense is available, the selected sense is the first one.
For `Implicit` 2 connective relations it is the 1st sense of the 1st connective.

### Relation Sense Levels
LUNA (and PDTB) Discourse Relations Senses are 3+ level:
e.g. `Comparison.Concession.Epistemic concession`.
It is often the case that relations are annotated up to a certain level;
i.e. not all relations have all 3 levels. 

#### Level 1 Senses

PDTB has 4 Level 1 senses: `Comparison`, `Contingency`, `Expansion` and `Temporal`.
LUNA adds 3 more which have only 1 level: 

- `Discourse Marker`
- `Interrupted`
- `Repetition`

While `Interrupted` and `Repetition` senses are quite frequent, `Discourse Marker` appears only once.


| Sense            | Explicit | Implicit | AltLex |
|:-----------------|---------:|---------:|-------:|
| Comparison       |      187 |       47 |      0 |
| Contingency      |      462 |      106 |      3 |
| Expansion        |      213 |      161 |      4 |
| Temporal         |      156 |       64 |      0 |
| Interrupted      |       29 |        1 |      0 |
| Repetition       |        0 |      108 |      0 |
| Discourse Marker |        1 |        0 |      0 |
| MISSING          |        4 |        3 |      1 |


#### Level 2 Senses

Even though mose relations have level 2 sense, a relation can have a level 1 sense only.


#### Level 3+ Senses

The 3rd level further categorizes L2 relations into the following types:
(as `Comparison.Concession.Epistemic concession`, `Contingency.Cause.Semantic cause`, etc.).
Refer to Tonelli et al. (2010) for further detail.

- Epistemic
- Inferential
- Pragmatic
- Propositional
- Semantic
- Speech act


`Temporal` sense has no 3rd level, i.e. only

- `Temporal.Asynchronous`
- `Temporal.Synchrony`

`Expansion.Restatement` on level 3 is further categorized into:

- `Expansion.Restatement.Equivalence`
- `Expansion.Restatement.Specification`


#### Sense Counts

The table below contains sense counts as they appear in the data.

| Sense                               | Explicit | Implicit | AltLex |
|:------------------------------------|---------:|---------:|-------:|
| Comparison (no L2)                  |        1 |        0 |      0 |
| Comparison.Concession               |      144 |       27 |      0 |
| Comparison.Contrast                 |       42 |       20 |      0 |
| Contingency (no L2)                 |        1 |        0 |      0 |
| Contingency.Cause                   |      265 |       88 |      2 |
| Contingency.Condition               |      124 |        8 |      1 |
| Contingency.Goal                    |       73 |       10 |      1 |
| Expansion (no L2)                   |        1 |        0 |      0 |
| Expansion.Alternative               |       28 |        3 |      1 |
| Expansion.Conjunction               |      111 |       70 |      1 |
| Expansion.Instantiation             |        8 |        3 |      1 |
| Expansion.Restatement (no L3)       |        4 |        8 |      1 |
| Expansion.Restatement.Equivalence   |       25 |       22 |      0 |
| Expansion.Restatement.Specification |       36 |       55 |      2 |
| Temporal (no L2)                    |        0 |        0 |      0 |
| Temporal.Asynchronous               |      128 |       55 |      3 |
| Temporal.Synchrony                  |       28 |        9 |      3 |
| Interrupted                         |       29 |        1 |      0 |
| Repetition                          |        0 |      108 |      0 |
| Discourse Marker                    |        1 |        0 |      0 |
| MISSING                             |        4 |        3 |      1 |


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



## Notes, Known Issues, Peculiarities and TODOs

- `0704000020`: `conn` and `arg2` spans overlap in `Explicit` relation (DONE)

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
