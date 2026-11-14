"""Restore the exported dashboard into NEW local containers, without replacing existing ones."""
import json
import subprocess
import time
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
PG="jaya-review-postgres"
MB="jaya-review-metabase"
BASE="http://localhost:3301/api"

def docker(*args,**kw):
    return subprocess.run(["docker",*args],check=True,**kw)

def wait_for(fn,description):
    for _ in range(90):
        try:
            if fn(): return
        except (requests.RequestException,subprocess.CalledProcessError): pass
        time.sleep(2)
    raise RuntimeError("Timeout: "+description)

def restore():
    manifest=json.loads((HERE/"dashboard_manifest.json").read_text())
    # Refuse to touch existing names. Use docker start to reopen a prior restore instead.
    names=subprocess.check_output(["docker","ps","-a","--format","{{.Names}}"],text=True).splitlines()
    if PG in names or MB in names:
        raise RuntimeError("Container jaya-review sudah ada; jalankan docker start atau gunakan nama baru. Tidak ada container yang dihapus.")
    if not (HERE/"metabase.db.mv.db").is_file() or not (HERE/"students.sql").is_file():
        raise FileNotFoundError("Ekspor metabase.db.mv.db dan students.sql wajib tersedia.")
    docker("run","-d","--name",PG,"-e","POSTGRES_DB=students","-e","POSTGRES_USER=reference","-e","POSTGRES_PASSWORD=jaya_reference_local","-p","127.0.0.1:55433:5432","postgres:16-alpine",stdout=subprocess.DEVNULL)
    wait_for(lambda:subprocess.run(["docker","exec",PG,"pg_isready","-U","reference","-d","students"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0,"PostgreSQL")
    with (HERE/"students.sql").open('rb') as source:
        docker("exec","-i",PG,"psql","-v","ON_ERROR_STOP=1","-U","reference","-d","students",stdin=source,stdout=subprocess.DEVNULL)
    # This image relocates a legacy H2 file to a private directory at startup.
    docker("create","--name",MB,"-p","127.0.0.1:3301:3000","-e","MB_DB_FILE=/tmp/metabase.db","metabase/metabase:v0.56.3",stdout=subprocess.DEVNULL)
    docker("cp",str(HERE/"metabase.db.mv.db"),MB+":/tmp/metabase.db.mv.db")
    docker("start",MB,stdout=subprocess.DEVNULL)
    wait_for(lambda:requests.get(BASE+"/health",timeout=5).ok,"Metabase")
    s=requests.Session()
    login=s.post(BASE+"/session",json={"username":"root@mail.com","password":"Root123!reference"},timeout=30)
    login.raise_for_status()
    s.headers['X-Metabase-Session']=login.json()['id']
    databases=s.get(BASE+"/database",timeout=30); databases.raise_for_status()
    db=next(d for d in databases.json()['data'] if d['name']=='Jaya Jaya Students')
    details=db['details']; details.update({'host':'host.docker.internal','port':55433,'dbname':'students','user':'reference','password':'jaya_reference_local','ssl':False})
    update=s.put(BASE+f"/database/{db['id']}",json={'name':db['name'],'engine':'postgres','details':details},timeout=60); update.raise_for_status()
    for card in manifest['cards']:
        query=s.post(BASE+f"/card/{card['card_id']}/query",json={"ignore_cache":True},timeout=60);query.raise_for_status()
        result=query.json()
        if result.get('status')!='completed' or result['data']['rows']!=card['rows']:
            raise AssertionError('Hasil restore berbeda: '+card['name'])
    evidence={'restored':True,'verified_cards':len(manifest['cards']),'url':f"http://localhost:3301/dashboard/{manifest['dashboard_id']}",'source':'exported H2 + PostgreSQL SQL dump','expected_rows_match':True}
    (HERE/'restore_verification.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence,indent=2))

if __name__=='__main__': restore()
