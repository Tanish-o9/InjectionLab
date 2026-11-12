# Contributing to InjectionLab

Thank you for your interest in improving InjectionLab! We welcome contributions to attack templates, mutation strategies, defense architectures, and benchmark evaluations.

---

## Getting Started

1. **Fork and Clone** the repository:
   ```bash
   git clone https://github.com/Tanish-o9/InjectionLab.git
   cd InjectionLab
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Verify the test suite**:
   ```bash
   python -m pytest -v tests
   ```

---

## Adding New Attack Templates

1. Open `attacks/templates.py`.
2. Add your attack tuple following the format:
   ```python
   (attack_type, [channels], "Template payload text with optional {addr} placeholder.")
   ```
   - `attack_type`: `"direct"`, `"indirect"`, or `"exfiltration"`
   - `channels`: `["user"]` (user query) or `["doc"]` (poisoned retrieved document)
3. Regenerate the dataset:
   ```bash
   python -m attacks.build_attacks
   ```

---

## Adding New Defenses

1. Implement your defense logic in a new module inside `defenses/`.
2. Register the defense name in `config.py` under `ALL_DEFENSES` and `DEFENSE_CONFIGS`.
3. Wire the defense hook into `target/app.py` or `target/prompts.py`.
4. Add corresponding test cases in `tests/test_comprehensive.py`.

---

## Pull Request Guidelines

- Ensure all existing and new tests pass: `python -m pytest tests`.
- Keep commits atomic and descriptive following conventional commits (`feat:`, `fix:`, `docs:`, `test:`).
- Open a PR against the `main` branch.
