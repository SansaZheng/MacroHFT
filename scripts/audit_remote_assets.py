"""Read-only, bounded inventory of MacroHFT's authorized c225 assets and credentials metadata."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time


def timeout(*_):raise TimeoutError('bounded filesystem operation')


def main():
    out=Path(os.environ['CQ_OUTPUT_DIR']);out.mkdir(parents=True,exist_ok=True)
    root=Path('/date/zyy/macrohft-reproduction')
    report={'host':socket.gethostname(),'root':str(root),'read_only':True,'files':[],
            'python':sys.version,'hf_token_env_present':bool(os.environ.get('HF_TOKEN')),
            'shared_credentials_used':False,'complete':False}
    signal.signal(signal.SIGALRM,timeout)
    if socket.gethostname().split('.')[0]!='c225':raise ValueError('Inputs are local to c225')
    signal.alarm(30)
    st=os.statvfs(root);report['legacy_free_bytes']=st.f_bavail*st.f_frsize
    st=os.statvfs(out);report['output_free_bytes']=st.f_bavail*st.f_frsize
    report['output_realpath']=str(out.resolve())
    for prefix in ['vendor/MacroHFT/data','vendor/MacroHFT/result','results']:
        for parent,dirs,files in os.walk(root/prefix,followlinks=False):
            dirs[:]=[d for d in dirs if d not in ['.git','.cache','__pycache__','.venv'] and not (Path(parent)/d).is_symlink()]
            for name in files:
                p=Path(parent)/name
                if p.is_symlink():continue
                st=p.stat();report['files'].append({'path':str(p.relative_to(root)),'size':st.st_size})
                if len(report['files'])>20000:raise ValueError('Inventory count limit')
    signal.alarm(0)
    report['candidate_credential_locations']=[{'path':str(p),'exists':p.is_file(),'content_read':False} for p in [root/'.hf/token',root/'.cache/huggingface/token',Path.home()/'.cache/huggingface/token']]
    for py in [root/'.venv/bin/python',root/'env/bin/python']:
        if py.exists():
            try:
                r=subprocess.run([str(py),'-c','import sys,importlib.util;print(sys.version.split()[0]);s=importlib.util.find_spec("huggingface_hub");print(bool(s))'],capture_output=True,text=True,timeout=10)
                report.setdefault('interpreters',[]).append({'path':str(py),'probe':r.stdout.strip(),'returncode':r.returncode})
            except subprocess.TimeoutExpired:report.setdefault('interpreters',[]).append({'path':str(py),'timeout':True})
    report['complete']=True
    (out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'progress.log').write_text('1/1 asset audit complete\n')
    print(json.dumps({'complete':True,'files':len(report['files']),'hf_login_not_used':True}))

if __name__=='__main__':main()
