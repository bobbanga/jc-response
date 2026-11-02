"""Distribution documentation checks; no network, Windows execution or credentials."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA = '91b6df6dd4ae0ee4684c8d4946956ca2599294e118014837f3a339bb717be713'


class DistributionDocs(unittest.TestCase):
    def load_state(self):
        return json.loads((ROOT / 'releases/1.2.0-r1/distribution.json').read_text(encoding='utf-8'))

    def test_distribution_state_is_honest(self):
        s = self.load_state()
        self.assertIn(s['status'], ('upload_pending', 'prerelease_published'))
        if s['status'] == 'upload_pending':
            self.assertIsNone(s['release_url'])
            self.assertIsNone(s['download_url'])
            self.assertFalse(s['public_download_verified'])
        else:
            prefix = 'https://github.com/bobbanga/jc-response/releases/'
            self.assertTrue(s['release_url'].startswith(prefix + 'tag/'))
            self.assertTrue(s['download_url'].startswith(prefix + 'download/v1.2.0-r1/'))
            self.assertTrue(s['public_download_verified'])
            self.assertTrue(s['public_download_verified_at'])

    def test_binary_identity_unchanged(self):
        s = self.load_state()
        self.assertEqual(s['file_size'], 122270089)
        self.assertEqual(s['sha256'], EXPECTED_SHA)
        self.assertEqual(s['program_version'], '1.2.0')
        self.assertEqual(s['package_revision'], 'r1')
        self.assertFalse(s['signed'])
        self.assertIsNone(s['binary_source_commit'])

    def test_notes_share_identity(self):
        for p in ('docs/Release上传.md', 'docs/Cursor-WorkBuddy市场适配.md',
                  'releases/1.2.0-r1/WINDOWS_VALIDATION.md', 'releases/1.2.0-r1/PUBLIC_RELEASE_NOTES.md'):
            with self.subTest(path=p):
                t = (ROOT / p).read_text(encoding='utf-8')
                self.assertIn(EXPECTED_SHA, t)
                self.assertIn('122270089', t)

    def test_publication_is_staged_and_non_destructive(self):
        t = (ROOT / 'docs/Release上传.md').read_text(encoding='utf-8')
        for value in ('--draft', '--prerelease', '--latest=false', '不使用 --clobber', '不带认证'):
            self.assertIn(value, t)

    def test_dynamic_evidence_is_attributed(self):
        t = (ROOT / 'releases/1.2.0-r1/WINDOWS_VALIDATION.md').read_text(encoding='utf-8')
        self.assertIn('没有独立运行 Windows EXE', t)
        self.assertIn('WorkBuddy 实际加载 r1 Skill | NOT_RUN', t)
        self.assertIn('本次包真实读取与同批导出 | NOT_RUN', t)

    def test_market_boundary(self):
        t = (ROOT / 'docs/Cursor-WorkBuddy市场适配.md').read_text(encoding='utf-8')
        for value in ('20,000,000', 'preAuth', '不要自动再运行 --configure-workbuddy',
                      '禁止自动提交 WorkBuddy 审核', '不重编译或重打包 r1'):
            self.assertIn(value, t)
        self.assertEqual(self.load_state()['workbuddy_market_status'], 'not_submitted')

    def test_no_personal_paths_or_execution_policy_bypass(self):
        paths = [ROOT / 'docs/Release上传.md', ROOT / 'docs/Cursor-WorkBuddy市场适配.md']
        for p in paths:
            t = p.read_text(encoding='utf-8').casefold()
            self.assertNotIn('c:\\users\\hiabo', t)
            self.assertNotIn('d:\\code\\work', t)
            self.assertNotIn('-executionpolicy bypass', t)


if __name__ == '__main__':
    unittest.main()
