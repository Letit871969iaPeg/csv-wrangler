# csv-wrangler

> A CLI tool for fast, opinionated CSV transformations and validation with a simple DSL.

---

## Installation

```bash
pip install csv-wrangler
```

Or with [pipx](https://pypa.github.io/pipx/) for isolated installs:

```bash
pipx install csv-wrangler
```

---

## Usage

Define your transformations in a `.wrangle` file using the built-in DSL:

```
# transform.wrangle
RENAME col_1 -> user_id
RENAME col_2 -> email
FILTER email NOT_EMPTY
VALIDATE email MATCHES ^[\w.]+@[\w.]+$
CAST user_id INT
```

Then run it against your CSV:

```bash
csv-wrangler run transform.wrangle --input data.csv --output clean.csv
```

**Other commands:**

```bash
# Validate only, no output written
csv-wrangler validate transform.wrangle --input data.csv

# Preview first 10 transformed rows
csv-wrangler preview transform.wrangle --input data.csv --rows 10
```

---

## Features

- Simple, readable DSL for defining transformations
- Fast processing backed by Python's `csv` module
- Inline validation with clear error reporting
- Supports stdin/stdout for pipeline-friendly workflows

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any significant changes.

---

## License

[MIT](LICENSE)