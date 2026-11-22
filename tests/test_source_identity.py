"""Regression checks for the nested non-Git vendor failure and source tampering."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('identity', Path(__file__).resolve().parents[1] / 'scripts/verify_source.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.vendor = self.root / 'vendor/MacroHFT'
        self.vendor.mkdir(parents=True)
        (self.vendor / 'agent.py').write_text('value = 42\n')
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.manifest = {'upstream_commit': '1'*40, 'source_roots': ['vendor/MacroHFT'],
                         'sha256': {'vendor/MacroHFT/agent.py': hashlib.sha256((self.vendor / 'agent.py').read_bytes()).hexdigest()}}
        (self.root / 'code-provenance.json').write_text(json.dumps(self.manifest))
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.commit = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True)

    def test_vendored_directory_without_git_is_valid(self):
        self.assertFalse((self.vendor / '.git').exists())
        self.assertEqual(module.verify(self.root, self.commit)['verified_files'], 1)

    def test_upstream_sha_cannot_identify_project(self):
        with self.assertRaisesRegex(ValueError, 'commit does not match'):
            module.verify(self.root, '1'*40)

    def test_nested_directory_cannot_borrow_parent_git_identity(self):
        with self.assertRaisesRegex(ValueError, 'actual Git root'):
            module.verify(self.vendor, self.commit)

    def test_modified_code_is_rejected(self):
        (self.vendor / 'agent.py').write_text('value = -1\n')
        with self.assertRaisesRegex(ValueError, 'Source hash mismatch'):
            module.verify(self.root, self.commit)

    def test_modified_manifest_is_rejected(self):
        (self.root / 'code-provenance.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'manifest differs'):
            module.verify(self.root, self.commit)

    def test_untracked_python_in_source_root_is_rejected(self):
        (self.vendor / 'shadow.py').write_text('value = -1\n')
        with self.assertRaisesRegex(ValueError, 'Unmanifested executable'):
            module.verify(self.root, self.commit)


if __name__ == '__main__':
    unittest.main()
