# Salesforce 添付ファイル抽出バッチ仕様書（ローカル実行版）

## 1. 概要

Salesforceから特定レコードに紐づく添付ファイルを抽出し、レコードIDごとのフォルダを作成して、ファイル名・拡張子を保ったままローカルに保存するバッチ処理をPythonで実装する。

## 2. 処理対象

- 抽出対象：任意のSalesforceオブジェクト（SOQLで指定）
- 添付ファイルの取得は `ContentVersion` を通じて行う
- 保存対象は以下の関係で構成される：

```
対象レコード（任意） 
└─ ContentDocumentLink（LinkedEntityId = レコードID）
   └─ ContentDocument（Id = ContentDocumentId）
      └─ ContentVersion（最新バージョンを取得）
```

### 2.1 取得フィールド

- `ContentDocumentLink`: `ContentDocumentId`, `LinkedEntityId`
- `ContentDocument`: `Id`
- `ContentVersion`: `Id`, `Title`, `FileExtension`, `VersionData`

## 3. 入力情報の管理

### 3.1 SOQL管理

- `soql/` ディレクトリに `.soql` ファイルを配置
- 実行時にファイル名を引数または環境変数で指定して読み込む
- SOQLにはコメント行・空行を含んでよい

#### 実行形式（例）:
```bash
python main.py --soql soql/activeAccounts.soql
```

### 3.2 Salesforce認証情報

- `.env` ファイルで管理（Git管理対象外）
- `.env.sample` をリポジトリに含めること
- 使用環境変数：
```env
SF_USERNAME=
SF_PASSWORD=
SF_SECURITY_TOKEN=
SF_DOMAIN=login
```

## 4. 出力仕様

### 4.1 保存形式

- 出力先は任意のパスを指定可能（CLI引数または環境変数）
- 明示されない場合、デフォルトで `output/` ディレクトリを作成
- サブディレクトリ名：対象レコードのID（例：`001ABC000012345`）
- ファイル名：Salesforce上のファイル名＋拡張子を維持
- 同名ファイルが存在する場合は自動的に `(1)`, `(2)` を付加しリネーム保存

#### 出力ディレクトリ指定例：
```bash
python main.py --soql soql/activeAccounts.soql --output-dir ./exports/
```

## 5. バッチ処理の流れ

1. 実行時引数または環境変数で SOQL ファイルを特定
2. Salesforce 認証を行い、SOQL を実行して対象レコードID群を取得
3. 各レコードに対して関連する `ContentDocumentLink` を取得
4. それに紐づく `ContentDocument` → 最新の `ContentVersion` を取得
5. 出力先にレコードIDのディレクトリを作成（存在しない場合は生成）
6. ファイル名を確認して保存（必要に応じてリネーム）
7. 成功ログ・失敗ログをCSVで出力

## 6. API制限対応

- 2000件を超えるレコードに対応するため、`nextRecordsUrl` を使用したページング処理を行う
- 取得数に応じて必要に応じてスリープを挿入
- 再試行処理は行わず、失敗はスキップしエラーログへ記録する

## 7. ログ出力仕様

### 7.1 出力場所・ファイル名

- 出力先：`logs/`
- 各実行ごとにタイムスタンプ（秒単位）をファイル名に付加  
```
logs/success_YYYYMMDD_HHMMSS.csv
logs/error_YYYYMMDD_HHMMSS.csv
```

### 7.2 出力形式

- CSV（UTF-8、BOMなし、ヘッダーあり）
- ファイル単位で記録

### 7.3 ログ項目定義（共通）

| 項目名             | 内容                                                             |
|--------------------|------------------------------------------------------------------|
| record_id          | 添付元レコードのID（例: `001ABC000012345`）                     |
| content_version_id | `ContentVersion.Id`                                              |
| filename           | Salesforce上のファイル名（例: `invoice.pdf`）                   |
| saved_filename     | 実際に保存されたファイル名（リネームされている可能性あり）     |
| saved_path         | ファイルの保存先（相対パス）                                     |
| status             | `success` または `error`                                        |
| message            | `"OK"` または エラーメッセージ                                  |

## 8. テスト方針（unittest）

### 8.1 テスト環境制約への対応

- Salesforce API は実行せず、**モックレスポンス**を使用してテストを行う
- テスト切り替え用の環境変数または引数を設ける（例：`--test-mode`）

### 8.2 テスト対象（正常系）

| テスト項目               | 内容                                                                 |
|--------------------------|----------------------------------------------------------------------|
| SOQLファイル読み込み     | コメント行・空行含めて正しくパースされるか                          |
| Salesforce APIモック     | モックデータにより一連の処理が完了するか                            |
| ファイル保存処理         | 正しい場所・名前で保存されるか、重複時にリネームされるか            |
| 成功ログ出力             | success ログファイルが正しく作成されているか                        |
| 失敗ログ出力（擬似）     | 一部失敗を想定し error ログが出力されているか（例：書込不可等）     |

### 8.3 異常系テスト

- 実運用パイロット中に発生したケースを基に、随時テストケースを追加する

## 9. ディレクトリ構成（例）

```
project-root/
├── main.py
├── salesforce_client.py
├── file_saver.py
├── soql/
│   └── activeAccounts.soql
├── logs/
├── output/
├── tests/
│   └── test_main.py
├── .env
├── .env.sample
└── requirements.txt
```

## 10. 補足事項

- ディレクトリ名はレコードID固定のためエスケープ処理は不要
- 権限による非表示ファイル等は考慮しない（実行ユーザーの権限に委ねる）
- 冗長なリトライ処理は行わない
- 将来的な拡張（Cloud Storage保存やリアルタイムトリガー）は別仕様として設計予定
