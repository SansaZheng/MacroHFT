import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import assets
from stage_assets import stage

class AssetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.data=b'bounded fixture\n'
        self.file={'path':'data/train.txt','source_path':'legacy/train.txt','size':len(self.data),'sha256':hashlib.sha256(self.data).hexdigest()}
        self.asset={'id':'fixture','repo_type':'dataset','repo_id':'owner/repo','revision':'a'*40,'status':'verified','files':[self.file]}
        self.manifest={'schema_version':1,'assets':[self.asset]}
    def test_rejects_moving_revision(self):
        self.asset['revision']='main'
        with self.assertRaises(ValueError):assets.validate(self.manifest)
    def test_rejects_path_traversal_globs_and_absolute(self):
        for name in ['../secret','/secret','data/../../secret','data/*.txt','data/a\\b']:
            with self.subTest(name=name),self.assertRaises(ValueError):assets.safe(self.root,name)
    def test_rejects_symlink_escape(self):
        (self.root/'escape').symlink_to(self.root.parent)
        with self.assertRaises(ValueError):assets.safe(self.root,'escape/token')
    def test_requires_explicit_selection(self):
        with self.assertRaises(ValueError):assets.select(self.manifest,[])
    def test_pending_assets_cannot_download(self):
        self.asset.update(status='pending_authentication',revision=None,repo_id=None)
        assets.validate(self.manifest)
        with self.assertRaises(ValueError):assets.select(self.manifest,['fixture'])
    def test_selective_pinned_download_and_reuse(self):
        cache=self.root/'cache';cache.mkdir();p=cache/'blob';p.write_bytes(self.data)
        calls=[]
        def download(**kwargs):calls.append(kwargs);return str(p)
        fake=types.SimpleNamespace(hf_hub_download=download)
        with patch.dict(sys.modules,{'huggingface_hub':fake}):
            for _ in range(2):assets.fetch(self.manifest,['fixture'],self.root/'out',cache)
        self.assertEqual(len(calls),1);self.assertEqual(calls[0]['revision'],'a'*40)
        self.assertEqual(calls[0]['filename'],'data/train.txt')
    def test_corruption_is_rejected(self):
        target=self.root/'fixture/data/train.txt';target.parent.mkdir(parents=True);target.write_bytes(b'wrong')
        with self.assertRaises(ValueError):assets.verify_file(target,self.file)
    def test_staging_preserves_source_and_rejects_overwrite(self):
        legacy=self.root/'legacy';source=legacy/'legacy/train.txt';source.parent.mkdir(parents=True);source.write_bytes(self.data)
        dest=self.root/'stage';stage(self.manifest,['fixture'],legacy,dest)
        self.assertEqual(source.read_bytes(),self.data)
        (dest/'data/train.txt').write_bytes(b'wrong')
        with self.assertRaises(ValueError):stage(self.manifest,['fixture'],legacy,dest)
    def test_stream_verification_no_download_cache(self):
        import io
        class FS:
            def open(_,path,*args,**kwargs):
                self.assertIn('@'+'a'*40+'/',path);return io.BytesIO(self.data)
        with patch.dict(sys.modules,{'huggingface_hub':types.SimpleNamespace(HfFileSystem=FS)}):
            self.assertEqual(assets.stream_verify(self.asset),['data/train.txt'])
    def test_unknown_file_selection_rejected(self):
        with patch.dict(sys.modules,{'huggingface_hub':types.SimpleNamespace(hf_hub_download=lambda **kw:None)}):
            with self.assertRaises(ValueError):assets.fetch(self.manifest,['fixture'],self.root,self.root,['bad.txt'])

if __name__=='__main__':unittest.main()
