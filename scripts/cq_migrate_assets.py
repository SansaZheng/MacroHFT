"""Resume an authorized private HF migration on a remote project disk through CQ."""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

from assets import ROOT, read, save, safe, validate, verify_file, upload, api_client


def run(args, cwd, log, timeout=1800):
    with log.open('a') as stream:
        subprocess.run([str(x) for x in args], cwd=cwd, stdout=stream,
                       stderr=subprocess.STDOUT, check=True, timeout=timeout)


def resume_manifest(committed, saved):
    """Resume pins only when all original payload identities still match."""
    current = validate(read(committed))
    if not saved.exists():
        return current
    old = validate(read(saved))
    def identities(m):
        return {a['id']: (a['repo_id'], a['repo_type'], a['code_commit'],
                         [(f['path'], f['size'], f['sha256'], f.get('source_path'), f.get('runtime_path'))
                          for f in a['files'] if f.get('role') != 'documentation'],
                         {key:a.get(key) for key in ['seed','configuration','evaluation_metrics',
                          'source_archive_commit','requires','license','code_identity_note']})
                for a in m['assets']}
    if identities(current) != identities(old):
        raise ValueError('Resume source identities changed; preserve old state')
    if any(a.get('upload_authorization') != 'approved_private' for a in current['assets']):
        raise ValueError('Current authorization missing')
    return old


