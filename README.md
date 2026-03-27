# A Textbook of Formal Learning Theory

**Six Paradigms, Their Characterization Theorems, and the Separations Between Them**

*Dhruv Gupta — Zetesis Labs, ARTPARK @ IISc Bangalore*

---

## What This Book Is

This is a graduate-level textbook that presents formal learning theory as a single, navigable mathematical structure. It treats six paradigms — PAC, online, Gold-style, exact, universal, and multiclass learning — within a unified framework, and devotes equal attention to the **separations** between them.

The key structural innovation is not any new theorem, but a *negative layer*: the book treats what **does not** hold — separation results with explicit witnesses, cross-paradigm analogies with their precise obstructions, and the boundaries where one framework's characterization theorem fails to generalize to another.

### The Six Paradigms

| Paradigm | Characterization | Complexity Measure | Key Reference |
|----------|------------------|--------------------|---------------|
| **PAC learning** | Fundamental Theorem (9 equiv. conditions) | VC dimension | Valiant 1984; Blumer et al. 1989 |
| **Online learning** | Littlestone's Theorem | Littlestone dimension | Littlestone 1988 |
| **Gold-style identification** | Mind-change hierarchy | Ordinal mind-change bounds | Gold 1967; Freivalds–Smith 1993 |
| **Exact learning** | Angluin's framework | Query complexity (MQ + EQ) | Angluin 1988 |
| **Universal learning** | Trichotomy theorem | Optimal learning rates | Bousquet et al. 2021 |
| **Multiclass learning** | DS dimension characterization | DS dimension | Brukhim et al. 2022 |

### The Knowledge Graph

The book is accompanied by a machine-readable concept graph encoding **142 concepts** connected by **260 typed edges** across **13 relation types**: `characterizes`, `strictly_stronger`, `does_not_imply`, `analogy`, `upper_bounds`, `lower_bounds`, `measures`, `defined_using`, `instance_of`, `restricts`, `extends_grammar`, `requires_assumption`, and `used_in_proof`.

The graph is in [`supplementary/flt_concept_graph.json`](supplementary/flt_concept_graph.json).

---

## Repository Structure

```
formal-learning-theory-book/
├── textbook/
│   ├── main.tex                  # Root document
│   ├── chapters/
│   │   ├── ch01_objects.tex      # Part I: Foundations
│   │   ├── ch02_data.tex
│   │   ├── ch03_automata.tex
│   │   ├── ch04_agents.tex       # Part II: Paradigms
│   │   ├── ch05_pac.tex
│   │   ├── ch06_online.tex
│   │   ├── ch07_gold.tex
│   │   ├── ch08_exact.tex
│   │   ├── ch09_universal.tex
│   │   ├── ch10_dimensions.tex   # Part III: Complexity Measures
│   │   ├── ch11_compression.tex
│   │   ├── ch12_generalization.tex
│   │   ├── ch13_ordinals.tex
│   │   ├── ch14_separations.tex  # Part IV: The Negative Layer
│   │   ├── ch15_analogies.tex
│   │   ├── ch16_computational.tex # Part V: Extensions
│   │   ├── ch17_extensions.tex
│   │   └── ch18_frontiers.tex
│   ├── appendices/
│   │   ├── appA_edge_inventory.tex
│   │   ├── appB_traversals.tex
│   │   ├── appC_validation.tex
│   │   └── appD_notation.tex
│   └── LICENSE
├── supplementary/
│   └── flt_concept_graph.json    # 142-node, 260-edge knowledge graph
├── scripts/
│   ├── validate_graph.py         # Schema and constraint validator (13 checks)
│   ├── validate_bibliography_links.py  # Bibliography cross-reference validator
│   ├── run_reference_tasks.py    # Executes 15 benchmark tasks against the graph
│   └── evaluate_reference_tasks.py     # Scores task outputs against gold answers
├── flt_bibliography.bib          # BibTeX bibliography (~120 entries)
├── LICENSE                       # CC BY-NC-SA 4.0
├── Makefile
├── CONTRIBUTING.md
└── README.md
```

### Book Organization

| Part | Chapters | Content |
|------|----------|---------|
| **I: Foundations** | 1–3 | Domains, concepts, hypothesis spaces, data presentations, automata |
| **II: Paradigms** | 4–9 | Each paradigm with its characterization theorem proved in full |
| **III: Complexity Measures** | 10–13 | 33 complexity measures: dimensions, compression, generalization bounds, ordinals |
| **IV: Negative Layer** | 14–15 | All separation results with proofs; analogy-obstruction pairs |
| **V: Extensions** | 16–18 | Computational hardness, multiclass/regression extensions, frontiers |

---

## Building the PDF

### Prerequisites

A full TeX Live installation (or equivalent). On Ubuntu/Debian:

```bash
sudo apt-get install texlive-full
```

On macOS with Homebrew:

```bash
brew install --cask mactex
```

### Compile

```bash
cd textbook
latexmk -pdf main.tex
```

Or manually:

```bash
cd textbook
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

The compiled PDF is not tracked in git. Releases with pre-built PDFs are available on the [Releases](../../releases) page.

---

## Validation

The knowledge graph and bibliography can be validated against the textbook content using the scripts in `scripts/`:

```bash
# Validate graph schema and constraints (13 checks)
python3 scripts/validate_graph.py supplementary/flt_concept_graph.json

# Validate bibliography cross-references
python3 scripts/validate_bibliography_links.py flt_bibliography.bib supplementary/flt_concept_graph.json

# Run benchmark tasks against the graph
python3 scripts/run_reference_tasks.py supplementary/flt_concept_graph.json

# Score task outputs
python3 scripts/evaluate_reference_tasks.py
```

See [Appendix C](textbook/appendices/appC_validation.tex) for details on what each script checks.

---

## Contributing

Contributions are welcome — errata fixes, proof clarifications, missing citations, diagram improvements, and new exercises.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to submit changes.

---

## Prerequisites for Reading

- Basic probability (concentration inequalities, Hoeffding/Markov/Chebyshev bounds)
- Basic combinatorics (growth functions, pigeonhole principle)
- Computability theory at the level of decidability and the halting problem (for Gold-style chapters)
- Mathematical maturity sufficient for ε-δ arguments

No prior machine learning background is required.

---

## License

This work is licensed under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-nc-sa/4.0/).

You are free to share and adapt this material for non-commercial purposes, with attribution and under the same license.

---

## Citation

```bibtex
@book{gupta2026flt,
  title     = {A Textbook of Formal Learning Theory: Six Paradigms,
               Their Characterization Theorems, and the Separations Between Them},
  author    = {Gupta, Dhruv},
  year      = {2026},
  publisher = {Zetesis Labs, ARTPARK @ IISc Bangalore},
  url       = {https://github.com/Zetetic-Dhruv/formal-learning-theory-book}
}
```

---

## Related

- [Formal-Learning-Theory](https://github.com/Zetetic-Dhruv/Formal-Learning-Theory) — The companion knowledge graph repository with validation scripts and benchmark tasks
