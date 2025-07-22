import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency for tests
    def load_dotenv(*_args, **_kwargs):
        return None

from salesforce_client import SalesforceClient
from file_saver import save_file, ensure_directory


def load_soql(path: Path) -> str:
    lines: List[str] = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('--') or stripped.startswith('#'):
                continue
            lines.append(stripped)
    return ' '.join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Salesforce file replicator')
    parser.add_argument('--soql', required=True, help='Path to SOQL file')
    parser.add_argument('--output-dir', default='output/', help='Directory to save files')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode with mock data')
    return parser.parse_args()


def load_env() -> dict:
    load_dotenv()
    return {
        'username': os.getenv('SF_USERNAME'),
        'password': os.getenv('SF_PASSWORD'),
        'security_token': os.getenv('SF_SECURITY_TOKEN'),
        'domain': os.getenv('SF_DOMAIN', 'login')
    }


def open_log_files() -> (csv.writer, csv.writer, open, open):
    ensure_directory(Path('logs'))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    success_path = Path('logs') / f'success_{timestamp}.csv'
    error_path = Path('logs') / f'error_{timestamp}.csv'
    success_fp = open(success_path, 'w', newline='', encoding='utf-8')
    error_fp = open(error_path, 'w', newline='', encoding='utf-8')
    success_writer = csv.writer(success_fp)
    error_writer = csv.writer(error_fp)
    headers = ['record_id', 'content_version_id', 'filename', 'saved_filename', 'saved_path', 'status', 'message']
    success_writer.writerow(headers)
    error_writer.writerow(headers)
    return success_writer, error_writer, success_fp, error_fp


def main():
    args = parse_args()
    env = load_env()
    soql_file = Path(args.soql)
    soql = load_soql(soql_file)
    output_dir = Path(args.output_dir)
    ensure_directory(output_dir)

    client = SalesforceClient(
        username=env['username'],
        password=env['password'],
        security_token=env['security_token'],
        domain=env['domain'],
        test_mode=args.test_mode
    )

    success_writer, error_writer, success_fp, error_fp = open_log_files()

    try:
        records = client.query(soql)
        for rec in records:
            record_id = rec.get('Id')
            links = client.get_content_document_links(record_id)
            for link in links:
                doc_id = link.get('ContentDocumentId')
                version = client.get_latest_content_version(doc_id)
                if not version:
                    error_writer.writerow([record_id, '', '', '', '', 'error', 'ContentVersion not found'])
                    continue
                filename = f"{version.get('Title')}.{version.get('FileExtension')}" if version.get('FileExtension') else version.get('Title')
                data = client.download_content_version_data(version)
                try:
                    saved_path = save_file(output_dir / record_id, filename, data)
                    success_writer.writerow([
                        record_id,
                        version.get('Id'),
                        filename,
                        saved_path.name,
                        str(saved_path.relative_to(Path.cwd()) if saved_path.is_relative_to(Path.cwd()) else saved_path),
                        'success',
                        'OK'
                    ])
                except Exception as e:
                    error_writer.writerow([
                        record_id,
                        version.get('Id'),
                        filename,
                        '',
                        '',
                        'error',
                        str(e)
                    ])
    finally:
        success_fp.close()
        error_fp.close()


if __name__ == '__main__':
    main()
