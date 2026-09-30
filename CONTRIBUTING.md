# Contributing

Contributions are welcome.

## Development setup

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
agent-hub-core check-schemas
agent-hub-core conformance
python scripts/audit_public_tree.py
python -m build
```

## Pull requests

Keep changes focused. Protocol changes should include:

- schema updates;
- validated examples;
- semantic validation when JSON Schema alone is insufficient;
- unit tests;
- conformance updates when routing or lifecycle semantics change;
- documentation.

Do not add real credentials, account identifiers, private repository names, or
deployment-specific secrets to fixtures.
