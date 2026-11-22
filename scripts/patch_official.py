"""Verify the vendored snapshot, or patch an explicitly pinned upstream checkout."""
import argparse
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--repo',type=Path,default=ROOT/'vendor/MacroHFT')
parser.add_argument('--expected-commit',help='Actual project commit from the CQ job specification')
args=parser.parse_args()
repo=args.repo.resolve()
patch=ROOT/'results/official-runtime-and-variants.patch'
if repo==(ROOT/'vendor/MacroHFT').resolve() and (ROOT/'code-provenance.json').exists():
    if not args.expected_commit:
        parser.error('Vendored sources require --expected-commit with the project SHA, not the upstream SHA')
    from verify_source import verify
    import json
    print(json.dumps(verify(ROOT,args.expected_commit)))
    raise SystemExit(0)
top=Path(subprocess.check_output(['git','-C',str(repo),'rev-parse','--show-toplevel'],text=True).strip()).resolve()
if top!=repo:
    raise SystemExit('Refusing to borrow a parent repository identity for the upstream checkout')
head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
if head!='31e5ef41f93b2aea6e63e6ae2267675c997a8e54':
    raise SystemExit('Refusing to apply the reproduction patch to an unverified source revision')
if subprocess.run(['git','-C',str(repo),'apply','--reverse','--check',str(patch)],capture_output=True).returncode==0:
    print('Recorded patch is already applied')
else:
    subprocess.run(['git','-C',str(repo),'apply','--check',str(patch)],check=True)
    subprocess.run(['git','-C',str(repo),'apply',str(patch)],check=True)
    print('Applied recorded patch')
