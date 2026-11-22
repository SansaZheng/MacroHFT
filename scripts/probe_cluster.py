"""Read-only capacity inventory through the authorized c225 SSH configuration."""
import concurrent.futures,json,subprocess
HOSTS=['c219','c220','c221','c222','c223','c224','c232','c237','c203']
PROBE=r'''hostname; id; printf '\nCPU_MEMORY\n'; nproc; uptime; free -m; printf '\nSTORAGE\n'; for p in /date /data /date/zyy /data/zyy; do if test -d "$p"; then ls -ld "$p"; df -Pm "$p" | tail -1; test -w "$p" && echo writable; fi; done; printf '\nGPUS\n'; nvidia-smi --query-gpu=index,name,memory.total,memory.free,utilization.gpu --format=csv,noheader 2>/dev/null; printf '\nRUNTIME\n'; command -v python3; ls -d /date/zyy/*/.venv/bin/python /data/zyy/*/.venv/bin/python 2>/dev/null; true'''
def check(host):
 try:
  r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',host,PROBE],capture_output=True,text=True,timeout=35)
  return {'host':host,'exit_code':r.returncode,'output':r.stdout,'error':r.stderr}
 except Exception as e:return {'host':host,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 print(json.dumps(list(pool.map(check,HOSTS)),indent=2))
