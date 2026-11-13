# Documentation claim auditor

An offline, read-only static auditor compares documented claims about the checked
feature with source call patterns. It never executes inspected source or contacts
an external service. Runtime dependencies are limited to the standard library.

## Use

```sh
python3 -m pip install .
pay-stub-extraction-claim-audit --version
pay-stub-extraction-claim-audit audit . --json
python3 -m pay_stub_extraction_claim_audit audit . --fail-on medium
pay-stub-extraction-claim-audit audit . --ignore vendor --ignore generated --verbose
python3 -m unittest discover
python3 -m build
```

The optional repository argument defaults to the current directory. Each ignore
option takes one relative path prefix, matching whole path components. The default
failure threshold is high; medium also fails on findings supported only by tests.
Exit status is 0 for success at the selected threshold, 2 for findings at or above
it, and 1 for usage or input errors. A medium finding can therefore produce status
0 while the report verdict remains FAIL.

JSON reports contain verdict, findings, production_evidence and test_evidence.
Every finding contains id, severity, message and docs. Severity values are uppercase.
There is at most one finding for an affirmative claim and one for a denial.

```text
documented-pay-stub-extraction-claim-false HIGH
  No production evidence; MEDIUM when evidence exists only in tests.
documented-no-pay-stub-extraction-claim-false HIGH
  A documented denial contradicts production evidence.
```

## Inspection rules

The auditor reads the root README and Markdown files with a docs path component.
It excludes backtick and tilde fenced blocks with up to three leading spaces;
inline code counts. Blank lines separate paragraphs. Matching lowercases text,
expands negative contractions, replaces hyphens with spaces and collapses
whitespace. Exact phrases use word boundaries, longest first with alphabetical
ties. Denial spans are removed before affirmative matching.

Source files are parsed as syntax trees, never executed. Symlinked files and
directories are excluded. Source beneath fixtures, docs or examples contributes
no evidence. Source in tests directories or with a test filename contributes only
test evidence. Invalid syntax contributes none. A claim without any source still
fails; a denial without source passes. Imports, bindings and local definitions
are inspected within each module. Assignments, annotated assignments and context
manager targets shadow imported names. Local functions, methods and classes
shadow route names. Pairs cannot be assembled across modules.

The checked operation concerns structured employee, employer, pay-period,
pay-date, gross/net compensation, deductions, withheld taxes and cumulative fields
from earnings documents. Recognized patterns are these pairs and generic names:

```text
Azure: DocumentAnalysisClient or DocumentIntelligenceClient construction,
with begin_analyze_document or begin_analyze_document_from_url,
first positional argument or model_id keyword exactly "prebuilt-payStub.us".
Import gate: azure.ai.formrecognizer or azure.ai.documentintelligence.
Mindee: Client construction and parse passing PayslipV2 or PayslipV3,
as a positional or keyword Name or Attribute. Import gate: mindee.
Generic Attribute calls on any base, or directly imported Name calls:
extract_pay_stub extract_pay_stubs parse_pay_stub parse_pay_stubs
extract_payslip extract_payslips parse_payslip parse_payslips
extract_paystub extract_paystubs parse_paystub parse_paystubs
extract_payroll_stub extract_payroll_stubs parse_payroll_stub parse_payroll_stubs
extract_pay_stub_data parse_pay_stub_data pay_stub_extraction pay_stub_extractor
pay_stub_parser payslip_extraction extract_payroll_stub_data parse_payroll_stub_data
```

## Differentiation

The neighbouring invoice/receipt/bank-check/bank-statement/tax-form extraction
families inspect other document types and their respective operations. OCR checks
text recognition and table extraction checks table structure. Neither establishes
the checked capability: a flat text dump or a table does not establish structured
compensation fields. ID documents and document question answering are distinct too.

## Honest limitations

