import ast
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from pay_stub_extraction_claim_audit import phrases
from pay_stub_extraction_claim_audit.audit import audit, evidence, claims
from pay_stub_extraction_claim_audit.__main__ import main

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
    def put(self, name, text):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path
    def cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
            code = main(['audit', str(self.root), *args])
        return code, out.getvalue()
    def test_bad(self):
        self.put('README.md', 'We extract pay stubs.')
        result = audit(self.root)
        self.assertEqual(result['findings'][0]['id'], 'documented-pay-stub-extraction-claim-false')
        self.assertEqual(result['findings'][0]['severity'], 'HIGH')
        self.assertEqual(self.cli()[0], 2)
    def test_good(self):
        self.put('README.md', 'We extract pay stubs.')
        self.put('app.py', 'x.extract_pay_stub(doc)')
        self.assertEqual(self.cli()[0], 0)
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
    def test_denial(self):
        self.put('README.md', 'Does not extract pay stubs.')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
        self.put('app.py', 'x.extract_pay_stub(doc)')
        f = audit(self.root)['findings'][0]
        self.assertEqual(f['id'], 'documented-no-pay-stub-extraction-claim-false')
        self.assertEqual(f['severity'], 'HIGH')
        self.assertEqual(self.cli()[0], 2)
    def test_test_only(self):
        self.put('README.md', 'extract pay stubs')
        self.put('tests/test_app.py', 'x.extract_pay_stub(doc)')
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'MEDIUM')
        self.assertEqual(self.cli()[0], 0)
        self.assertEqual(self.cli('--fail-on', 'medium')[0], 2)
    def test_no_claim(self):
        self.put('README.md', 'A utility.')
        self.put('app.py', 'x.extract_pay_stub(doc)')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
    def test_json(self):
        self.put('README.md', 'extract pay stubs')
        code, text = self.cli('--json')
        self.assertEqual(code, 2)
        result = json.loads(text)
        self.assertEqual(result['verdict'], 'FAIL')
        self.assertIn('message', result['findings'][0])
    def test_split_modules(self):
        self.put('README.md', 'extract pay stubs')
        self.put('one.py', 'import mindee\nc = mindee.Client()')
        self.put('two.py', 'c.parse(PayslipV3, doc)')
        self.assertEqual(self.cli()[0], 2)
    def test_symlinks(self):
        self.put('README.md', 'extract pay stubs')
        target = self.put('fixtures/source.py', 'x.extract_pay_stub(doc)')
        (self.root/'app.py').symlink_to(target)
        (self.root/'linked').symlink_to(target.parent, target_is_directory=True)
        self.assertEqual(self.cli()[0], 2)
    def test_docs_and_ignore(self):
        self.put('nested/docs/a.md', 'extract pay stubs')
        self.assertEqual(self.cli()[0], 2)
        self.assertEqual(self.cli('--ignore', 'nested/docs')[0], 0)
        self.assertEqual(self.cli('--ignore', 'nested/doc')[0], 2)
    def test_usage(self):
        for args in ([], ['oops'], ['audit', '--fail-on', 'HIGH'], ['audit', '--ignore', 'a', 'b', 'c']):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                main(args)
            self.assertEqual(caught.exception.code, 1)
    def test_bad_path(self):
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['audit', str(self.root/'missing')]), 1)
    def test_entry_points(self):
        result = subprocess.run([sys.executable, '-m', 'pay_stub_extraction_claim_audit', '--version'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), '0.1.0')
    def test_console_entry(self):
        import shutil
        executable = shutil.which('pay-stub-extraction-claim-audit')
        if executable:
            result = subprocess.run([executable, '--version'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), '0.1.0')
        else:
            project = Path(__file__).resolve().parents[1]/'pyproject.toml'
            self.assertIn('pay-stub-extraction-claim-audit = "pay_stub_extraction_claim_audit.__main__:main"', project.read_text())
            with contextlib.redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit) as caught:
                main(['--version'])
            self.assertEqual(caught.exception.code, 0)
            self.assertEqual(output.getvalue().strip(), '0.1.0')
    def test_phrase_oracle(self):
        tree = ast.parse(Path(phrases.__file__).read_text())
        values = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)}
        self.assertEqual(values['PAYSTUBEXTRACTION'], ('pay stub extraction', 'extract pay stubs', 'extracts pay stubs', 'extracting pay stubs', 'extract pay stub', 'extracts pay stub', 'extracting pay stub', 'pay stub parsing', 'pay stub parser', 'parse pay stubs', 'parses pay stubs', 'parse pay stub', 'parses pay stub', 'payslip extraction', 'extract payslips', 'extracts payslips', 'extracting payslips', 'extract payslip', 'extracts payslip', 'extracting payslip', 'payslip parsing', 'payslip parser', 'parse payslips', 'parses payslips', 'parse payslip', 'parses payslip', 'paystub extraction', 'extract paystubs', 'extracts paystubs', 'extracting paystubs', 'extract paystub', 'extracts paystub', 'extracting paystub', 'paystub parsing', 'paystub parser', 'parse paystubs', 'parses paystubs', 'parse paystub', 'parses paystub', 'payroll stub extraction', 'extract payroll stubs', 'extracts payroll stubs', 'extracting payroll stubs', 'pay stub data extraction', 'extract pay stub data', 'pay stub field extraction', 'payroll stub parsing', 'parse payroll stubs', 'pay stub document extraction', 'extract pay stub documents'))
        self.assertEqual(values['NOPAYSTUBEXTRACTION'], ('no pay stub extraction', 'does not extract pay stubs', 'does not extract pay stub', 'does not support pay stub extraction', 'without pay stub extraction', 'no payslip extraction', 'does not extract payslips', 'does not extract payslip', 'does not support payslip extraction', 'without payslip extraction', 'no paystub extraction', 'does not extract paystubs', 'does not extract paystub', 'does not support paystub extraction', 'without paystub extraction', 'no payroll stub extraction', 'does not extract payroll stubs', 'pay stub extraction not supported', 'payslip extraction not supported', 'paystub extraction not supported', 'no pay stub parser', 'does not parse pay stubs', 'does not parse pay stub', 'no pay stub field extraction'))
        self.assertEqual(values['GENERIC_NAMES'], ('extract_pay_stub', 'extract_pay_stubs', 'parse_pay_stub', 'parse_pay_stubs', 'extract_payslip', 'extract_payslips', 'parse_payslip', 'parse_payslips', 'extract_paystub', 'extract_paystubs', 'parse_paystub', 'parse_paystubs', 'extract_payroll_stub', 'extract_payroll_stubs', 'parse_payroll_stub', 'parse_payroll_stubs', 'extract_pay_stub_data', 'parse_pay_stub_data', 'pay_stub_extraction', 'pay_stub_extractor', 'pay_stub_parser', 'payslip_extraction', 'extract_payroll_stub_data', 'parse_payroll_stub_data'))
        self.assertEqual(values['AZURE_MODEL_IDS'], ('prebuilt-payStub.us',))
        self.assertEqual(values['MINDEE_PRODUCTS'], ('PayslipV2', 'PayslipV3'))
    def test_positive_00(self):
        self.assertEqual(claims('pay stub extraction'), (True, False))
    def test_positive_01(self):
        self.assertEqual(claims('extract pay stubs'), (True, False))
    def test_positive_02(self):
        self.assertEqual(claims('extracts pay stubs'), (True, False))
    def test_positive_03(self):
        self.assertEqual(claims('extracting pay stubs'), (True, False))
    def test_positive_04(self):
        self.assertEqual(claims('extract pay stub'), (True, False))
    def test_positive_05(self):
        self.assertEqual(claims('extracts pay stub'), (True, False))
    def test_positive_06(self):
        self.assertEqual(claims('extracting pay stub'), (True, False))
    def test_positive_07(self):
        self.assertEqual(claims('pay stub parsing'), (True, False))
    def test_positive_08(self):
        self.assertEqual(claims('pay stub parser'), (True, False))
    def test_positive_09(self):
        self.assertEqual(claims('parse pay stubs'), (True, False))
    def test_positive_10(self):
        self.assertEqual(claims('parses pay stubs'), (True, False))
    def test_positive_11(self):
        self.assertEqual(claims('parse pay stub'), (True, False))
    def test_positive_12(self):
        self.assertEqual(claims('parses pay stub'), (True, False))
    def test_positive_13(self):
        self.assertEqual(claims('payslip extraction'), (True, False))
    def test_positive_14(self):
        self.assertEqual(claims('extract payslips'), (True, False))
    def test_positive_15(self):
        self.assertEqual(claims('extracts payslips'), (True, False))
    def test_positive_16(self):
        self.assertEqual(claims('extracting payslips'), (True, False))
    def test_positive_17(self):
        self.assertEqual(claims('extract payslip'), (True, False))
    def test_positive_18(self):
        self.assertEqual(claims('extracts payslip'), (True, False))
    def test_positive_19(self):
        self.assertEqual(claims('extracting payslip'), (True, False))
    def test_positive_20(self):
        self.assertEqual(claims('payslip parsing'), (True, False))
    def test_positive_21(self):
        self.assertEqual(claims('payslip parser'), (True, False))
    def test_positive_22(self):
        self.assertEqual(claims('parse payslips'), (True, False))
    def test_positive_23(self):
        self.assertEqual(claims('parses payslips'), (True, False))
    def test_positive_24(self):
        self.assertEqual(claims('parse payslip'), (True, False))
    def test_positive_25(self):
        self.assertEqual(claims('parses payslip'), (True, False))
    def test_positive_26(self):
        self.assertEqual(claims('paystub extraction'), (True, False))
    def test_positive_27(self):
        self.assertEqual(claims('extract paystubs'), (True, False))
    def test_positive_28(self):
        self.assertEqual(claims('extracts paystubs'), (True, False))
    def test_positive_29(self):
        self.assertEqual(claims('extracting paystubs'), (True, False))
    def test_positive_30(self):
        self.assertEqual(claims('extract paystub'), (True, False))
    def test_positive_31(self):
        self.assertEqual(claims('extracts paystub'), (True, False))
    def test_positive_32(self):
        self.assertEqual(claims('extracting paystub'), (True, False))
    def test_positive_33(self):
        self.assertEqual(claims('paystub parsing'), (True, False))
    def test_positive_34(self):
        self.assertEqual(claims('paystub parser'), (True, False))
    def test_positive_35(self):
        self.assertEqual(claims('parse paystubs'), (True, False))
    def test_positive_36(self):
        self.assertEqual(claims('parses paystubs'), (True, False))
    def test_positive_37(self):
        self.assertEqual(claims('parse paystub'), (True, False))
    def test_positive_38(self):
        self.assertEqual(claims('parses paystub'), (True, False))
    def test_positive_39(self):
        self.assertEqual(claims('payroll stub extraction'), (True, False))
    def test_positive_40(self):
        self.assertEqual(claims('extract payroll stubs'), (True, False))
    def test_positive_41(self):
        self.assertEqual(claims('extracts payroll stubs'), (True, False))
    def test_positive_42(self):
        self.assertEqual(claims('extracting payroll stubs'), (True, False))
    def test_positive_43(self):
        self.assertEqual(claims('pay stub data extraction'), (True, False))
    def test_positive_44(self):
        self.assertEqual(claims('extract pay stub data'), (True, False))
    def test_positive_45(self):
        self.assertEqual(claims('pay stub field extraction'), (True, False))
    def test_positive_46(self):
        self.assertEqual(claims('payroll stub parsing'), (True, False))
    def test_positive_47(self):
        self.assertEqual(claims('parse payroll stubs'), (True, False))
    def test_positive_48(self):
        self.assertEqual(claims('pay stub document extraction'), (True, False))
    def test_positive_49(self):
        self.assertEqual(claims('extract pay stub documents'), (True, False))
    def test_negative_00(self):
        self.assertEqual(claims('no pay stub extraction'), (False, True))
    def test_negative_01(self):
        self.assertEqual(claims('does not extract pay stubs'), (False, True))
    def test_negative_02(self):
        self.assertEqual(claims('does not extract pay stub'), (False, True))
    def test_negative_03(self):
        self.assertEqual(claims('does not support pay stub extraction'), (False, True))
    def test_negative_04(self):
        self.assertEqual(claims('without pay stub extraction'), (False, True))
    def test_negative_05(self):
        self.assertEqual(claims('no payslip extraction'), (False, True))
    def test_negative_06(self):
        self.assertEqual(claims('does not extract payslips'), (False, True))
    def test_negative_07(self):
        self.assertEqual(claims('does not extract payslip'), (False, True))
    def test_negative_08(self):
        self.assertEqual(claims('does not support payslip extraction'), (False, True))
    def test_negative_09(self):
        self.assertEqual(claims('without payslip extraction'), (False, True))
    def test_negative_10(self):
        self.assertEqual(claims('no paystub extraction'), (False, True))
    def test_negative_11(self):
        self.assertEqual(claims('does not extract paystubs'), (False, True))
    def test_negative_12(self):
        self.assertEqual(claims('does not extract paystub'), (False, True))
    def test_negative_13(self):
        self.assertEqual(claims('does not support paystub extraction'), (False, True))
    def test_negative_14(self):
        self.assertEqual(claims('without paystub extraction'), (False, True))
    def test_negative_15(self):
        self.assertEqual(claims('no payroll stub extraction'), (False, True))
    def test_negative_16(self):
        self.assertEqual(claims('does not extract payroll stubs'), (False, True))
    def test_negative_17(self):
        self.assertEqual(claims('pay stub extraction not supported'), (False, True))
    def test_negative_18(self):
        self.assertEqual(claims('payslip extraction not supported'), (False, True))
    def test_negative_19(self):
        self.assertEqual(claims('paystub extraction not supported'), (False, True))
    def test_negative_20(self):
        self.assertEqual(claims('no pay stub parser'), (False, True))
    def test_negative_21(self):
        self.assertEqual(claims('does not parse pay stubs'), (False, True))
    def test_negative_22(self):
        self.assertEqual(claims('does not parse pay stub'), (False, True))
    def test_negative_23(self):
        self.assertEqual(claims('no pay stub field extraction'), (False, True))
    def test_excluded_005(self):
        self.assertEqual(evidence('def extract_pay_stub(doc): pass\nextract_pay_stub(doc)'), False)
    def test_excluded_006(self):
        self.assertEqual(evidence('def extract_pay_stub(doc): pass\nx.extract_pay_stub(doc)'), False)
    def test_excluded_007(self):
        self.assertEqual(evidence('class extract_pay_stub: pass\nx.extract_pay_stub(doc)'), False)
    def test_excluded_008(self):
        self.assertEqual(evidence('class X:\n def extract_pay_stub(self): pass\nx.extract_pay_stub(doc)'), False)
    def test_excluded_009(self):
        self.assertEqual(evidence('extract_pay_stub(doc)'), False)
    def test_excluded_010(self):
        self.assertEqual(evidence('x.extract_pay_stub'), False)
    def test_excluded_011(self):
        self.assertEqual(evidence('# x.extract_pay_stub(doc)\ns="x.extract_pay_stub(doc)"'), False)
    def test_excluded_012(self):
        self.assertEqual(evidence('def broken('), False)
    def test_excluded_013(self):
        self.assertEqual(evidence('extract_pay_stub = callback\nextract_pay_stub(doc)'), False)
    def test_excluded_014(self):
        self.assertEqual(evidence('from engine import extract_pay_stub\nextract_pay_stub: object = callback\nextract_pay_stub(doc)'), False)
    def test_excluded_015(self):
        self.assertEqual(evidence('from engine import extract_pay_stub\nwith context() as extract_pay_stub:\n extract_pay_stub(doc)'), False)
    def test_excluded_016(self):
        self.assertEqual(evidence('from engine import extract_pay_stub\nasync def f():\n async with context() as extract_pay_stub:\n  extract_pay_stub(doc)'), False)
    def test_fence_0(self):
        self.assertEqual(claims('```\nextract pay stubs\n```'), (False, False))
    def test_fence_1(self):
        self.assertEqual(claims('   ~~~~\nextract pay stubs\n   ~~~~'), (False, False))
    def test_fence_2(self):
        self.assertEqual(claims('```text\nextract pay stubs\n```'), (False, False))
    def test_inline_and_contraction(self):
        self.assertEqual(claims('We `extract pay stubs`.'), (True, False))
        self.assertEqual(claims("doesn't extract pay stubs"), (False, True))
        self.assertEqual(claims('pay-stub extraction'), (True, False))
    def test_excluded_paths(self):
        self.put('README.md', 'extract pay stubs')
        for path in ('fixtures/app.py', 'docs/app.py', 'examples/app.py'):
            self.put(path, 'x.extract_pay_stub(doc)')
        self.assertEqual(self.cli()[0], 2)
    def test_test_filename(self):
        self.put('README.md', 'extract pay stubs')
        self.put('app_test.py', 'x.extract_pay_stub(doc)')
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'MEDIUM')
    def test_route_000(self):
        self.assertEqual(evidence('x.extract_pay_stub(doc)'), True)
    def test_route_001(self):
        self.assertEqual(evidence('from engine import extract_pay_stub as operation\noperation(doc)'), True)
    def test_route_002(self):
        self.assertEqual(evidence('x.extract_pay_stubs(doc)'), True)
    def test_route_003(self):
        self.assertEqual(evidence('from engine import extract_pay_stubs as operation\noperation(doc)'), True)
    def test_route_004(self):
        self.assertEqual(evidence('x.parse_pay_stub(doc)'), True)
    def test_route_005(self):
        self.assertEqual(evidence('from engine import parse_pay_stub as operation\noperation(doc)'), True)
    def test_route_006(self):
        self.assertEqual(evidence('x.parse_pay_stubs(doc)'), True)
    def test_route_007(self):
        self.assertEqual(evidence('from engine import parse_pay_stubs as operation\noperation(doc)'), True)
    def test_route_008(self):
        self.assertEqual(evidence('x.extract_payslip(doc)'), True)
    def test_route_009(self):
        self.assertEqual(evidence('from engine import extract_payslip as operation\noperation(doc)'), True)
    def test_route_010(self):
        self.assertEqual(evidence('x.extract_payslips(doc)'), True)
    def test_route_011(self):
        self.assertEqual(evidence('from engine import extract_payslips as operation\noperation(doc)'), True)
    def test_route_012(self):
        self.assertEqual(evidence('x.parse_payslip(doc)'), True)
    def test_route_013(self):
        self.assertEqual(evidence('from engine import parse_payslip as operation\noperation(doc)'), True)
    def test_route_014(self):
        self.assertEqual(evidence('x.parse_payslips(doc)'), True)
    def test_route_015(self):
        self.assertEqual(evidence('from engine import parse_payslips as operation\noperation(doc)'), True)
    def test_route_016(self):
        self.assertEqual(evidence('x.extract_paystub(doc)'), True)
    def test_route_017(self):
        self.assertEqual(evidence('from engine import extract_paystub as operation\noperation(doc)'), True)
    def test_route_018(self):
        self.assertEqual(evidence('x.extract_paystubs(doc)'), True)
    def test_route_019(self):
        self.assertEqual(evidence('from engine import extract_paystubs as operation\noperation(doc)'), True)
    def test_route_020(self):
        self.assertEqual(evidence('x.parse_paystub(doc)'), True)
    def test_route_021(self):
        self.assertEqual(evidence('from engine import parse_paystub as operation\noperation(doc)'), True)
    def test_route_022(self):
        self.assertEqual(evidence('x.parse_paystubs(doc)'), True)
    def test_route_023(self):
        self.assertEqual(evidence('from engine import parse_paystubs as operation\noperation(doc)'), True)
    def test_route_024(self):
        self.assertEqual(evidence('x.extract_payroll_stub(doc)'), True)
    def test_route_025(self):
        self.assertEqual(evidence('from engine import extract_payroll_stub as operation\noperation(doc)'), True)
    def test_route_026(self):
        self.assertEqual(evidence('x.extract_payroll_stubs(doc)'), True)
    def test_route_027(self):
        self.assertEqual(evidence('from engine import extract_payroll_stubs as operation\noperation(doc)'), True)
    def test_route_028(self):
        self.assertEqual(evidence('x.parse_payroll_stub(doc)'), True)
    def test_route_029(self):
        self.assertEqual(evidence('from engine import parse_payroll_stub as operation\noperation(doc)'), True)
    def test_route_030(self):
        self.assertEqual(evidence('x.parse_payroll_stubs(doc)'), True)
    def test_route_031(self):
        self.assertEqual(evidence('from engine import parse_payroll_stubs as operation\noperation(doc)'), True)
    def test_route_032(self):
        self.assertEqual(evidence('x.extract_pay_stub_data(doc)'), True)
    def test_route_033(self):
        self.assertEqual(evidence('from engine import extract_pay_stub_data as operation\noperation(doc)'), True)
    def test_route_034(self):
        self.assertEqual(evidence('x.parse_pay_stub_data(doc)'), True)
    def test_route_035(self):
        self.assertEqual(evidence('from engine import parse_pay_stub_data as operation\noperation(doc)'), True)
    def test_route_036(self):
        self.assertEqual(evidence('x.pay_stub_extraction(doc)'), True)
    def test_route_037(self):
        self.assertEqual(evidence('from engine import pay_stub_extraction as operation\noperation(doc)'), True)
    def test_route_038(self):
        self.assertEqual(evidence('x.pay_stub_extractor(doc)'), True)
    def test_route_039(self):
        self.assertEqual(evidence('from engine import pay_stub_extractor as operation\noperation(doc)'), True)
    def test_route_040(self):
        self.assertEqual(evidence('x.pay_stub_parser(doc)'), True)
    def test_route_041(self):
        self.assertEqual(evidence('from engine import pay_stub_parser as operation\noperation(doc)'), True)
    def test_route_042(self):
        self.assertEqual(evidence('x.payslip_extraction(doc)'), True)
    def test_route_043(self):
        self.assertEqual(evidence('from engine import payslip_extraction as operation\noperation(doc)'), True)
    def test_route_044(self):
        self.assertEqual(evidence('x.extract_payroll_stub_data(doc)'), True)
    def test_route_045(self):
        self.assertEqual(evidence('from engine import extract_payroll_stub_data as operation\noperation(doc)'), True)
    def test_route_046(self):
        self.assertEqual(evidence('x.parse_payroll_stub_data(doc)'), True)
    def test_route_047(self):
        self.assertEqual(evidence('from engine import parse_payroll_stub_data as operation\noperation(doc)'), True)
    def test_route_048(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-payStub.us', doc)"), True)
    def test_route_049(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document_from_url('prebuilt-payStub.us', url)"), True)
    def test_route_050(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document(model_id='prebuilt-payStub.us', body=doc)"), True)
    def test_route_051(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer as az\nc=az.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-payStub.us', doc)"), True)
    def test_route_052(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer as az\nc=az.DocumentAnalysisClient()\nc.begin_analyze_document_from_url('prebuilt-payStub.us', url)"), True)
    def test_route_053(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer as az\nc=az.DocumentAnalysisClient()\nc.begin_analyze_document(model_id='prebuilt-payStub.us', body=doc)"), True)
    def test_route_054(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-payStub.us', doc)"), True)
    def test_route_055(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document_from_url('prebuilt-payStub.us', url)"), True)
    def test_route_056(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document(model_id='prebuilt-payStub.us', body=doc)"), True)
    def test_route_057(self):
        self.assertEqual(evidence("import azure.ai.documentintelligence\nc=azure.ai.documentintelligence.DocumentIntelligenceClient()\nc.begin_analyze_document('prebuilt-payStub.us', doc)"), True)
    def test_route_058(self):
        self.assertEqual(evidence("import azure.ai.documentintelligence\nc=azure.ai.documentintelligence.DocumentIntelligenceClient()\nc.begin_analyze_document_from_url('prebuilt-payStub.us', url)"), True)
    def test_route_059(self):
        self.assertEqual(evidence("import azure.ai.documentintelligence\nc=azure.ai.documentintelligence.DocumentIntelligenceClient()\nc.begin_analyze_document(model_id='prebuilt-payStub.us', body=doc)"), True)
    def test_route_060(self):
        self.assertEqual(evidence("import azure.ai.documentintelligence as az\nc=az.DocumentIntelligenceClient()\nc.begin_analyze_document('prebuilt-payStub.us', doc)"), True)
    def test_route_061(self):
        self.assertEqual(evidence("import azure.ai.documentintelligence as az\nc=az.DocumentIntelligenceClient()\nc.begin_analyze_document_from_url('prebuilt-payStub.us', url)"), True)
    def test_route_062(self):
        self.assertEqual(evidence("import azure.ai.documentintelligence as az\nc=az.DocumentIntelligenceClient()\nc.begin_analyze_document(model_id='prebuilt-payStub.us', body=doc)"), True)
    def test_route_063(self):
        self.assertEqual(evidence("from azure.ai.documentintelligence import DocumentIntelligenceClient as C\nc=C()\nc.begin_analyze_document('prebuilt-payStub.us', doc)"), True)
    def test_route_064(self):
        self.assertEqual(evidence("from azure.ai.documentintelligence import DocumentIntelligenceClient as C\nc=C()\nc.begin_analyze_document_from_url('prebuilt-payStub.us', url)"), True)
    def test_route_065(self):
        self.assertEqual(evidence("from azure.ai.documentintelligence import DocumentIntelligenceClient as C\nc=C()\nc.begin_analyze_document(model_id='prebuilt-payStub.us', body=doc)"), True)
    def test_route_066(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(PayslipV2, doc)'), True)
    def test_route_067(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(product=PayslipV2, document=doc)'), True)
    def test_route_068(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(PayslipV3, doc)'), True)
    def test_route_069(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(product=PayslipV3, document=doc)'), True)
    def test_route_070(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(product.fr.PayslipV3, doc)'), True)
    def test_route_071(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(product=product.fr.PayslipV3, document=doc)'), True)
    def test_route_072(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(mindee.product.fr.PayslipV2, doc)'), True)
    def test_route_073(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(product=mindee.product.fr.PayslipV2, document=doc)'), True)
    def test_route_074(self):
        self.assertEqual(evidence('from mindee import Client as C\nc=C()\nc.parse(PayslipV2, doc)'), True)
    def test_route_075(self):
        self.assertEqual(evidence('from mindee import Client as C\nc=C()\nc.parse(product=PayslipV2, document=doc)'), True)
    def test_route_076(self):
        self.assertEqual(evidence('from mindee import Client as C\nc=C()\nc.parse(PayslipV3, doc)'), True)
    def test_route_077(self):
        self.assertEqual(evidence('from mindee import Client as C\nc=C()\nc.parse(product=PayslipV3, document=doc)'), True)
    def test_route_078(self):
        self.assertEqual(evidence('from mindee import Client as C\nc=C()\nc.parse(product.fr.PayslipV3, doc)'), True)
    def test_route_079(self):
        self.assertEqual(evidence('from mindee import Client as C\nc=C()\nc.parse(product=product.fr.PayslipV3, document=doc)'), True)
    def test_route_080(self):
        self.assertEqual(evidence('from mindee import Client as C\nc=C()\nc.parse(mindee.product.fr.PayslipV2, doc)'), True)
    def test_route_081(self):
        self.assertEqual(evidence('from mindee import Client as C\nc=C()\nc.parse(product=mindee.product.fr.PayslipV2, document=doc)'), True)
    def test_not_evidence_000(self):
        self.assertEqual(evidence('import mindee'), False)
    def test_not_evidence_001(self):
        self.assertEqual(evidence('import veryfi'), False)
    def test_not_evidence_002(self):
        self.assertEqual(evidence('import boto3'), False)
    def test_not_evidence_003(self):
        self.assertEqual(evidence('import azure.ai.formrecognizer'), False)
    def test_not_evidence_004(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()'), False)
    def test_not_evidence_005(self):
        self.assertEqual(evidence('import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()'), False)
    def test_not_evidence_006(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()'), False)
    def test_not_evidence_007(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-invoice')"), False)
    def test_not_evidence_008(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-receipt')"), False)
    def test_not_evidence_009(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-layout')"), False)
    def test_not_evidence_010(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-read')"), False)
    def test_not_evidence_011(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-idDocument')"), False)
    def test_not_evidence_012(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-check.us')"), False)
    def test_not_evidence_013(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-tax.us')"), False)
    def test_not_evidence_014(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-bankStatement.us')"), False)
    def test_not_evidence_015(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-payStub')"), False)
    def test_not_evidence_016(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-paystub.us')"), False)
    def test_not_evidence_017(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(InvoiceV4, doc)'), False)
    def test_not_evidence_018(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(ReceiptV5, doc)'), False)
    def test_not_evidence_019(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(PassportV1, doc)'), False)
    def test_not_evidence_020(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(FinancialDocumentV1, doc)'), False)
    def test_not_evidence_021(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(BankCheckV1, doc)'), False)
    def test_not_evidence_022(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(BankAccountDetailsV2, doc)'), False)
    def test_not_evidence_023(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(CustomV1, doc)'), False)
    def test_not_evidence_024(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(TypePayslipV2, doc)'), False)
    def test_not_evidence_025(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(TypePayslipV3, doc)'), False)
    def test_not_evidence_026(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_any_document(doc)'), False)
    def test_not_evidence_027(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_any_document_url(doc)'), False)
    def test_not_evidence_028(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_document(doc)'), False)
    def test_not_evidence_029(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_document_url(doc)'), False)
    def test_not_evidence_030(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_w2_document(doc)'), False)
    def test_not_evidence_031(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_w2_document_url(doc)'), False)
    def test_not_evidence_032(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_w9_document(doc)'), False)
    def test_not_evidence_033(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_w9_document_url(doc)'), False)
    def test_not_evidence_034(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_w8_document(doc)'), False)
    def test_not_evidence_035(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_w8_document_url(doc)'), False)
    def test_not_evidence_036(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_check(doc)'), False)
    def test_not_evidence_037(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_check_url(doc)'), False)
    def test_not_evidence_038(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_check_with_remittance(doc)'), False)
    def test_not_evidence_039(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_check_with_remittance_url(doc)'), False)
    def test_not_evidence_040(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_bank_statement_document(doc)'), False)
    def test_not_evidence_041(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_bank_statement_document_url(doc)'), False)
    def test_not_evidence_042(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_bussines_card_document(doc)'), False)
    def test_not_evidence_043(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.classify_document(doc)'), False)
    def test_not_evidence_044(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_w2s(doc)'), False)
    def test_not_evidence_045(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_w2(doc)'), False)
    def test_not_evidence_046(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.delete_w2(doc)'), False)
    def test_not_evidence_047(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_w9s(doc)'), False)
    def test_not_evidence_048(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_w9(doc)'), False)
    def test_not_evidence_049(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.delete_w9(doc)'), False)
    def test_not_evidence_050(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_w8s(doc)'), False)
    def test_not_evidence_051(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_w8(doc)'), False)
    def test_not_evidence_052(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.delete_w8(doc)'), False)
    def test_not_evidence_053(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_bank_statements(doc)'), False)
    def test_not_evidence_054(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_checks(doc)'), False)
    def test_not_evidence_055(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_pay_stub(doc)'), False)
    def test_not_evidence_056(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_payslip(doc)'), False)
    def test_not_evidence_057(self):
        self.assertEqual(evidence('textract.analyze_document(doc)'), False)
    def test_not_evidence_058(self):
        self.assertEqual(evidence('textract.analyze_expense(doc)'), False)
    def test_not_evidence_059(self):
        self.assertEqual(evidence('textract.start_document_analysis(doc)'), False)
    def test_not_evidence_060(self):
        self.assertEqual(evidence('textract.get_expense_analysis(doc)'), False)
    def test_not_evidence_061(self):
        self.assertEqual(evidence('pdfplumber.extract_text(doc)'), False)
    def test_not_evidence_062(self):
        self.assertEqual(evidence('pdfplumber.extract_table(doc)'), False)
    def test_not_evidence_063(self):
        self.assertEqual(evidence('pdfplumber.extract_tables(doc)'), False)
    def test_not_evidence_064(self):
        self.assertEqual(evidence('pdfplumber.find_table(doc)'), False)
    def test_not_evidence_065(self):
        self.assertEqual(evidence('pdfplumber.find_tables(doc)'), False)
    def test_not_evidence_066(self):
        self.assertEqual(evidence('fitz.extract_text(doc)'), False)
    def test_not_evidence_067(self):
        self.assertEqual(evidence('fitz.find_tables(doc)'), False)
    def test_not_evidence_068(self):
        self.assertEqual(evidence('pypdf.extract_text(doc)'), False)
    def test_not_evidence_069(self):
        self.assertEqual(evidence('PyPDF2.extract_text(doc)'), False)
    def test_not_evidence_070(self):
        self.assertEqual(evidence('pdfminer.extract_text(doc)'), False)
    def test_not_evidence_071(self):
        self.assertEqual(evidence('pytesseract.image_to_string(doc)'), False)
    def test_not_evidence_072(self):
        self.assertEqual(evidence('pandas.read_csv(doc)'), False)
    def test_not_evidence_073(self):
        self.assertEqual(evidence('pandas.read_excel(doc)'), False)
    def test_not_evidence_074(self):
        self.assertEqual(evidence('camelot.read_pdf(doc)'), False)
    def test_not_evidence_075(self):
        self.assertEqual(evidence('tabula.read_pdf(doc)'), False)
    def test_not_evidence_076(self):
        self.assertEqual(evidence('tabula.convert_into(doc)'), False)
    def test_not_evidence_077(self):
        self.assertEqual(evidence('re.search("gross", text)\nre.findall("net", text)\nfields={"net": 1}'), False)
    def test_not_evidence_078(self):
        self.assertEqual(evidence('text="pay stub"\nfields=text.split()'), False)
    def test_not_evidence_079(self):
        self.assertEqual(evidence('subprocess.run(["mindee", "parse", "doc"])'), False)
    def test_not_evidence_080(self):
        self.assertEqual(evidence('subprocess.run(["veryfi", "process", "doc"])'), False)
    def test_not_evidence_081(self):
        self.assertEqual(evidence('import mindee as m\nc=m.Client()\nc.parse(PayslipV3, doc)'), False)
    def test_not_evidence_082(self):
        self.assertEqual(evidence('from engine import extract_pay_stub as op\ndef extract_pay_stub(): pass\nop(doc)'), False)
    def test_split_azure(self):
        self.put('README.md', 'extract pay stubs')
        self.put('one.py', 'from azure.ai.formrecognizer import DocumentAnalysisClient\nc=DocumentAnalysisClient()')
        self.put('two.py', "c.begin_analyze_document('prebuilt-payStub.us')")
        self.assertEqual(self.cli()[0], 2)
    def test_readme_self_audit(self):
        self.assertEqual(claims((Path(__file__).resolve().parents[1]/'README.md').read_text()), (False, False))
    def test_boundaries(self):
        self.assertEqual(claims('preextract pay stubsuffix'), (False, False))
        self.assertEqual(claims('extract pay\n\nstubs'), (False, False))

if __name__ == '__main__':
    unittest.main()
