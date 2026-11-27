"""Stage explicitly selected legacy assets on a remote disk without altering originals."""
import argparse
import os
from pathlib import Path
import shutil
import sys
from assets import read, safe, save, digest, validate, verify_file, storage_root, select, install_verified


def stage(manifest, ids, legacy_root, destination):
    selected=[a for a in manifest['assets'] if a['id'] in ids]
    if len(selected)!=len(set(ids)): raise ValueError('Unknown/duplicate asset selection')
    count=0
    for a in selected:
        for f in a['files']:
            if f.get('role') == 'documentation': continue
            if f.get('sha256') is None: raise ValueError('Inventory/hash pending: '+f['path'])
            source=safe(legacy_root,f['source_path']);target=safe(destination,f['path'])
            verify_file(source,f)
            if target.exists():verify_file(target,f)
            else:
                # Copy mutable legacy files; partial copies are never published.
                install_verified(source,target,f,link=False)
            count+=1
    return count


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',default=str(Path(__file__).resolve().parents[1]/'assets/manifest.json'))
    p.add_argument('--asset',action='append',required=True)
    p.add_argument('--legacy-root',required=True);p.add_argument('--root',required=True)
    p.add_argument('--output-manifest',required=True)
    a=p.parse_args()
    m=validate(read(a.manifest));root=storage_root(a.root,'MACROHFT_STAGE_ROOT')
    n=stage(m,a.asset,Path(a.legacy_root),root)
    card=("---\ntags:\n- macrohft\n- reinforcement-learning\n---\n# MacroHFT private research assets\n\n"
          "Private research backup. No new license or public redistribution permission is granted.\n"
          "Code and reproduction instructions: https://github.com/SansaZheng/MacroHFT\n"
          "Each metadata/<asset>/provenance.json records source identity, splits/dependencies,\n"
          "configuration, seed and metrics where available. See the pinned GitHub asset manifest.\n"
          "Selected negative-result models are retained as research evidence. Model weights alone\n"
          "do not guarantee exact training resumption; original license notices remain applicable.\n")
    for item in m['assets']:
        if item['id'] not in a.asset:continue
        item['files']=[f for f in item['files'] if f.get('role')!='documentation']
        dependencies=select(m,item['requires']) if item.get('requires') else []
        item['dataset_revisions']=[{k:d[k] for k in ['id','repo_id','repo_type','revision']} for d in dependencies if d['repo_type']=='dataset']
        meta='metadata/'+item['id']+'/provenance.json'
        save(safe(root,meta),dict(item,split_definitions=read(Path(__file__).resolve().parents[1]/'assets/splits.json')))
        (root/'README.md').write_text(card)
        for name in [meta,'README.md']:
            f=safe(root,name)
            item['files'].append({'path':name,'size':f.stat().st_size,'sha256':digest(f),'role':'documentation'})
    save(a.output_manifest,m)
    print({'staged_files':n,'output_manifest':a.output_manifest})