Matching is static pattern recognition, not semantic judgement. Dead code counts;
unsupported alias chains are missed. Exact vocabulary misses paraphrases and denial
handling depends on a fixed list. An operation in one module cannot complete a
pair in another. Bare imports, references, strings and comments do not count.

The claim vocabulary can also describe blank template rendering, blank downloads,
viewing documents, employee portals, download links, filename or URL conventions,
or records inside a payroll run. Those meanings can cause false positives.
Generic named calls may parse numbers typed by a user rather than process a
document; they still count. Manual field assembly using regular expressions on
OCR text and plain string splitting without a listed call are missed. External
CLIs invoked through subprocess are excluded, so thin wrappers can fail.

The recognized French product endpoint returns employee, employer, period,
gross/net compensation and deduction fields; its geographic scope does not
invalidate its evidence. Cloud client patterns establish neither configured
credentials nor successful API execution.

```text
Mindee PayslipV2 / PayslipV3: French endpoint payslip_fra.
TypePayslipV2 / TypePayslipV3 are not supported legacy names.
Mindee parse with InvoiceV4, ReceiptV5, PassportV1, FinancialDocumentV1,
BankCheckV1, BankAccountDetailsV2 or CustomV1 does not count.
Azure Document Intelligence, Mindee and Veryfi are cloud APIs.
```

Model identifiers are exact and case-sensitive. The required suffix and capital
letter matter; a lowercase language-support table label is not the model ID.
Other document models do not establish the checked feature.

```text
Counts: prebuilt-payStub.us
Does not count: prebuilt-payStub, prebuilt-paystub.us
Other excluded models: prebuilt-invoice, prebuilt-receipt, prebuilt-layout,
prebuilt-read, prebuilt-idDocument, prebuilt-check.us, prebuilt-tax.us,
prebuilt-bankStatement.us
```

The following provider has no dedicated operation for the checked feature in
its inspected SDK. Generic configurable operations and generic receipt/invoice
operations do not count. Its tax forms, checks, statements and business cards
belong to other document types; classification, retrieval and management also
provide no evidence.

```text
Veryfi SDK 5.1.0: no pay-stub method.
Excluded: process_any_document / process_any_document_url (AnyDocs),
process_document / process_document_url (receipts and invoices),
process_w2_document / process_w9_document / process_w8_document (tax forms),
process_check / process_check_url / process_check_with_remittance /
process_check_with_remittance_url (checks),
process_bank_statement_document / process_bank_statement_document_url,
process_bussines_card_document (business cards), classify_document,
get_w2s / get_w2 / delete_w2 / get_w9s / get_w9 / delete_w9 /
get_w8s / get_w8 / delete_w8 / get_bank_statements / get_checks.
All other Veryfi methods are excluded as well.
```

Generic document/expense analysis, plain text reading, OCR, spreadsheet reading
and table operations alone provide no evidence. The following are examples:

```text
Textract: analyze_document, analyze_expense, start_document_analysis,
get_expense_analysis. Textract has no dedicated operation for this feature.
pdfplumber / fitz / pypdf / PyPDF2 / pdfminer: extract_text
pytesseract: image_to_string; pandas: read_csv / read_excel
camelot: read_pdf; tabula: read_pdf / convert_into
pdfplumber: extract_table / extract_tables / find_table / find_tables
fitz: find_tables; re.search / re.findall plus manual field assembly
subprocess calls to mindee, veryfi or any other external CLI
```

Claims about pay dates, pay rates or pay history, running or calculating payroll,
and operations on neighbouring document types are outside the phrase vocabulary.

```text
Not claim phrases: extract pay dates / extract pay rates / extract pay history;
process payroll / calculate payroll / run payroll;
extract invoices / invoice extraction; extract receipts / receipt extraction;
extract passports / passport extraction; extract bank checks / check extraction;
extract bank statements / statement extraction;
extract tax forms / extract w2 forms / 1099 extraction.
```

The package is distributed under the MIT license.
