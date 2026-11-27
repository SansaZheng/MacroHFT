"""Pinned, selective HF asset transfer. Never accepts a token as a CLI argument."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r'^[0-9a-f]{40}$')
HASH = re.compile(r'^[0-9a-f]{64}$')


def read(path):
    return json.loads(Path(path).read_text())


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.manifest-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2); f.write('\n')
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def rel(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or any(c in name for c in '*?[]') or str(p) != name:
        raise ValueError('Unsafe relative asset path')
    return p


def safe(root, name):
    p = Path(root).joinpath(*rel(name).parts)
    if not p.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('Path/symlink escapes root')
    return p


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024**2), b''): h.update(b)
    return h.hexdigest()


def verify_file(path, spec):
    if Path(path).stat().st_size != spec['size'] or digest(path) != spec['sha256']:
        raise ValueError('Integrity failure: ' + spec['path'])


def install_verified(source, target, spec, link=True):
    """Publish complete verified bytes atomically; never overwrite existing originals."""
    source=Path(source);target=Path(target)
    if target.exists():verify_file(target,spec);return
    target.parent.mkdir(parents=True,exist_ok=True)
    if link:
        try:os.link(source,target);verify_file(target,spec);return
        except FileExistsError:verify_file(target,spec);return
        except OSError:pass  # e.g. cache and run directory are different filesystems
    fd,tmp=tempfile.mkstemp(prefix='.asset-part-',dir=target.parent)
    try:
        with os.fdopen(fd,'wb') as out,source.open('rb') as inp:shutil.copyfileobj(inp,out,1024**2)
        verify_file(tmp,spec)
        try:os.link(tmp,target)  # same-filesystem atomic publish; fails if target appeared
        except FileExistsError:verify_file(target,spec)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def validate(m, require_pins=False):
    if m['schema_version'] != 1: raise ValueError('Unsupported manifest schema')
    ids = set()
    for a in m['assets']:
        if a['id'] in ids: raise ValueError('Duplicate asset id')
        ids.add(a['id']); rel(a['id'])
        if a['repo_type'] not in ('dataset', 'model'): raise ValueError('Invalid repo type')
        if require_pins or a['status'] == 'verified':
            if not a.get('repo_id') or len(a['repo_id'].split('/')) != 2 or not SHA.fullmatch(a.get('revision') or ''):
                raise ValueError('Asset needs repo_id and immutable 40-character HF commit: ' + a['id'])
        seen = set()
        for f in a['files']:
            rel(f['path'])
            if f['path'] in seen: raise ValueError('Duplicate file path')
            seen.add(f['path'])
            if f.get('sha256') is not None and not HASH.fullmatch(f['sha256']): raise ValueError('Invalid SHA-256')
            if f.get('size') is not None and (not isinstance(f['size'], int) or f['size'] < 0): raise ValueError('Invalid size')
            if (require_pins or a['status'] == 'verified') and (f.get('sha256') is None or f.get('size') is None):
                raise ValueError('Verified assets require every file hash and size')
    return m


def select(m, ids):
    if not ids: raise ValueError('Select one or more --asset; whole-repository download is disabled')
    byid = {a['id']: a for a in m['assets']}
    if set(ids) - byid.keys(): raise ValueError('Unknown asset id')
    selected = [byid[i] for i in dict.fromkeys(ids)]
    validate({'schema_version': 1, 'assets': selected}, require_pins=True)
    return selected


def file_subset(selected, paths):
    if not paths:return selected
    if len(selected)!=1:raise ValueError('--file requires exactly one asset')
    a=selected[0]
    if set(paths)-{f['path'] for f in a['files']}:raise ValueError('File not declared by asset')
    return [dict(a,files=[f for f in a['files'] if f['path'] in paths])]


def storage_root(value, variable):
    value = value or os.environ.get(variable)
    if not value: raise ValueError('Set --root / --cache-dir or ' + variable + '; no personal-computer default')
    p = Path(value).expanduser()
    if not p.is_absolute(): raise ValueError('Storage paths must be absolute')
    if p.resolve() == ROOT.resolve() or ROOT.resolve() in p.resolve().parents:
        raise ValueError('Asset/cache root must be outside the code checkout')
    p.mkdir(parents=True, exist_ok=True)
    return p


def api_client():
    from huggingface_hub import HfApi
    return HfApi()  # official HF_TOKEN or hf auth login credential provider


def audit(namespace=None):
    import huggingface_hub as hub
    from huggingface_hub import get_token
    report = {'client_version': hub.__version__, 'authenticated': bool(get_token()),
              'quota': 'unknown: inspect authenticated HF storage settings; do not infer unused quota'}
    if not report['authenticated']: return report
    api = api_client(); w = api.whoami()
    report.update(account=w.get('name'), token_role=w.get('auth', {}).get('accessToken', {}).get('role'),
                  organizations=[{'name': x.get('name'), 'role': x.get('roleInOrg')} for x in w.get('orgs', [])])
    owner = namespace or w['name']
    report['namespace'] = owner
    # List all owned repositories to detect alternate names, not just the proposed names.
    report['repositories'] = []
    for typ, method in [('model', api.list_models), ('dataset', api.list_datasets)]:
        for r in method(author=owner):
            if 'macrohft' in r.id.lower():
                info = api.repo_info(r.id, repo_type=typ)
                try: api.auth_check(r.id, repo_type=typ, write=True); writable = True
                except Exception: writable = False
                report['repositories'].append({'repo_id': r.id, 'repo_type': typ, 'private': info.private,
                                               'revision': info.sha, 'write_allowed': writable})
    return report


def fetch(m, ids, root, cache, paths=None):
    from huggingface_hub import hf_hub_download
    assets = file_subset(select(m, ids), paths); records = []
    for a in assets:
        files = a['files']
        for f in files:
            target = safe(root, a['id'] + '/' + f['path'])
            if target.exists(): verify_file(target, f)
            else:
                downloaded = hf_hub_download(repo_id=a['repo_id'], repo_type=a['repo_type'],
                    revision=a['revision'], filename=f['path'], cache_dir=str(cache))
                verify_file(downloaded, f)
                install_verified(downloaded,target,f)
            records.append({'asset': a['id'], 'path': f['path'], 'sha256': f['sha256'], 'revision': a['revision']})
    return {'verified_files': records}


def remote_identity(a, path):
    from huggingface_hub import HfFileSystem
    fs=HfFileSystem();prefix='datasets/' if a['repo_type']=='dataset' else ''
    h=hashlib.sha256();size=0
    with fs.open(prefix+a['repo_id']+'@'+a['revision']+'/'+path,'rb',block_size=1024**2,cache_type='none') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):h.update(block);size+=len(block)
    return {'sha256':h.hexdigest(),'size':size}


def stream_verify(a):
    """Stream whole pinned files to a hash; no persistent dataset/model cache."""
    checked=[]
    for f in a['files']:
        identity=remote_identity(a,f['path'])
        if identity['sha256']!=f['sha256'] or identity['size']!=f['size']:
            raise ValueError('Remote integrity failure: '+f['path'])
        checked.append(f['path'])
    return checked


def reserve_quota(path, namespace, size):
    """Conservative persisted reservation survives interrupted or concurrent uploads."""
    import fcntl
    path=Path(path)
    with Path(str(path)+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        quota=read(path)
        age=dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(quota['checked_at'])
        if age.total_seconds()<0 or age.total_seconds()>86400 or quota['namespace']!=namespace:
            raise ValueError('Need a matching quota observation less than 24 hours old')
        if quota.get('charges_authorized') is not False or not quota.get('source'):
            raise ValueError('Quota observation must identify source and prohibit charges')
        remaining=quota['included_free_bytes_remaining']-quota.get('reserved_bytes',0)
        if size>remaining*0.9:raise ValueError('Insufficient verified included quota headroom')
        quota['reserved_bytes']=quota.get('reserved_bytes',0)+size
        quota.setdefault('reservations',[]).append({'at':dt.datetime.now(dt.timezone.utc).isoformat(),'bytes':size})
        save(path,quota)
    # Never auto-release after errors: interrupted transfers may already use remote bytes.
    # Refresh actual storage observation to reconcile conservative reservations.


def upload(m, asset_id, source, repo_id, quota_path, output, create=False):
    """Bounded batches with remote hash deduplication, guarded commits, restartable calls."""
    from huggingface_hub.errors import RepositoryNotFoundError
    a = next(x for x in m['assets'] if x['id'] == asset_id)
    if a.get('upload_authorization') != 'approved_private':
        raise ValueError('Asset upload rights must be recorded before transfer')
    if not SHA.fullmatch(a.get('code_commit') or ''): raise ValueError('Record full corresponding source commit and provenance limits')
    if len(repo_id.split('/')) != 2: raise ValueError('Use namespace/repository')
    total = sum(f['size'] for f in a['files'])
    dependencies = select(m, a.get('requires', [])) if a.get('requires') else []
    a['dependency_revisions'] = [{k:d[k] for k in ['id','repo_id','repo_type','revision']} for d in dependencies]
    a['dataset_revisions'] = [d for d in a['dependency_revisions'] if d['repo_type']=='dataset']
    source = Path(source).resolve()
    for f in a['files']:
        p = safe(source, f['path'])
        if p.is_symlink(): raise ValueError('Upload source must be an explicit regular file')
        verify_file(p, f)
        if any(x in rel(f['path']).parts for x in ('.git','.venv','venv','.cache')) or Path(f['path']).name in ('.env','token','stored_tokens'):
            raise ValueError('Credential/environment/cache path refused')
    api = api_client(); w = api.whoami()
    # Reserve conservatively before any repository mutation. Reconcile against actual
    # HF usage after interrupted uploads; never silently release a reservation.
    reserve_quota(quota_path, repo_id.split('/')[0], total)
    # Inspect possible project repositories before creating another one.
    try: info = api.repo_info(repo_id, repo_type=a['repo_type'])
    except RepositoryNotFoundError as exc:
        if not create: raise
        namespace=repo_id.split('/')[0]
        owners={w.get('name')} | {o.get('name') for o in w.get('orgs',[]) if o.get('roleInOrg') in ('admin','write')}
        if namespace not in owners: raise ValueError('Namespace creation permission not established')
        method = api.list_datasets if a['repo_type'] == 'dataset' else api.list_models
        existing = [r.id for r in method(author=repo_id.split('/')[0]) if 'macrohft' in r.id.lower()]
        if existing: raise ValueError('Inspect/reuse existing project repos before creating: '+','.join(existing))
        api.create_repo(repo_id, repo_type=a['repo_type'], private=True, exist_ok=False)
        info = api.repo_info(repo_id, repo_type=a['repo_type'])
    if not info.private: raise ValueError('This workflow uploads only to private repositories')
    api.auth_check(repo_id, repo_type=a['repo_type'], write=True)
    # Compare actual remote bytes at the observed commit. LFS hashes avoid bulk reads.
    pending = []
    for f in a['files']:
        found = api.get_paths_info(repo_id, [f['path']], repo_type=a['repo_type'], revision=info.sha)
        same = False
        if found and hasattr(found[0], 'lfs') and found[0].lfs:
            same = found[0].lfs.sha256 == f['sha256'] and found[0].size == f['size']
        elif found:
            identity=remote_identity(dict(a,repo_id=repo_id,revision=info.sha),f['path'])
            same=identity['sha256']==f['sha256'] and identity['size']==f['size']
        if found and f['path']=='README.md' and not same:
            # Preserve an existing repository card, including its license metadata.
            identity=remote_identity(dict(a,repo_id=repo_id,revision=info.sha),f['path'])
            f.update(identity);f['preserved_existing_card']=True;same=True
        if not same: pending.append(f)
    # upload_folder in the pinned client supports parent_commit and Xet transport;
    # restart reruns remote comparisons; at most 50 explicit files per commit.
    for start in range(0, len(pending), 50):
        batch = pending[start:start+50]
        info = api.upload_folder(repo_id=repo_id, repo_type=a['repo_type'], folder_path=source,
             allow_patterns=[f['path'] for f in batch], parent_commit=info.sha if hasattr(info,'sha') else info.oid,
             commit_message='MacroHFT selected assets '+asset_id)
    revision = info.sha if hasattr(info, 'sha') else info.oid
    pinned = dict(a, repo_id=repo_id, revision=revision, status='verified')
    stream_verify(pinned)  # independent pinned remote bytes, not a local-cache hit
    a.update(repo_id=repo_id, revision=revision, status='verified')
    a['verified_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
    validate(m); save(output, m)
    return {'asset': asset_id, 'repo_id': repo_id, 'revision': revision, 'verified_files':len(a['files']), 'uploaded_files':len(pending)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,default=ROOT/'assets/manifest.json')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('validate')
    q=sub.add_parser('audit');q.add_argument('--namespace')
    for name in ['fetch','verify','stream-verify']:
        q=sub.add_parser(name);q.add_argument('--asset',action='append',required=True);q.add_argument('--file',action='append')
        if name != 'stream-verify':q.add_argument('--root')
        if name == 'fetch':q.add_argument('--cache-dir')
    q=sub.add_parser('upload');q.add_argument('--asset',required=True);q.add_argument('--source',required=True)
    q.add_argument('--repo-id',required=True);q.add_argument('--quota-record',required=True)
    q.add_argument('--output-manifest',required=True);q.add_argument('--create-repo',action='store_true')
    a=p.parse_args()
    if a.command=='audit':result=audit(a.namespace)
    else:
        m=validate(read(a.manifest))
        if a.command=='validate': result={'valid':True,'assets':len(m['assets']),'verified':sum(x['status']=='verified' for x in m['assets'])}
        elif a.command=='upload':result=upload(m,a.asset,a.source,a.repo_id,a.quota_record,a.output_manifest,a.create_repo)
        elif a.command=='stream-verify': result={x['id']:stream_verify(x) for x in file_subset(select(m,a.asset),a.file)}
        else:
            root=storage_root(a.root,'MACROHFT_ASSET_ROOT')
            if a.command=='fetch':result=fetch(m,a.asset,root,storage_root(a.cache_dir,'MACROHFT_HF_CACHE'),a.file)
            else:
                checked=0
                for x in file_subset(select(m,a.asset),a.file):
                    for f in x['files']:verify_file(safe(root,x['id']+'/'+f['path']),f);checked+=1
                result={'verified_files':checked}
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        # Library exception text can contain request URLs/headers; never log it.
        print('Asset operation failed ('+type(exc).__name__+'). Check authentication, paths, manifest and quota; credentials were not logged.',file=sys.stderr)
        sys.exit(1)
