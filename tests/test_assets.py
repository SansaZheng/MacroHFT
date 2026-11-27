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


    def test_interrupted_copy_does_not_leave_a_partial_target(self):
        source=self.root/'source';source.write_bytes(self.data);target=self.root/'destination/data.txt'
        with patch.object(assets.shutil,'copyfileobj',side_effect=OSError('interrupted')):
            with self.assertRaises(OSError):assets.install_verified(source,target,self.file,link=False)
        self.assertFalse(target.exists());self.assertEqual(list(target.parent.glob('.asset-part-*')),[])
        assets.install_verified(source,target,self.file,link=False)
        self.assertEqual(target.read_bytes(),self.data)

class UploadTests(unittest.TestCase):
    def setUp(self):
        import datetime as dt
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'weights.txt').write_bytes(b'selected checkpoint fixture')
        self.file={'path':'weights.txt','size':(self.root/'weights.txt').stat().st_size,'sha256':assets.digest(self.root/'weights.txt')}
        self.asset={'id':'model','repo_type':'model','repo_id':None,'revision':None,'status':'pending_authentication',
                    'code_commit':'b'*40,'upload_authorization':'approved_private','files':[self.file]}
        self.manifest={'schema_version':1,'assets':[self.asset]}
        self.quota=self.root/'quota.json';self.quota.write_text(json.dumps({'namespace':'owner','checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),
            'source':'authenticated settings observation','included_free_bytes_remaining':1000000,'charges_authorized':False}))
        self.info=types.SimpleNamespace(sha='a'*40,private=True)
        self.api=types.SimpleNamespace(whoami=lambda:{'name':'owner'},repo_info=lambda *args,**kwargs:self.info,
                 auth_check=lambda *args,**kwargs:None,get_paths_info=lambda *args,**kwargs:[])
        self.calls=[]
        def upload(**kwargs):self.calls.append(kwargs);return types.SimpleNamespace(oid='c'*40)
        self.api.upload_folder=upload
        self.error=types.SimpleNamespace(RepositoryNotFoundError=type('RepositoryNotFoundError',(Exception,),{}))
    def invoke(self):
        with patch.dict(sys.modules,{'huggingface_hub.errors':self.error}),patch.object(assets,'api_client',return_value=self.api),patch.object(assets,'stream_verify',return_value=['weights.txt']):
            return assets.upload(self.manifest,'model',self.root,'owner/project',self.quota,self.root/'new-manifest.json')
    def test_upload_requires_private_repo(self):
        self.info.private=False
        with self.assertRaises(ValueError):self.invoke()
        self.assertFalse(self.calls)
    def test_upload_requires_rights(self):
        self.asset['upload_authorization']='pending_rights_review'
        with self.assertRaises(ValueError):self.invoke()
        self.assertFalse(self.calls)
    def test_upload_requires_quota_headroom(self):
        q=assets.read(self.quota);q['included_free_bytes_remaining']=1;assets.save(self.quota,q)
        with self.assertRaises(ValueError):self.invoke()
        self.assertFalse(self.calls)
    def test_upload_uses_guarded_commit_and_captures_returned_pin(self):
        r=self.invoke();self.assertEqual(r['revision'],'c'*40)
        self.assertEqual(self.calls[0]['parent_commit'],'a'*40)
        self.assertEqual(self.calls[0]['allow_patterns'],['weights.txt'])
        self.assertEqual(assets.read(self.root/'new-manifest.json')['assets'][0]['revision'],'c'*40)
    def test_rerun_skips_identical_remote_file(self):
        self.api.get_paths_info=lambda *args,**kwargs:[types.SimpleNamespace(size=self.file['size'],lfs=types.SimpleNamespace(sha256=self.file['sha256']))]
        r=self.invoke();self.assertEqual(r['uploaded_files'],0);self.assertFalse(self.calls)
    def test_model_rejects_unpinned_dataset(self):
        self.asset['requires']=['data'];self.manifest['assets'].append({'id':'data','repo_type':'dataset','repo_id':None,'revision':None,'status':'pending_authentication','files':[]})
        with self.assertRaises(ValueError):self.invoke()
        self.assertFalse(self.calls)

    def test_quota_reservations_survive_retries(self):
        assets.reserve_quota(self.quota,'owner',800000)
        with self.assertRaises(ValueError):assets.reserve_quota(self.quota,'owner',300000)
        self.assertEqual(assets.read(self.quota)['reserved_bytes'],800000)

    def test_interruption_does_not_emit_verified_manifest(self):
        def broken(**kwargs):raise TimeoutError('simulated transport interruption')
        self.api.upload_folder=broken
        with self.assertRaises(TimeoutError):self.invoke()
        self.assertFalse((self.root/'new-manifest.json').exists())
        self.assertGreater(assets.read(self.quota)['reserved_bytes'],0)
    def test_create_is_private_and_duplicate_aware(self):
        calls=[]
        def info(*args,**kwargs):
            if not calls:raise self.error.RepositoryNotFoundError()
            return self.info
        self.api.repo_info=info
        self.api.list_models=lambda **kw:[]
        self.api.create_repo=lambda *args,**kw:calls.append(kw)
        with patch.dict(sys.modules,{'huggingface_hub.errors':self.error}),patch.object(assets,'api_client',return_value=self.api),patch.object(assets,'stream_verify',return_value=[]):
            assets.upload(self.manifest,'model',self.root,'owner/macrohft-models',self.quota,self.root/'new.json',create=True)
        self.assertTrue(calls[0]['private']);self.assertFalse(calls[0]['exist_ok'])

    def test_existing_card_and_license_are_preserved(self):
        (self.root/'README.md').write_text('new generic card')
        f={'path':'README.md','size':16,'sha256':assets.digest(self.root/'README.md'),'role':'documentation'}
        self.asset['files'].append(f)
        old={'size':20,'sha256':'d'*64}
        self.api.get_paths_info=lambda repo,paths,**kw:([types.SimpleNamespace(lfs=None)] if paths==['README.md'] else [])
        with patch.object(assets,'remote_identity',return_value=old):r=self.invoke()
        self.assertEqual(self.calls[0]['allow_patterns'],['weights.txt'])
        self.assertEqual(self.asset['files'][1]['sha256'],'d'*64)
        self.assertEqual((self.root/'README.md').read_text(),'new generic card')

