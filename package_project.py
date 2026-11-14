"""Package reproducible evidence separately from the minimal cloud runtime."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parent
def included(path):
    excluded={'.venv','__pycache__','.git','.ipynb_checkpoints'}
    return path.is_file() and not any(p in excluded for p in path.relative_to(ROOT).parts) and path.name not in {'.DS_Store','integrity_manifest.json'}

files=sorted(p for p in ROOT.rglob('*') if included(p))
manifest={str(p.relative_to(ROOT)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files}
(ROOT/'integrity_manifest.json').write_text(json.dumps(manifest,indent=2))
files.append(ROOT/'integrity_manifest.json')
full=ROOT.parent/'jaya_jaya_reference.zip'
with ZipFile(full,'w',ZIP_DEFLATED) as z:
    for p in files:z.write(p,str(Path(ROOT.name)/p.relative_to(ROOT)))
cloud=ROOT.parent/'jaya_jaya_cloud_bundle.zip'
cloudfiles=[ROOT/'app.py',ROOT/'requirements.txt',ROOT/'NOTICE.md',ROOT/'.streamlit/config.toml',ROOT/'reports/metrics.json']
cloudfiles+=list((ROOT/'src').glob('*.py'))+list((ROOT/'model').glob('*.joblib'))+list((ROOT/'data').glob('*'))
with ZipFile(cloud,'w',ZIP_DEFLATED) as z:
    for p in sorted(cloudfiles): z.write(p,str(p.relative_to(ROOT)))
for p in [full,cloud]:
    with ZipFile(p) as z:
        assert z.testzip() is None
        print(p.name,p.stat().st_size,'bytes;',len(z.namelist()),'files; archive CRC OK')
