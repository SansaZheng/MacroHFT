"""Bootstrap failures must leave retrievable diagnostics, never venv symlinks."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('runtime', Path(__file__).resolve().parents[1]/'scripts/cq_runtime_qualify.py')
runtime = importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)


class CleanupTests(unittest.TestCase):
    def check_failure(self, fail_at):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            def run(command, **kwargs):
                if 'venv' in command:
                    env = out/'env';(env/'bin').mkdir(parents=True)
                    (env/'bin/python').symlink_to(sys.executable)
                    (env/'lib').mkdir();(env/'lib64').symlink_to(env/'lib', target_is_directory=True)
                    if fail_at == 'venv': raise subprocess.CalledProcessError(1, command)
                elif 'install' in command:
                    raise subprocess.CalledProcessError(1, command)
                return subprocess.CompletedProcess(command, 0, stdout='fixture\n', stderr='')
            with patch.dict(os.environ, {'CQ_OUTPUT_DIR':tmp, 'SOURCE_COMMIT':'0'*40}), \
                 patch.object(sys, 'argv', ['qualify']), patch.object(runtime, 'bootstrap_pip'), \
                 patch.object(runtime.subprocess, 'run', side_effect=run):
                with self.assertRaises(subprocess.CalledProcessError): runtime.main()
            self.assertTrue((out/'failure.txt').is_file())
            self.assertTrue((out/'source-manifest.json').is_file())
            self.assertFalse((out/'env').exists())
            self.assertFalse((out/'tmp').exists())
            self.assertFalse(any(p.is_symlink() for p in out.rglob('*')))

    def test_failed_venv_bootstrap_is_cleaned(self): self.check_failure('venv')
    def test_failed_dependency_install_is_cleaned(self): self.check_failure('pip')


if __name__ == '__main__': unittest.main()
