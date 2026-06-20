"use client";

import React, { useState, useEffect } from "react";
import { 
  TrendingUp, 
  Search, 
  BarChart3, 
  ListFilter, 
  Award, 
  BookOpen, 
  Compass, 
  ExternalLink,
  ChevronRight,
  Info,
  CheckCircle,
  XCircle,
  FileText
} from "lucide-react";

export default function Home() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Navigation Tabs
  const [activeTab, setActiveTab] = useState("metrics"); // 'metrics', 'ranking', 'detail'
  
  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [recommendationFilter, setRecommendationFilter] = useState("ALL");

  useEffect(() => {
    fetch("/api/data")
      .then((res) => {
        if (!res.ok) throw new Error("Gagal mengambil data dari filesystem.");
        return res.json();
      })
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#09090b] text-white">
        <div className="relative flex items-center justify-center">
          <div className="h-16 w-16 animate-spin rounded-full border-4 border-cyan-500/30 border-t-cyan-500"></div>
          <div className="absolute font-mono text-xs text-cyan-400">LOADING</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#09090b] p-6 text-white text-center">
        <XCircle className="h-16 w-16 text-rose-500 mb-4 animate-bounce" />
        <h2 className="text-2xl font-bold text-rose-400 mb-2">Error Loading Data</h2>
        <p className="text-zinc-400 max-w-md mb-6">{error}</p>
        <div className="bg-zinc-900 border border-zinc-800 p-4 rounded-lg text-left text-xs font-mono text-zinc-300 max-w-lg mb-6">
          Pastikan Anda sudah menjalankan seluruh eksperimen menggunakan script <code className="text-cyan-400">python run_all.py</code> di folder Tugas Jurnal terlebih dahulu.
        </div>
        <button 
          onClick={() => window.location.reload()} 
          className="px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 font-medium transition-colors"
        >
          Coba Lagi
        </button>
      </div>
    );
  }

  const { baseline, evaluation } = data;

  // Extract list for rankings
  const baselineList = baseline.students || [];
  const evalMetrics = evaluation || {};

  const studentsData = baselineList.map((s) => ({
    name: s.nama_siswa,
    school: s.sekolah || "-",
    bidang: s.bidang || "-",
    prestasi: s.prestasi || "-",
    rankBase: s.rank || 999,
    scoreBase: s.final_score || 0,
    rekoBase: s.rekomendasi || "TIDAK TERDETEKSI",
    postUrl: s.best_post_url || "#",
    caption: s.best_post_snippet || "",
  })).sort((a, b) => a.rankBase - b.rankBase);

  // Filtered lists
  const filteredStudents = studentsData.filter(s => {
    const matchesSearch = s.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          s.school.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          s.bidang.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (recommendationFilter === "ALL") return matchesSearch;
    return matchesSearch && s.rekoBase === recommendationFilter;
  });

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 selection:bg-cyan-500 selection:text-black">
      
      {/* Glow effects background */}
      <div className="absolute top-0 left-1/4 h-[500px] w-[500px] rounded-full bg-cyan-900/10 blur-[120px] pointer-events-none"></div>
      <div className="absolute top-1/3 right-1/4 h-[600px] w-[600px] rounded-full bg-cyan-950/5 blur-[130px] pointer-events-none"></div>

      {/* HEADER SECTION */}
      <header className="border-b border-zinc-800/80 bg-zinc-950/50 backdrop-blur sticky top-0 z-40">
        <div className="mx-auto max-w-7xl px-6 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-cyan-600 to-cyan-400 text-white shadow-lg">
              <Compass className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                IR Student Recommendation Dashboard
                <span className="text-xs font-normal py-0.5 px-2 rounded-full bg-zinc-800 border border-zinc-700 text-zinc-400">
                  Lexical Model
                </span>
              </h1>
              <p className="text-xs text-zinc-400">Pencarian Siswa SMA Berprestasi: TF-IDF + BM25 + Analisis Engagement</p>
            </div>
          </div>
          
          {/* Quick Stats Grid */}
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="px-3 py-1.5 rounded-lg bg-zinc-900/60 border border-zinc-800 flex flex-col items-center">
              <span className="text-zinc-500">CORPUS SIZE</span>
              <span className="text-cyan-400 font-bold">914 Posts</span>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-zinc-900/60 border border-zinc-800 flex flex-col items-center">
              <span className="text-zinc-500">CANDIDATES</span>
              <span className="text-cyan-300 font-bold">100 Students</span>
            </div>
          </div>
        </div>
      </header>

      {/* DASHBOARD CONTAINER */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        
        {/* STATS OVERVIEW CARDS */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          
          <div className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-800 hover:border-zinc-700 transition-all flex justify-between items-start">
            <div>
              <span className="text-xs text-zinc-500 font-medium uppercase tracking-wider block">Mean Average Precision (MAP)</span>
              <span className="text-3xl font-extrabold tracking-tight text-cyan-400 font-mono mt-1 block">
                {(evalMetrics?.baseline_metrics?.map * 100).toFixed(2)}%
              </span>
              <span className="text-[10px] text-zinc-400 mt-2 block">Stabilitas perankingan sistem</span>
            </div>
            <div className="p-2 rounded-lg bg-cyan-950/50 text-cyan-400 border border-cyan-800/30">
              <Award className="h-5 w-5" />
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-800 hover:border-zinc-700 transition-all flex justify-between items-start">
            <div>
              <span className="text-xs text-zinc-500 font-medium uppercase tracking-wider block">Precision@5</span>
              <span className="text-3xl font-extrabold tracking-tight text-cyan-300 font-mono mt-1 block">
                {(evalMetrics?.baseline_metrics?.["precision@5"] * 100).toFixed(2)}%
              </span>
              <span className="text-[10px] text-zinc-400 mt-2 block">Akurasi pada 5 rekomendasi teratas</span>
            </div>
            <div className="p-2 rounded-lg bg-cyan-900/40 text-cyan-300 border border-cyan-800/30">
              <TrendingUp className="h-5 w-5" />
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-800 hover:border-zinc-700 transition-all flex justify-between items-start">
            <div>
              <span className="text-xs text-zinc-500 font-medium uppercase tracking-wider block">NDCG@50</span>
              <span className="text-3xl font-extrabold tracking-tight text-emerald-400 font-mono mt-1 block">
                {(evalMetrics?.baseline_metrics?.["ndcg@50"] * 100).toFixed(2)}%
              </span>
              <span className="text-[10px] text-zinc-400 mt-2 block">Kualitas prioritas peringkat siswa</span>
            </div>
            <div className="p-2 rounded-lg bg-emerald-950/50 text-emerald-400 border border-emerald-800/30">
              <BarChart3 className="h-5 w-5" />
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-800 hover:border-zinc-700 transition-all flex justify-between items-start">
            <div>
              <span className="text-xs text-zinc-500 font-medium uppercase tracking-wider block">Ground Truth Relevan</span>
              <span className="text-3xl font-extrabold tracking-tight text-purple-400 font-mono mt-1 block">
                {evalMetrics?.metadata?.total_ground_truth_relevant} / {evalMetrics?.metadata?.total_candidates}
              </span>
              <span className="text-[10px] text-zinc-400 mt-2 block">74.0% Akurasi Validasi Entitas Siswa</span>
            </div>
            <div className="p-2 rounded-lg bg-purple-950/50 text-purple-400 border border-purple-800/30">
              <FileText className="h-5 w-5" />
            </div>
          </div>

        </section>

        {/* NAVIGATION TAB BUTTONS */}
        <div className="flex border-b border-zinc-800/80 mb-6 gap-2 overflow-x-auto pb-1">
          <button 
            onClick={() => setActiveTab("metrics")}
            className={`px-4 py-2 text-sm font-semibold rounded-t-lg border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${activeTab === 'metrics' ? 'border-cyan-500 text-cyan-400 bg-cyan-950/10' : 'border-transparent text-zinc-400 hover:text-zinc-200'}`}
          >
            <BarChart3 className="h-4 w-4" />
            Evaluasi Kinerja @K
          </button>
          <button 
            onClick={() => setActiveTab("ranking")}
            className={`px-4 py-2 text-sm font-semibold rounded-t-lg border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${activeTab === 'ranking' ? 'border-cyan-500 text-cyan-400 bg-cyan-950/10' : 'border-transparent text-zinc-400 hover:text-zinc-200'}`}
          >
            <ListFilter className="h-4 w-4" />
            Daftar Rekomendasi Siswa
          </button>
          <button 
            onClick={() => setActiveTab("detail")}
            className={`px-4 py-2 text-sm font-semibold rounded-t-lg border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${activeTab === 'detail' ? 'border-cyan-500 text-cyan-400 bg-cyan-950/10' : 'border-transparent text-zinc-400 hover:text-zinc-200'}`}
          >
            <Search className="h-4 w-4" />
            Pencarian Detail Siswa
          </button>
        </div>

        {/* TAB 1: EVALUATION METRICS */}
        {activeTab === "metrics" && (
          <div className="space-y-8 animate-fadeIn">
            
            {/* Visual Custom Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              
              {/* Chart 1: Bar Chart Comparison */}
              <div className="p-6 rounded-2xl bg-zinc-900/30 border border-zinc-800">
                <h3 className="text-md font-bold mb-6 text-white flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-cyan-400" />
                  Performa Sistem Leksikal Diusulkan (TF-IDF + BM25 + Engagement)
                </h3>
                
                <div className="space-y-6">
                  {["precision@5", "precision@10", "precision@20", "precision@50", "map", "ndcg@10", "ndcg@50"].map((metric) => {
                    const valBase = evalMetrics.baseline_metrics[metric] || 0;
                    
                    return (
                      <div key={metric} className="space-y-2">
                        <div className="flex justify-between text-xs font-semibold">
                          <span className="font-mono uppercase text-zinc-400">{metric.replace("@", " @ ")}</span>
                          <span className="text-zinc-300">
                            Score: <span className="text-cyan-400 font-mono">{(valBase).toFixed(4)}</span>
                          </span>
                        </div>
                        
                        {/* Single bar progress */}
                        <div className="h-3 w-full bg-zinc-800/50 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-cyan-600 to-cyan-400 rounded-full transition-all duration-1000"
                            style={{ width: `${valBase * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Chart 2: Precision@K and Recall@K curves */}
              <div className="p-6 rounded-2xl bg-zinc-900/30 border border-zinc-800 flex flex-col justify-between">
                <div>
                  <h3 className="text-md font-bold mb-6 text-white flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-emerald-400" />
                    Perbandingan Presisi vs Recall pada berbagai level K
                  </h3>
                  
                  {/* Grid for two small charts */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    
                    {/* Precision Chart Curve */}
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold text-center text-zinc-400 uppercase tracking-wider">Precision @ K</h4>
                      
                      <div className="h-40 bg-zinc-950/80 rounded-xl p-3 border border-zinc-800 relative flex items-end justify-between font-mono text-[10px]">
                        {/* Axes helper lines */}
                        <div className="absolute inset-x-0 bottom-1/4 border-b border-zinc-800/50"></div>
                        <div className="absolute inset-x-0 bottom-1/2 border-b border-zinc-800/50"></div>
                        <div className="absolute inset-x-0 bottom-3/4 border-b border-zinc-800/50"></div>

                        {/* Bars for Precision @ 5, 10, 20, 50 */}
                        {[5, 10, 20, 50].map((k) => {
                          const baseVal = evalMetrics.baseline_metrics[`precision@${k}`] || 0;
                          return (
                            <div key={k} className="flex flex-col items-center h-full justify-end z-10 w-10">
                              <div className="flex gap-1 h-32 items-end justify-center w-full">
                                <div 
                                  className="w-5 bg-cyan-500 rounded-t transition-all duration-700" 
                                  style={{ height: `${baseVal * 80}%` }}
                                  title={`Baseline P@${k}: ${baseVal}`}
                                ></div>
                              </div>
                              <span className="text-zinc-500 font-bold mt-1">@{k}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Recall Chart Curve */}
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold text-center text-zinc-400 uppercase tracking-wider">Recall @ K</h4>
                      
                      <div className="h-40 bg-zinc-950/80 rounded-xl p-3 border border-zinc-800 relative flex items-end justify-between font-mono text-[10px]">
                        {/* Axes helper lines */}
                        <div className="absolute inset-x-0 bottom-1/4 border-b border-zinc-800/50"></div>
                        <div className="absolute inset-x-0 bottom-1/2 border-b border-zinc-800/50"></div>
                        <div className="absolute inset-x-0 bottom-3/4 border-b border-zinc-800/50"></div>

                        {/* Bars for Recall @ 5, 10, 20, 50 */}
                        {[5, 10, 20, 50].map((k) => {
                          const baseVal = evalMetrics.baseline_metrics[`recall@${k}`] || 0;
                          return (
                            <div key={k} className="flex flex-col items-center h-full justify-end z-10 w-10">
                              <div className="flex gap-1 h-32 items-end justify-center w-full">
                                <div 
                                  className="w-5 bg-emerald-500 rounded-t transition-all duration-700" 
                                  style={{ height: `${baseVal * 80}%` }}
                                  title={`Baseline R@${k}: ${baseVal}`}
                                ></div>
                              </div>
                              <span className="text-zinc-500 font-bold mt-1">@{k}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                  </div>
                </div>

                <div className="bg-zinc-950/40 p-4 border border-zinc-800/80 rounded-xl mt-6 text-xs text-zinc-400 leading-relaxed">
                  <div className="font-bold text-zinc-300 mb-1 flex items-center gap-1.5">
                    <Info className="h-3.5 w-3.5 text-cyan-400" />
                    Interpretasi Teoretis IR Leksikal:
                  </div>
                  Pencarian Leksikal yang diusulkan unggul sempurna di K=5 (Precision@5 = 1.0000) karena pencocokan istilah spesifik (seperti "OSN", "medali") diposisikan di urutan teratas. Nilai Recall terus meningkat hingga 50.0% pada K=50, menunjukkan efektivitas penyaringan kata kunci dan pembobotan interaksi media sosial.
                </div>
              </div>

            </div>

            {/* Complete Metrics Table */}
            <div className="p-6 rounded-2xl bg-zinc-900/30 border border-zinc-800">
              <h3 className="text-md font-bold mb-4 text-white">Tabel Lengkap Metrik Evaluasi Sistem</h3>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-400 font-semibold text-xs uppercase tracking-wider">
                      <th className="py-3 px-4">Metrik Evaluasi</th>
                      <th className="py-3 px-4 text-cyan-400">Skor Sistem (TF-IDF + BM25 + Engagement)</th>
                      <th className="py-3 px-4">Signifikansi & Dampak Rekomendasi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60 font-mono text-xs">
                    {Object.keys(evalMetrics.baseline_metrics || {}).sort().map((metric) => {
                      const baseVal = evalMetrics.baseline_metrics[metric];
                      
                      return (
                        <tr key={metric} className="hover:bg-zinc-900/10 transition-colors">
                          <td className="py-3.5 px-4 font-bold text-zinc-300 uppercase tracking-tight">{metric.replace("@", " @ ")}</td>
                          <td className="py-3.5 px-4 text-cyan-400 font-bold text-sm">{baseVal.toFixed(4)}</td>
                          <td className="py-3.5 px-4 text-zinc-400 font-sans">
                            {metric.startsWith("precision") && "Proporsi siswa berprestasi riil (lolos verifikasi) di antara kandidat hasil pencarian."}
                            {metric.startsWith("recall") && "Rasio temuan siswa berprestasi yang berhasil dijaring oleh sistem dibandingkan total yang ada."}
                            {metric.startsWith("ndcg") && "Keakuratan penempatan siswa dengan prestasi tertinggi di peringkat-peringkat awal."}
                            {metric === "map" && "Kerapatan presisi teragregasi di seluruh data hasil temu kembali informasi."}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}

        {/* TAB 2: RECOMMENDATION LIST / RANKING */}
        {activeTab === "ranking" && (
          <div className="space-y-6 animate-fadeIn">
            
            {/* Table filters */}
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
              <div className="relative w-full sm:max-w-md">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
                <input 
                  type="text" 
                  placeholder="Cari siswa, sekolah, atau bidang..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-cyan-500 text-zinc-200"
                />
              </div>

              <div className="flex items-center gap-2 text-xs w-full sm:w-auto overflow-x-auto">
                <span className="text-zinc-500 font-bold whitespace-nowrap">Filter Status:</span>
                {["ALL", "SANGAT DIREKOMENDASIKAN", "DIREKOMENDASIKAN", "PERTIMBANGKAN"].map((f) => (
                  <button
                    key={f}
                    onClick={() => setRecommendationFilter(f)}
                    className={`px-3 py-1 rounded-full border transition-all whitespace-nowrap ${recommendationFilter === f ? 'bg-zinc-800 text-white border-zinc-700' : 'bg-transparent text-zinc-500 border-transparent hover:text-zinc-300'}`}
                  >
                    {f === 'ALL' ? 'Semua' : f.replace("DIREKOMENDASIKAN", "REKO")}
                  </button>
                ))}
              </div>
            </div>

            {/* Recommendation Table */}
            <div className="border border-zinc-800 bg-zinc-900/10 rounded-2xl overflow-hidden">
              <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead className="bg-zinc-950/80 backdrop-blur sticky top-0 z-10">
                    <tr className="border-b border-zinc-800 text-zinc-400 font-semibold text-xs uppercase tracking-wider">
                      <th className="py-3 px-4">Rank</th>
                      <th className="py-3 px-4">Nama Siswa</th>
                      <th className="py-3 px-4">Sekolah</th>
                      <th className="py-3 px-4">Bidang</th>
                      <th className="py-3 px-4 text-cyan-400">Skor Akhir</th>
                      <th className="py-3 px-4">Status Rekomendasi</th>
                      <th className="py-3 px-4 text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60 text-xs">
                    {filteredStudents.map((s) => {
                      const isNoiseBase = s.name === "dalam menimba ilmu" || s.name === "menerima apresiasi langsung" || s.name === "sobat";
                      
                      return (
                        <tr key={s.name} className={`hover:bg-zinc-800/40 transition-colors ${isNoiseBase ? "bg-rose-950/5" : ""}`}>
                          <td className="py-3 px-4 font-mono font-bold text-zinc-400">{s.rankBase}</td>
                          <td className="py-3 px-4 font-bold text-zinc-200">
                            <span className="flex items-center gap-1.5">
                              {s.name}
                              {isNoiseBase && (
                                <span className="py-0.5 px-1 bg-rose-950 border border-rose-800/60 text-[9px] text-rose-400 rounded">
                                  Noise NER
                                </span>
                              )}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-zinc-400 max-w-[200px] truncate">{s.school}</td>
                          <td className="py-3 px-4 text-zinc-400">{s.bidang}</td>
                          <td className="py-3 px-4 font-mono font-bold text-cyan-400">{s.scoreBase.toFixed(4)}</td>
                          <td className="py-3 px-4">
                            <span className={`px-2.5 py-1 rounded-full font-sans font-bold text-[9px] ${
                              s.rekoBase === "SANGAT DIREKOMENDASIKAN" ? "bg-emerald-950 text-emerald-400 border border-emerald-800/30" :
                              s.rekoBase === "DIREKOMENDASIKAN" ? "bg-cyan-950 text-cyan-400 border border-cyan-800/30" :
                              s.rekoBase === "PERTIMBANGKAN" ? "bg-yellow-950 text-yellow-400 border border-yellow-800/30" :
                              "bg-zinc-950 text-zinc-500 border border-zinc-800"
                            }`}>
                              {s.rekoBase}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <button
                              onClick={() => setSelectedStudent(s)}
                              className="px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition-colors font-sans hover:text-white"
                            >
                              Detail
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}

        {/* TAB 3: DETAILED PROFILE VIEW */}
        {activeTab === "detail" && (
          <div className="space-y-6 animate-fadeIn">
            
            <div className="p-6 rounded-2xl bg-zinc-900/30 border border-zinc-800">
              <h3 className="text-md font-bold mb-2 text-white">Profil Detail & Pembobotan Siswa</h3>
              <p className="text-xs text-zinc-500 mb-6">Analisis teks caption, skor relevansi leksikal, dan parameter engagement untuk setiap penerima rekomendasi.</p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Candidates List Column */}
                <div className="border border-zinc-800 bg-zinc-950 rounded-xl overflow-hidden flex flex-col h-[500px]">
                  <div className="p-3 border-b border-zinc-800 bg-zinc-900/40 relative">
                    <Search className="absolute left-6 top-5.5 h-3.5 w-3.5 text-zinc-500" />
                    <input 
                      type="text" 
                      placeholder="Cari nama siswa..." 
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-1.5 pl-9 pr-3 text-xs focus:outline-none focus:border-cyan-500 text-zinc-200"
                    />
                  </div>
                  
                  <div className="overflow-y-auto divide-y divide-zinc-900/60 flex-1">
                    {filteredStudents.map((s) => (
                      <button
                        key={s.name}
                        onClick={() => setSelectedStudent(s)}
                        className={`w-full text-left p-3.5 transition-colors flex justify-between items-center ${selectedStudent?.name === s.name ? "bg-cyan-950/20 text-cyan-400 border-l-2 border-cyan-500" : "hover:bg-zinc-900/50 text-zinc-300"}`}
                      >
                        <div className="truncate pr-2">
                          <span className="font-semibold text-xs block truncate">{s.name}</span>
                          <span className="text-[10px] text-zinc-500 block truncate">{s.school}</span>
                        </div>
                        <ChevronRight className="h-3.5 w-3.5 text-zinc-600 flex-shrink-0" />
                      </button>
                    ))}
                  </div>
                </div>

                {/* Candidate Detail Profile Column (Span 2) */}
                <div className="md:col-span-2 border border-zinc-800 bg-zinc-950/40 rounded-xl p-6 h-[500px] overflow-y-auto">
                  {selectedStudent ? (
                    <div className="space-y-6">
                      
                      {/* Name Card */}
                      <div className="flex justify-between items-start border-b border-zinc-800/80 pb-4">
                        <div>
                          <h4 className="text-lg font-bold text-white flex items-center gap-2">
                            {selectedStudent.name}
                          </h4>
                          <p className="text-xs text-zinc-400 mt-1">{selectedStudent.school} | Bidang {selectedStudent.bidang}</p>
                        </div>
                        <a 
                          href={selectedStudent.postUrl}
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 font-semibold font-mono"
                        >
                          OPEN INSTAGRAM
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      </div>

                      {/* Score Comparison Cards */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        
                        {/* Lexical card */}
                        <div className="p-4 rounded-xl bg-cyan-950/10 border border-cyan-800/20">
                          <span className="text-[10px] text-cyan-400 font-bold block uppercase tracking-wider">Skor Akhir Rekomendasi</span>
                          <div className="flex items-baseline gap-2 mt-2">
                            <span className="text-3xl font-black font-mono text-cyan-300">{selectedStudent.scoreBase.toFixed(4)}</span>
                            <span className="text-[10px] text-zinc-500 font-mono">Rank {selectedStudent.rankBase}</span>
                          </div>
                          <p className="text-[10px] text-cyan-500/80 mt-2 font-mono uppercase tracking-tight">Status: {selectedStudent.rekoBase}</p>
                        </div>

                      </div>

                      {/* Achievement and context */}
                      <div className="space-y-4">
                        <div className="p-4 rounded-xl bg-zinc-950 border border-zinc-800">
                          <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block">Prestasi Terdeteksi</span>
                          <p className="text-xs text-zinc-300 font-semibold mt-1 flex items-center gap-1.5">
                            <Award className="h-4 w-4 text-yellow-500" />
                            {selectedStudent.prestasi}
                          </p>
                        </div>

                        <div className="p-4 rounded-xl bg-zinc-950 border border-zinc-800">
                          <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block">Snippet Caption Instagram</span>
                          <blockquote className="text-xs text-zinc-400 leading-relaxed italic mt-1.5 border-l-2 border-zinc-700 pl-3">
                            "{selectedStudent.caption}"
                          </blockquote>
                        </div>
                      </div>

                    </div>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-center text-zinc-500">
                      <Award className="h-12 w-12 text-zinc-800 mb-2 animate-pulse" />
                      <p className="text-xs">Pilih salah satu siswa dari daftar di sebelah kiri untuk menganalisis data.</p>
                    </div>
                  )}
                </div>

              </div>
            </div>

          </div>
        )}

      </main>

      {/* FOOTER */}
      <footer className="border-t border-zinc-800/80 bg-zinc-950/30 py-8 mt-16 text-center text-xs text-zinc-500 font-mono">
        <div className="mx-auto max-w-7xl px-6">
          <p>© 2026 Tugas IR: Pencarian Siswa Berprestasi | Built with Next.js & Tailwind</p>
        </div>
      </footer>

      {/* POPUP DETAIL MODAL */}
      {selectedStudent && activeTab === "ranking" && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex justify-between items-start border-b border-zinc-800 pb-3">
              <div>
                <h4 className="text-md font-bold text-white">{selectedStudent.name}</h4>
                <p className="text-[11px] text-zinc-400">{selectedStudent.school}</p>
              </div>
              <button 
                onClick={() => setSelectedStudent(null)}
                className="text-zinc-500 hover:text-white font-mono text-sm"
              >
                CLOSE
              </button>
            </div>
            
            <div className="p-4 bg-cyan-950/15 border border-cyan-800/20 rounded-lg">
              <span className="text-[9px] text-cyan-400 font-bold block uppercase">Skor Akhir Rekomendasi</span>
              <span className="text-2xl font-black font-mono text-cyan-300">{selectedStudent.scoreBase.toFixed(4)}</span>
              <span className="text-[10px] text-zinc-500 block">Rank: {selectedStudent.rankBase}</span>
            </div>

            <div className="p-3 bg-zinc-950 border border-zinc-850 rounded-lg text-xs space-y-2">
              <div>
                <span className="text-[9px] text-zinc-500 font-bold block uppercase">Prestasi</span>
                <span className="text-zinc-300 font-semibold">{selectedStudent.prestasi}</span>
              </div>
              <div>
                <span className="text-[9px] text-zinc-500 font-bold block uppercase">Caption Instagram</span>
                <span className="text-zinc-400 block max-h-24 overflow-y-auto italic">"{selectedStudent.caption}"</span>
              </div>
            </div>

            <div className="flex justify-between items-center text-xs">
              <a 
                href={selectedStudent.postUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-cyan-400 hover:underline flex items-center gap-1"
              >
                Lihat Postingan Asli
                <ExternalLink className="h-3 w-3" />
              </a>
              <button 
                onClick={() => setSelectedStudent(null)}
                className="px-4 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded font-semibold transition-colors"
              >
                Tutup
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
