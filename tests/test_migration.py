"""A saved upload checkpoint must never silently replace changed source inputs."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from assets import save
from cq_migrate_assets import resume_manifest


class MigrationResumeTests(unittest.TestCase):
    def test_verified_pin_and_generated_metadata_survive_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            current={'schema_version':1,'assets':[{'id':'data','repo_id':'owner/repo',
                'repo_type':'dataset','code_commit':'a'*40,'status':'pending_authentication',
                'upload_authorization':'approved_private','revision':None,
                'files':[{'path':'data.txt','size':4,'sha256':'b'*64}]}]}
            saved=copy.deepcopy(current);saved['assets'][0].update(status='verified',revision='c'*40)
            saved['assets'][0]['files'].append({'path':'README.md','size':4,'sha256':'d'*64,'role':'documentation'})
            save(root/'source.json',current);save(root/'saved.json',saved)
            self.assertEqual(resume_manifest(root/'source.json',root/'saved.json'),saved)
            current['assets'][0]['files'][0]['sha256']='e'*64;save(root/'source.json',current)
            with self.assertRaises(ValueError):resume_manifest(root/'source.json',root/'saved.json')

    def test_revoked_authorization_blocks_a_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            current={'schema_version':1,'assets':[{'id':'data','repo_id':'owner/repo',
                'repo_type':'dataset','code_commit':'a'*40,'status':'pending_authentication',
                'upload_authorization':'approved_private','revision':None,'files':[]}]}
            save(root/'saved.json',current)
            current['assets'][0]['upload_authorization']='pending_rights_review';save(root/'source.json',current)
            with self.assertRaises(ValueError):resume_manifest(root/'source.json',root/'saved.json')


if __name__=='__main__':unittest.main()
