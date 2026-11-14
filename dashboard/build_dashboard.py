"""Create a fresh reference dashboard via the local Metabase API."""
import json
import sys
from pathlib import Path
import requests

BASE=sys.argv[1] if len(sys.argv)>1 else "http://localhost:3300"
HERE=Path(__file__).resolve().parent
s=requests.Session()
def api(method,path,data=None):
    r=s.request(method,BASE+"/api"+path,json=data,timeout=90)
    if not r.ok:
        raise RuntimeError(f"{method} {path}: {r.status_code}: {r.text[:1000]}")
    return r.json() if r.content else None

props=api("GET","/session/properties")
if props.get("setup-token"):
    token=api("POST","/setup",{"token":props["setup-token"],"user":{"first_name":"Reference","last_name":"Reviewer","email":"root@mail.com","password":"Root123!reference"},"prefs":{"site_name":"Jaya Jaya · Student Success","site_locale":"en","allow_tracking":False}})["id"]
else:
    token=api("POST","/session",{"username":"root@mail.com","password":"Root123!reference"})["id"]
s.headers["X-Metabase-Session"]=token
databases=api("GET","/database")["data"]
db=next((d for d in databases if d["name"]=="Jaya Jaya Students"),None)
if not db:
    db=api("POST","/database",{"name":"Jaya Jaya Students","engine":"postgres","details":{"host":"host.docker.internal","port":55432,"dbname":"students","user":"reference","password":"jaya_reference_local","ssl":False},"is_full_sync":True})
dbid=db["id"]
dash=api("POST","/dashboard",{"name":"Jaya Jaya | Student Success Overview","description":"Snapshot historis 4.424 mahasiswa. Dropout / seluruh catatan; Enrolled bukan Graduate. Asosiasi bukan sebab-akibat. Tanpa tanggal kohort, tren waktu tidak tersedia.","parameters":[]})

specs=[
("Seluruh mahasiswa", "SELECT COUNT(*) AS mahasiswa FROM students", "scalar",{},0,0,6,3),
("Dropout / seluruh catatan (%)", "SELECT ROUND(100.0*COUNT(*) FILTER(WHERE status='Dropout')/COUNT(*),2) AS dropout_persen FROM students", "scalar",{},0,6,6,3),
("Enrolled | hasil belum selesai", "SELECT COUNT(*) AS enrolled FROM students WHERE status='Enrolled'", "scalar",{},0,12,6,3),
("Nilai semester 1 | skala 0–20", "SELECT ROUND(AVG(curricular_units_1st_sem_grade)::numeric,2) AS nilai FROM students", "scalar",{},0,18,6,3),
("Komposisi status | jumlah mahasiswa", "SELECT status,COUNT(*) AS mahasiswa FROM students GROUP BY status ORDER BY mahasiswa DESC", "bar",{"graph.dimensions":["status"],"graph.metrics":["mahasiswa"],"graph.colors":["#19756c"],"graph.y_axis.min":0,"graph.show_values":True},3,0,12,7),
("Pembayaran & dropout (%) | ukuran kelompok di bawah", "SELECT CASE WHEN tuition_fees_up_to_date=1 THEN 'Mutakhir' ELSE 'Belum mutakhir' END AS pembayaran,ROUND(100.0*COUNT(*) FILTER(WHERE status='Dropout')/COUNT(*),2) AS dropout_persen,COUNT(*) AS n FROM students GROUP BY tuition_fees_up_to_date ORDER BY dropout_persen DESC", "bar",{"graph.dimensions":["pembayaran"],"graph.metrics":["dropout_persen"],"graph.colors":["#c45535"],"graph.y_axis.min":0,"graph.y_axis.max":100,"graph.y_axis.auto_range":False,"graph.show_values":True},3,12,12,7),
("Unit lulus semester 1 | rata-rata menurut status", "SELECT status,ROUND(AVG(curricular_units_1st_sem_approved)::numeric,2) AS unit_lulus,COUNT(*) AS n FROM students GROUP BY status ORDER BY unit_lulus", "bar",{"graph.dimensions":["status"],"graph.metrics":["unit_lulus"],"graph.colors":["#19756c"],"graph.y_axis.min":0,"graph.show_values":True},10,0,12,7),
("Beasiswa & dropout (%) | asosiasi historis", "SELECT CASE WHEN scholarship_holder=1 THEN 'Penerima' ELSE 'Bukan penerima' END AS beasiswa,ROUND(100.0*COUNT(*) FILTER(WHERE status='Dropout')/COUNT(*),2) AS dropout_persen,COUNT(*) AS n FROM students GROUP BY scholarship_holder ORDER BY dropout_persen DESC", "bar",{"graph.dimensions":["beasiswa"],"graph.metrics":["dropout_persen"],"graph.colors":["#c45535"],"graph.y_axis.min":0,"graph.y_axis.max":100,"graph.y_axis.auto_range":False,"graph.show_values":True},10,12,12,7),
("Ukuran kelompok pembayaran | jumlah mahasiswa", "SELECT CASE WHEN tuition_fees_up_to_date=1 THEN 'Mutakhir' ELSE 'Belum mutakhir' END AS pembayaran,COUNT(*) AS mahasiswa FROM students GROUP BY tuition_fees_up_to_date", "bar",{"graph.dimensions":["pembayaran"],"graph.metrics":["mahasiswa"],"graph.y_axis.min":0,"graph.colors":["#769793"],"graph.show_values":True},17,0,12,6),
("Ukuran kelompok beasiswa | jumlah mahasiswa", "SELECT CASE WHEN scholarship_holder=1 THEN 'Penerima' ELSE 'Bukan penerima' END AS beasiswa,COUNT(*) AS mahasiswa FROM students GROUP BY scholarship_holder", "bar",{"graph.dimensions":["beasiswa"],"graph.metrics":["mahasiswa"],"graph.y_axis.min":0,"graph.colors":["#769793"],"graph.show_values":True},17,12,12,6),
]
cards=[]
proof=[]
for i,(name,sql,display,settings,row,col,sx,sy) in enumerate(specs):
    query={"database":dbid,"type":"native","native":{"query":sql,"template-tags":{}}}
    card=api("POST","/card",{"name":name,"dataset_query":query,"display":display,"visualization_settings":settings,"description":"Data historis publik; populasi seluruh 4.424 catatan. Angka kelompok dapat diperiksa dari SQL."})
    result=api("POST",f"/card/{card['id']}/query",{"ignore_cache":True})
    if result.get("status")!="completed":
        raise RuntimeError(str(result)[:1500])
    cards.append({"id":-(i+1),"card_id":card["id"],"row":row,"col":col,"size_x":sx,"size_y":sy,"parameter_mappings":[],"visualization_settings":{}})
    proof.append({"name":name,"card_id":card["id"],"sql":sql,"rows":result["data"]["rows"]})
updated=api("PUT",f"/dashboard/{dash['id']}",{"dashcards":cards,"width":"full"})
assert len(updated["dashcards"])==len(specs)
(HERE/"dashboard_manifest.json").write_text(json.dumps({"dashboard_id":dash["id"],"url":f"{BASE}/dashboard/{dash['id']}","cards":proof},indent=2))
print(f"Created and query-verified {len(specs)} cards: {BASE}/dashboard/{dash['id']}")
