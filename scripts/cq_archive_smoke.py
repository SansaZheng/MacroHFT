"""Qualify source identity and archival integrity through CQ; no market evaluation."""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time


def main():
    root=Path(__file__).resolve().parents[1]
    out=Path(os.environ['CQ_OUTPUT_DIR']);out.mkdir(parents=True,exist_ok=True)
    tmp=out/'tmp';tmp.mkdir(exist_ok=True)
    env=dict(os.environ,TMPDIR=str(tmp),PYTHONDONTWRITEBYTECODE='1')
    start=time.monotonic();(out/'progress.log').write_text('0/3 verify pinned code manifest\n')
    manifest=json.loads((root/'code-manifest.json').read_text())
    for name,expected in manifest['sha256'].items():
        actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
        if actual!=expected:raise RuntimeError('Source hash mismatch: '+name)
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,text=True)
    observed=head.stdout.strip() if head.returncode==0 else None
    expected_commit=os.environ['SOURCE_COMMIT']
    if observed and observed!=expected_commit:raise RuntimeError('Git HEAD differs from CQ spec')
    (out/'progress.log').write_text('1/3 source verified; running archive integrity tests\n')
    run=subprocess.run([sys.executable,str(root/'tests/test_archive.py')],cwd=root,
                       env=env,capture_output=True,text=True,timeout=240)
    (out/'archive-tests.log').write_text(run.stdout+run.stderr)
    if run.returncode or 'Ran 5 tests' not in run.stderr or '\nOK\n' not in run.stderr:
        raise RuntimeError('Archive integrity qualification failed; inspect archive-tests.log')
    identity=subprocess.run([sys.executable,str(root/'tests/test_source_identity.py')],cwd=root,
                            env=env,capture_output=True,text=True,timeout=60)
    (out/'source-identity-tests.log').write_text(identity.stdout+identity.stderr)
    if identity.returncode or 'Ran 6 tests' not in identity.stderr or '\nOK\n' not in identity.stderr:
        raise RuntimeError('Source identity qualification failed')
    (out/'progress.log').write_text('2/3 integrity tests passed; recording receipt\n')
    peak=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    result={'source_manifest_verified':True,'declared_commit':expected_commit,
            'observed_git_commit':observed,'source_manifest':manifest,
            'archive_tests_passed':True,'archive_test_count':5,
            'source_identity_tests_passed':True,'source_identity_test_count':6,
            'python':sys.version,'elapsed_seconds':time.monotonic()-start,
            'children_peak_rss_bytes':peak if sys.platform=='darwin' else peak*1024,
            'training_performed':False,'market_test_evaluations':0,
            'purpose':'code and archive qualification only; not reproduction performance'}
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'progress.log').write_text('3/3 qualification complete\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
