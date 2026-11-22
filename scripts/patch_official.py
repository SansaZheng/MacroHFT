"""Apply the recorded patch once to a fresh checkout of the pinned repository."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
repo=ROOT/'vendor/MacroHFT'
patch=ROOT/'results/official-runtime-and-variants.patch'
head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
if head!='31e5ef41f93b2aea6e63e6ae2267675c997a8e54':
    raise SystemExit('Refusing to apply the reproduction patch to an unverified source revision')
if subprocess.run(['git','-C',str(repo),'apply','--reverse','--check',str(patch)],capture_output=True).returncode==0:
    print('Recorded patch is already applied')
else:
    subprocess.run(['git','-C',str(repo),'apply','--check',str(patch)],check=True)
    subprocess.run(['git','-C',str(repo),'apply',str(patch)],check=True)
    print('Applied recorded patch')
