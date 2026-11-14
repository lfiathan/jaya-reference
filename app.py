"""Student-support reference prototype. Run: streamlit run app.py."""
import json
import joblib
import pandas as pd
import plotly.express as px
import streamlit as st
from src.common import ROOT, FEATURES, SEM, COURSES, load_data, validate_inputs

st.set_page_config(page_title="Jaya Jaya · Student Success",page_icon="🎓",layout="wide")
st.markdown("""<style>.block-container{max-width:1250px;padding-top:2.4rem}h1{letter-spacing:-.035em}div[data-testid=stMetric]{background:#f0f5f4;border-radius:12px;padding:18px}div[data-testid=stMetric] *{color:#163f3d}footer{visibility:hidden}</style>""",unsafe_allow_html=True)

@st.cache_resource
def resources():
    return joblib.load(ROOT/"model/dropout_model.joblib"),json.loads((ROOT/"reports/metrics.json").read_text())

bundle, report=resources()
st.caption("JAYA JAYA INSTITUT  /  STUDENT SUCCESS")
st.title("Kenali kebutuhan. Mulai pendampingan.")
st.write("Pantau hasil akademik dan gunakan sinyal akhir semester satu untuk membantu merencanakan percakapan dengan mahasiswa.")
page=st.sidebar.radio("Ruang kerja",["Prediksi individual","Prediksi CSV","Dashboard","Tentang model"])
st.sidebar.info("Prototipe berbasis data historis Portugal. Perlu validasi lokal sebelum dipakai untuk layanan nyata.")

def show_result(frame):
    x=validate_inputs(frame)
    p=bundle["pipeline"].predict_proba(x)[:,1]
    output=x.copy()
    output["skor_dropout"]=p
    output["perlu_tinjauan"]=p>=bundle["threshold"]
    return output

if page=="Prediksi individual":
    st.subheader("Mulai dari satu mahasiswa")
    st.caption("Isi data yang sudah tersedia pada akhir semester satu. Nilai penerimaan memakai skala 0–200; nilai semester memakai skala 0–20.")
    with st.form("student"):
        c1,c2=st.columns(2)
        with c1:
            course=st.selectbox("Program studi",list(COURSES),format_func=lambda c:COURSES[c],index=list(COURSES).index(9147))
            daytime=st.selectbox("Waktu kuliah",[1,0],format_func=lambda v:"Siang" if v else "Malam")
            previous=st.number_input("Nilai kualifikasi sebelumnya (0–200)",0.,200.,130.)
            admission=st.number_input("Nilai masuk (0–200)",0.,200.,125.)
        with c2:
            credited=st.number_input("Unit yang diakui / credited",0,100,0)
            enrolled=st.number_input("Unit yang diambil",0,100,6)
            evaluations=st.number_input("Jumlah evaluasi",0,200,8)
            approved=st.number_input("Unit yang lulus",0,100,4)
            grade=st.number_input("Rata-rata nilai semester (0–20)",0.,20.,12.)
            without=st.number_input("Unit tanpa evaluasi",0,100,0)
        submitted=st.form_submit_button("Lihat sinyal pendampingan",type="primary")
    if submitted:
        values=[course,daytime,previous,admission,credited,enrolled,evaluations,approved,grade,without]
        try:
            out=show_result(pd.DataFrame([values],columns=FEATURES))
            score=out.skor_dropout.iloc[0]
            flagged=bool(out.perlu_tinjauan.iloc[0])
            st.metric("Skor model",f"{score:.1%}")
            if flagged:
                st.warning("Prioritaskan tinjauan pendampingan")
            else:
                st.success("Pendampingan rutin; tetap pantau perkembangan")
            st.write(f"Ambang tinjauan yang dipilih dari validasi: {bundle['threshold']:.3f}. Skor ini merupakan estimasi model pada populasi berlabel selesai (Dropout/Graduate), bukan kepastian atau peluang terkalibrasi untuk seluruh mahasiswa aktif.")
            st.info("Tindak lanjut: verifikasi data, diskusikan hambatan belajar, dan susun rencana bersama dosen pembimbing. Jangan gunakan skor sebagai dasar sanksi atau pembatasan akses pendidikan.")
        except ValueError as exc:
            st.error(str(exc))
elif page=="Prediksi CSV":
    st.subheader("Tinjau satu kelompok")
    st.write("Unggah CSV berkoma dengan 10 kolom sesuai contoh. Nama/identitas tidak diperlukan; hasil mempertahankan urutan baris. Data unggahan diproses dalam sesi dan tidak ditulis ke berkas oleh aplikasi.")
    sample=load_data()[FEATURES].head(3)
    st.download_button("Unduh contoh CSV",sample.to_csv(index=False),"contoh_input.csv","text/csv")
    upload=st.file_uploader("CSV data akhir semester satu",type=["csv"])
    if upload is not None:
        try:
            frame=pd.read_csv(upload)
            if len(frame)>10000:
                raise ValueError("Maksimum 10.000 baris per unggahan.")
            out=show_result(frame)
            st.metric("Perlu tinjauan",int(out.perlu_tinjauan.sum()))
            st.dataframe(out,width='stretch')
            st.download_button("Unduh hasil",out.to_csv(index=False),"hasil_pendampingan.csv","text/csv")
        except (ValueError,pd.errors.ParserError,pd.errors.EmptyDataError) as exc:
            st.error(str(exc))
