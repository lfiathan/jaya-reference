# Naskah demonstrasi referensi · sekitar 4 menit

**Status:** ini naskah, bukan rekaman video. Video merupakan peningkatan opsional penilaian.

**00:00–00:35 · Masalah dan data**

Jaya Jaya Institut ingin mendeteksi kebutuhan pendampingan sedini mungkin. Proyek ini menggunakan data publik 4.424 mahasiswa dari Portugal untuk skenario institusi fiktif. Ada 1.421 Dropout, 2.209 Graduate, dan 794 Enrolled. Dropout historis mencakup 32,12 persen seluruh catatan.

**00:35–01:30 · Solusi machine learning**

Model digunakan setelah semester pertama. Sepuluh fitur meliputi program studi, waktu kuliah, nilai kualifikasi dan penerimaan, serta enam indikator akademik semester satu. Semester dua tidak digunakan. Outcome Enrolled belum selesai, sehingga tidak dianggap sebagai Graduate pada pelatihan. Data outcome selesai dibagi menjadi train, validation, dan test. Empat kandidat dibandingkan dengan cross-validation pada train. Logistic regression memperoleh AP terbaik. Ambang dipilih pada validation, tanpa menggunakan test untuk pemilihan.

**01:30–02:15 · Hasil dan prototipe**

Pada 726 catatan test, AP sebesar 0,921, recall dropout 83,80 persen dan precision 81,23 persen. Model mendeteksi 238 dropout, melewatkan 46, dan menghasilkan 55 false positive. Tunjukkan formulir Streamlit, masukkan profil ilustratif tanpa identitas, lalu klik Lihat sinyal pendampingan. Skor membantu menentukan siapa yang perlu diajak berbicara; skor bukan kepastian. Tunjukkan opsi CSV dan penjelasan model.

**02:15–03:10 · Dashboard**

Buka Metabase. Tunjukkan total catatan, proporsi dropout, Enrolled, dan rata-rata nilai semester satu. Baca distribusi status, indikator unit lulus, serta asosiasi pembayaran dan beasiswa dengan dropout. Selalu tunjukkan ukuran kelompok dan penyebut. Dashboard ini merupakan snapshot historis, bukan live monitoring atau tren waktu, karena data tidak memiliki tanggal.

**03:10–04:00 · Kesimpulan dan tindakan**

Model menunjukkan kemampuan membedakan outcome historis. Hasil belum membuktikan kemampuan yang sama pada mahasiswa aktif atau penurunan dropout setelah intervensi. Usulan tindakan: pilot tinjauan oleh pembimbing, dukungan belajar, konsultasi bantuan keuangan, pengumpulan snapshot bertanggal, dan evaluasi retensi. Akhiri dengan status deployment aktual; jangan menyatakan aplikasi cloud sudah aktif sebelum URL dan akses reviewer diverifikasi.
