# Contributing

Thank you for your interest in improving this textbook. Contributions of all kinds are welcome.

## Types of Contributions

### Errata and Corrections
- Typos, broken cross-references, notation inconsistencies
- Mathematical errors in proofs or definitions
- Missing or incorrect citations

### Content Improvements
- Proof clarifications or alternative proofs
- Additional examples or exercises
- Improved TikZ diagrams
- New or improved computational illustrations

### Structural Contributions
- Knowledge graph corrections (missing edges, wrong relation types)
- Build system and CI improvements
- Issue/PR template improvements

## How to Contribute

1. **Fork** the repository and create a feature branch from `main`.
2. **Make your changes** — keep commits focused and atomic.
3. **Test the build** — ensure the PDF compiles cleanly:
   ```bash
   cd textbook && latexmk -pdf main.tex
   ```
4. **Open a Pull Request** against `main` with:
   - A clear title describing the change
   - The chapter(s) and definition/theorem numbers affected
   - For mathematical changes, a brief justification

## Style Conventions

### LaTeX
- Use the macros defined in `main.tex` (e.g., `\VC`, `\Ldim`, `\DSdim`, `\E`, `\Pr`, `\risk`, `\emprisk`).
- Theorem environments: `defn`, `thm`, `prop`, `cor`, `lemma`, `claim`, `example`, `remark`, `openprob`.
- Colored boxes: `separation`, `traversal`, `obstbox`, `historical`, `computational`, `graphnode`.
- Cross-reference with `\cref{}` (via `cleveref`).
- Use `\edge{A}{relation}{B}` for inline graph edges.

### Commit Messages
- Start with the chapter or component: `ch05: fix Sauer-Shelah proof typo`
- For cross-cutting changes: `repo: update .gitignore`
- Keep the first line under 72 characters.

### Knowledge Graph
- The graph is in `flt_concept_graph.json` at the repo root.
- Valid relation types: `characterizes`, `strictly_stronger`, `does_not_imply`, `analogy`, `upper_bounds`, `lower_bounds`, `measures`, `defined_using`, `instance_of`, `restricts`, `extends_grammar`, `requires_assumption`, `used_in_proof`.
- Changes to the graph should reference the relevant textbook theorem or definition.

## Reporting Issues

Use [GitHub Issues](../../issues) for:
- **Errata**: mathematical errors, typos, broken references
- **Enhancements**: suggestions for new examples, exercises, or diagrams
- **Questions**: clarification requests about content or structure

Please include the chapter number and definition/theorem number when reporting errata.

## License

By contributing, you agree that your contributions will be licensed under the same [CC BY-NC-SA 4.0](LICENSE) license as the rest of the work.
