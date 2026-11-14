# Pembandingan dengan proyek mandiri

Referensi ini dibuat secara terpisah. Pembandingan baru dapat dilakukan setelah proyek mandiri tersedia. Tidak ada penilaian terhadap karya yang belum diperiksa.

| Aspek | Bukti proyek referensi | Proyek mandiri | Temuan terverifikasi |
|---|---|---|---|
| Sumber & integritas data | `reports/metrics.json`: URL dan SHA256 | Belum diberikan | Belum dibandingkan |
| Definisi label & populasi | Dropout vs Graduate; Enrolled hanya dashboard | Belum diberikan | Belum dibandingkan |
| Waktu keputusan | Akhir semester satu; semester dua dilarang sebagai fitur | Belum diberikan | Belum dibandingkan |
| Pemisahan data | 2.178 train, 726 validation, 726 test | Belum diberikan | Belum dibandingkan |
| Preprocessing | Pipeline; fit dalam train/fold | Belum diberikan | Belum dibandingkan |
| Model & pemilihan ambang | Train CV AP; validation precision maksimum pada recall ≥0,80 | Belum diberikan | Belum dibandingkan |
| Hasil test | AP 0,9207; recall 0,8380; precision 0,8123; n=726 | Belum diberikan | Belum dibandingkan |
| Beban & kasus terlewat | 293 tinjauan, 55 false positive, 46 false negative | Belum diberikan | Belum dibandingkan |
| Dashboard | Metabase, 10 kartu teruji query + ekspor DB | Belum diberikan | Belum dibandingkan |
| Deployment | Lokal berjalan; cloud menunggu akun | Belum diberikan | Belum dibandingkan |
| Conclusion & tindakan | README dan notebook; asosiasi dipisahkan dari kausalitas | Belum diberikan | Belum dibandingkan |

Model yang berbeda tidak otomatis salah. Metrik dari populasi, fitur, waktu prediksi, atau split berbeda tidak dapat dibandingkan secara langsung. Tidak ada nilai referensi yang dianggap sebagai kebenaran tanpa bukti. Perbedaan hasil harus ditelusuri ke data, definisi target, pemisahan, transformasi, atau kode yang dapat dijalankan.
