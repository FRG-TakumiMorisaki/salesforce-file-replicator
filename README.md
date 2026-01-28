# Salesforce File Replicator

This project downloads files attached to Salesforce records and stores them in a local directory structure. Records are selected via a SOQL query, and each attachment is saved under a folder named with the record ID. Execution logs are written to CSV files.

## Open Source Usage & Distribution

This project leverages open-source software dependencies listed in `requirements.txt`. Redistribution of modified versions is prohibited, as this remains our proprietary solution. The following table is provided so customers can understand which licenses are used.

| パッケージ | ライセンス | 根拠 |
| --- | --- | --- |
| simple-salesforce (>=1.12.2) | Apache-2.0 | PyPI の “License Expression: Apache-2.0” 記載 |
| python-dotenv | BSD-3-Clause | PyPI の “License Expression: BSD-3-Clause” 記載 |
| pytest | MIT | 公式ドキュメント/リポジトリで MIT と明記 |

## Features

- Read SOQL statements from `.soql` files
- Authenticate to Salesforce using credentials in `.env`
- Download files from `ContentVersion`
- Automatically rename duplicate filenames
- Output success and error logs in `logs/`
- Optional test mode that uses mock data (no API calls)

## Quick Start

1. Copy `.env.sample` to `.env` and fill in your Salesforce credentials.

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a query file in `soql/` (e.g., `query.soql`). Example:

```sql
SELECT Id FROM Account WHERE Active__c = true
```

4. Run the tool:

```bash
python main.py --soql soql/query.soql --output-dir output/
```

Files will be saved under `output/<record_id>/`. Logs will appear in the `logs/` directory.

### Test Mode

For unit tests or dry runs, you can execute with `--test-mode` to avoid real API calls.

```bash
python main.py --soql soql/query.soql --test-mode
```

## Repository Layout

- `main.py` - command line entry point
- `salesforce_client.py` - wrapper for Salesforce API
- `file_saver.py` - utilities for writing files
- `design.md` - detailed design document (Japanese)
- `soql/` - place SOQL query files here
- `tests/` - unit tests (use `pytest`)

## Running Tests

```bash
pytest
```
