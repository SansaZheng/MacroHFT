import concurrent.futures,json,subprocess
hosts=['c219','c220','c224','c237','c203']
cmd=r'''lscpu | grep -E 'Model name|CPU MHz|Socket'; python3 -V; python3 -m pip --version 2>/dev/null; printf '\nOWNED_RUNTIME_CANDIDATES\n'; find /data/zyy /date/zyy -maxdepth 5 -type f -path '*/bin/python*' -o -path '*/bin/python3' 2>/dev/null | head -15; ls -d /home/sudingli/miniconda3/bin/python* /home/sudingli/miniforge3/bin/python* 2>/dev/null; printf '\nPROJECT_PREEXISTS\n'; ls -ld /data/zyy/macrohft-cluster /date/zyy/macrohft-cluster 2>/dev/null; true'''
def f(h):
 r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',h,cmd],text=True,capture_output=True,timeout=30)
 return {'host':h,'output':r.stdout,'error':r.stderr}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as p:print(json.dumps(list(p.map(f,hosts)),indent=2))
