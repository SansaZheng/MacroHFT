"""Integrity tests for real split archives and fail-closed completeness."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('restore',ROOT/'scripts/restore_archive.py')
restore=importlib.util.module_from_spec(spec);spec.loader.exec_module(restore)


class ArchiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.base=Path(cls.temp.name)
        source=cls.base/'source';source.mkdir();cls.archive=cls.base/'archive';(cls.archive/'.git').mkdir(parents=True)
        cls.original=source/'large.bin';block=os.urandom(1024**2)
        with cls.original.open('wb') as f:
            for _ in range(41): f.write(block)
        (source/'small.txt').write_text('measured evidence\n')
        subprocess.run([sys.executable,str(ROOT/'scripts/prepare_github_archive.py'),'--source',str(source),
                        '--destination',str(cls.archive)],check=True,stdout=subprocess.DEVNULL)
        cls.manifest=json.loads((cls.archive/'data-archive/manifest.json').read_text())
        cls.large=next(e for e in cls.manifest['files'] if e['path']=='large.bin')
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_roundtrip(self):
        self.assertGreaterEqual(len(self.large['parts']),2)
        target=self.base/'restored';self.assertEqual(restore.verify(self.archive,target)['verified_files'],2)
        self.assertEqual(restore.digest(target/'large.bin'),restore.digest(self.original))
    def test_corruption(self):
        p=self.archive/self.large['parts'][0]['path']
        with p.open('r+b') as f:b=f.read(1);f.seek(0);f.write(bytes([b[0]^1]))
        try:
            with self.assertRaisesRegex(ValueError,'Invalid part'):restore.verify(self.archive)
        finally:
            with p.open('r+b') as f:f.write(b)
    def test_preserve_existing(self):
        dest=self.base/'preserve';dest.mkdir();target=dest/'large.bin';target.write_bytes(b'old result')
        with self.assertRaises(FileExistsError):restore.verify(self.archive,dest)
        self.assertEqual(target.read_bytes(),b'old result');self.assertFalse(list(dest.glob('.restore-*')))
    def test_path_boundary(self):
        with self.assertRaises(ValueError):restore.safe(self.archive,'../../outside')
    def test_incomplete_archive_cannot_be_certified(self):
        p=self.archive/'data-archive/manifest.json';original=p.read_text();m=json.loads(original)
        m['complete_local_snapshot']=False;m['files'].append({'path':'missing','storage':'pending','size':1})
        p.write_text(json.dumps(m))
        try:
            with self.assertRaisesRegex(ValueError,'incomplete'):restore.verify(self.archive)
            receipt=restore.verify(self.archive,allow_partial=True)
            self.assertFalse(receipt['complete_local_snapshot']);self.assertEqual(receipt['pending_files'],1)
        finally:p.write_text(original)


if __name__=='__main__':unittest.main()