class RunIsolationTests(unittest.TestCase):
    def test_prepare_uses_verified_assets_and_skips_documentation_links(self):
        import io,tarfile
        import remote_run
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);inputs=root/'inputs';work=root/'work';work.mkdir()
            entries=[]
            for name in ['eth-prepared','feature-definitions','released-experts']:
                base=inputs/name;base.mkdir(parents=True)
                (base/'data.txt').write_text('fixed input');(base/'README.md').write_text('card')
                files=[{'path':'data.txt','runtime_path':'vendor/'+name+'/data.txt','size':11,'sha256':assets.digest(base/'data.txt')},
                       {'path':'README.md','role':'documentation','size':4,'sha256':assets.digest(base/'README.md')}]
                entries.append({'id':name,'repo_type':'dataset' if name!='released-experts' else 'model','repo_id':'owner/'+name,'revision':'a'*40,'status':'verified','files':files})
            stream=io.BytesIO()
            with tarfile.open(fileobj=stream,mode='w') as tar:
                member=tarfile.TarInfo('README.md');data=b'code-only';member.size=len(data);tar.addfile(member,io.BytesIO(data))
            def git(cmd,**kwargs):return 'b'*40+'\n' if cmd[1]=='rev-parse' else stream.getvalue()
            with patch.object(remote_run.subprocess,'check_output',side_effect=git):
                remote_run.prepare({'schema_version':1,'assets':entries},inputs,work)
            self.assertTrue((work/'vendor/eth-prepared/data.txt').is_symlink())
            self.assertEqual((work/'README.md').read_text(),'code-only')
            self.assertEqual(assets.read(work/'run-inputs.json')['code_commit'],'b'*40)

if __name__=='__main__':unittest.main()
