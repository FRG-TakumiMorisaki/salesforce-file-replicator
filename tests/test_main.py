# Copyright (c) 2025
# This is a proprietary solution. Redistribution of modified versions is prohibited.
# Open-source dependency licenses are documented in the README table.

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from main import load_soql, main
from salesforce_client import SalesforceClient


def test_load_soql(tmp_path):
    soql_file = tmp_path / 'query.soql'
    soql_file.write_text('\n'.join([
        '-- comment',
        'SELECT Id',
        'FROM Account',
        '',
        '# another comment'
    ]), encoding='utf-8')
    assert load_soql(soql_file) == 'SELECT Id FROM Account'


def create_mock_client(tmpdir):
    data = {
        'query': [{'Id': '0011'}],
        'links': {'0011': [{'ContentDocumentId': 'cd1'}]},
        'versions': {'cd1': {'Id': 'cv1', 'Title': 'test', 'FileExtension': 'txt', 'VersionData': b'data'}}
    }
    client = SalesforceClient(username='', password='', security_token='', test_mode=True, mock_data=data)
    return client


def test_main_flow(tmp_path, monkeypatch):
    soql_file = tmp_path / 'q.soql'
    soql_file.write_text('SELECT Id FROM Account', encoding='utf-8')
    output_dir = tmp_path / 'out'
    output_dir.mkdir(parents=True, exist_ok=True)

    mock_client = create_mock_client(tmp_path)

    def mock_init(*args, **kwargs):
        return mock_client

    with mock.patch('main.SalesforceClient', side_effect=mock_init):
        with mock.patch('main.open_log_files') as mock_logs:
            success_path = output_dir / 'success.csv'
            error_path = output_dir / 'error.csv'
            success_fp = open(success_path, 'w', newline='', encoding='utf-8')
            error_fp = open(error_path, 'w', newline='', encoding='utf-8')
            success_writer = mock.Mock()
            error_writer = mock.Mock()
            mock_logs.return_value = (success_writer, error_writer, success_fp, error_fp)
            args = ['--soql', str(soql_file), '--output-dir', str(output_dir)]
            with mock.patch('sys.argv', ['main.py'] + args):
                main()
            assert (output_dir / '0011' / 'test.txt').exists()
            success_writer.writerow.assert_called()