def main(worker=False):
    if socket.gethostname().split('.')[0] != 'c225':
        raise ValueError('This migration uses c225-local originals and credentials')
    out = Path(os.environ['CQ_OUTPUT_DIR']).resolve()
    work = Path(os.environ['MACROHFT_MIGRATION_ROOT']).resolve()
    if not str(work).startswith('/date/zyy/macrohft-assets/') or work == out:
        raise ValueError('Use the authorized independent migration workspace')
    os.umask(0o077)
    out.mkdir(parents=True, exist_ok=True); work.mkdir(parents=True, exist_ok=True)
    credential = Path(os.environ['HF_HOME']).resolve()
    if credential.is_relative_to(out) or credential.is_relative_to(work):
        raise ValueError('Credentials must remain outside collected/migration outputs')
    if not (credential/'token').is_file():
        raise ValueError('Project HF login unavailable')
    log = work/'private-process.log'  # Never collected into GitHub or HF.
    def mark(stage):
        save(out/'status.json', {'stage':stage, 'host':'c225', 'complete':False})
        (out/'progress.log').write_text(stage+'\n')
        print(json.dumps({'stage':stage}), flush=True)
    if not worker:
        mark('0/12 prepare isolated official HF client')
        envroot = work/'asset-env'
        py = envroot/'bin/python'
        if not envroot.exists():
            run(['/date/zyy/macrohft-reproduction/.venv/bin/python',
                 ROOT/'scripts/create_asset_env.py', '--root', envroot], ROOT, log, 600)
        # Never repair or overwrite an unknown existing environment in place.
        run([py,'-c',"import huggingface_hub as h; assert h.__version__=='1.8.0'"], ROOT, log, 30)
        os.execv(str(py), [str(py), str(Path(__file__).resolve()), '--worker'])

    import huggingface_hub
    if huggingface_hub.__version__ != '1.8.0':
        raise ValueError('Unqualified upload client')
    api = api_client()
    identity = api.whoami()
    if identity.get('name') != 'Sansa005':
        raise ValueError('Unexpected authenticated account')
    permissions = []
    for typ in ['dataset','model']:
        info = api.repo_info('Sansa005/MacroHFT', repo_type=typ)
        if not info.private: raise ValueError('Private destination required')
        api.auth_check('Sansa005/MacroHFT', repo_type=typ, write=True)
        permissions.append({'repo_id':'Sansa005/MacroHFT','repo_type':typ,
                            'private':True,'write_allowed':True,'observed_revision':info.sha})
    save(out/'access.json', {'account':identity['name'],'client_version':huggingface_hub.__version__,
                            'repositories':permissions,'token_contents_recorded':False})
    quota = work/'quota.json'
    if not quota.exists():
        observed = read(ROOT/'docs/storage/verification/hf-browser-discovery-20261128.json')
        save(quota, {'namespace':'Sansa005','checked_at':observed['checked_at'],
                     'source':'Authenticated private storage settings observation in code manifest',
                     'included_free_bytes_remaining':observed['storage_observation']['conservative_included_free_bytes_remaining'],
                     'charges_authorized':False})
    if shutil.disk_usage(work).free < 5*1024**3:
        raise ValueError('Need 5 GiB free on authorized remote disk')
    state = work/'migration-manifest.json'
    manifest = resume_manifest(ROOT/'assets/manifest.json', state)
    save(state, manifest)
    started = time.monotonic()
    source = Path('/date/zyy/macrohft-reproduction')
    results = []
    for number, item in enumerate(manifest['assets'], 1):
        asset_id = item['id']
        mark(f'{number-1}/12 migrate {asset_id}')
        if item['status'] == 'verified':
            results.append({'asset':asset_id,'resumed_verified_revision':item['revision']})
            save(out/'verified-manifest.json', manifest)
            continue
        if item['upload_authorization'] != 'approved_private':
            raise ValueError('Private backup authorization missing')
        legacy = source
        if asset_id == 'cost-memory-data':
            # Recover only nine required historical ZIP blobs on the server, never the Mac.
            historical = work/'historical-code'
            if not historical.exists():
                run(['git','init','-q',historical], work, log)
                run(['git','remote','add','origin','https://github.com/SansaZheng/MacroHFT.git'], historical, log)
            commit = manifest['source_archive']['commit']
            run(['git','fetch','--depth=1','--filter=blob:none','origin',commit], historical, log)
            legacy = work/'historical-originals'
            for f in item['files']:
                if f.get('role') == 'documentation': continue
                target = safe(legacy, f['source_path'])
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    temporary = target.with_suffix(target.suffix+'.partial')
                    with temporary.open('wb') as stream, log.open('a') as errors:
                        subprocess.run(['git','show',commit+':'+f['source_path']],cwd=historical,
                                       stdout=stream,stderr=errors,check=True,timeout=180)
                    verify_file(temporary,f); os.replace(temporary,target)
                verify_file(target,f)
        stage = work/'stage'/asset_id
        plan = work/'upload-plan.json'
        run([sys.executable,ROOT/'scripts/stage_assets.py','--manifest',state,'--asset',asset_id,
             '--legacy-root',legacy,'--root',stage,'--output-manifest',plan], ROOT, log)
        manifest = validate(read(plan))
        # upload() captures returned commits and independently streams every selected file.
        result = upload(manifest, asset_id, stage, item['repo_id'], quota, state)
        results.append(result)
        save(out/'verified-manifest.json', manifest)
        save(out/'uploaded-assets.json', results)
    save(out/'receipt.json', {'complete':True,'source_commit':os.environ['SOURCE_COMMIT'],
         'client_version':huggingface_hub.__version__,'assets_verified':len(manifest['assets']),
         'selected_file_bytes':sum(f['size'] for a in manifest['assets'] for f in a['files']),
         'private_repositories':permissions,'elapsed_seconds':time.monotonic()-started,
         'originals_preserved':True,'clean_remote_restore_pending':True})
    mark('12/12 all selected private assets uploaded and streamed at immutable revisions')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--worker',action='store_true')
    try:
        main(parser.parse_args().worker)
    except Exception as exc:
        # Remote libraries can include signed URLs in exception text. Record only safe classifications.
        response=getattr(exc,'response',None)
        failure={'complete':False,'error_type':type(exc).__name__,
                 'http_status':getattr(response,'status_code',None)}
        out=Path(os.environ['CQ_OUTPUT_DIR']);out.mkdir(parents=True,exist_ok=True)
        save(out/'failure.json',failure);print(json.dumps(failure),flush=True)
        sys.exit(1)