elif page=="Dashboard":
    st.subheader("Gambaran hasil & performa mahasiswa")
    df=load_data()
    choices=st.multiselect("Program studi",list(COURSES),format_func=lambda c:COURSES[c])
    if choices:
        df=df[df.Course.isin(choices)]
    if df.empty:
        st.info("Tidak ada mahasiswa pada filter ini.")
        st.stop()
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Seluruh catatan",f"{len(df):,}")
    c2.metric("Dropout / seluruh catatan",f"{df.Status.eq('Dropout').mean():.1%}")
    c3.metric("Enrolled / belum selesai",f"{df.Status.eq('Enrolled').sum():,}")
    c4.metric("Rata-rata nilai semester 1",f"{df[SEM+'grade'].mean():.2f}/20")
    st.caption("Snapshot historis; tidak memuat tanggal untuk tren waktu. Status Enrolled dipertahankan. Angka dropout di sini menggunakan seluruh catatan sebagai penyebut, berbeda dari populasi evaluasi model.")
    colors={"Dropout":"#c45535","Graduate":"#19756c","Enrolled":"#d9ae4b"}
    c1,c2=st.columns(2)
    counts=df.Status.value_counts().rename_axis("Status").reset_index(name="Mahasiswa")
    c1.plotly_chart(px.bar(counts,x="Status",y="Mahasiswa",color="Status",color_discrete_map=colors,title="Komposisi hasil akhir"),width='stretch')
    rates=df.groupby("Tuition_fees_up_to_date").Status.agg(n="size",dropout=lambda s:s.eq("Dropout").sum()).reset_index()
    rates["Dropout (%)"]=100*rates.dropout/rates.n
    rates["Pembayaran"]=rates.Tuition_fees_up_to_date.map({0:"Belum mutakhir",1:"Mutakhir"})
    c2.plotly_chart(px.bar(rates,x="Pembayaran",y="Dropout (%)",text="n",range_y=[0,100],title="Asosiasi pembayaran & dropout; label = n"),width='stretch')
    c1,c2=st.columns(2)
    c1.plotly_chart(px.box(df,x="Status",y=SEM+"approved",color="Status",color_discrete_map=colors,title="Distribusi unit lulus semester 1"),width='stretch')
    group=df.groupby("Course").Status.agg(n="size",dropout=lambda s:s.eq("Dropout").sum()).reset_index()
    group["Dropout (%)"]=100*group.dropout/group.n
    group["Program studi"]=group.Course.map(COURSES)
    c2.plotly_chart(px.bar(group.sort_values("Dropout (%)"),x="Dropout (%)",y="Program studi",orientation="h",text="n",range_x=[0,100],title="Dropout menurut program; label = n",height=600),width='stretch')
    st.info("Perbedaan antarkelompok merupakan asosiasi, tidak membuktikan sebab-akibat. Tinjau ukuran kelompok dan konteks sebelum memilih intervensi.")
else:
    st.subheader("Bukti & batas penggunaan")
    m=report["test"]
    c1,c2,c3=st.columns(3)
    c1.metric("Recall dropout · test",f"{m['recall']:.1%}")
    c2.metric("Precision · test",f"{m['precision']:.1%}")
    c3.metric("Average precision · test",f"{m['pr_auc_ap']:.3f}")
    st.write(f"Model: {report['selected_model']}. Pemilihan model: 5-fold CV hanya pada train. Ambang dipilih pada validation; test {m['n']} baris disimpan terpisah. Data Enrolled tidak dipakai sebagai label negatif.")
    st.write("Fitur: program studi, waktu kuliah, nilai sebelumnya, nilai masuk, dan enam indikator semester satu. Semester dua, demografi, keuangan, dan ekonomi tidak dipakai model. Waktu pencatatan historis belum dapat diverifikasi secara independen.")
    st.write("Pemindahan hasil ke mahasiswa aktif berisiko pergeseran populasi. Diperlukan uji prospektif, pemeriksaan kalibrasi dan per kelompok, persetujuan tata kelola, serta pemantauan drift. Data ini berasal dari Portugal dan dipakai dalam skenario institusi fiktif.")
    st.link_button("Sumber dataset & kamus", "https://github.com/dicodingacademy/dicoding_dataset/blob/main/students_performance/README.md")
