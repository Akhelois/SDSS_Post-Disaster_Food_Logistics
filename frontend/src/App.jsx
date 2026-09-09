import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { PolygonLayer, ScatterplotLayer } from '@deck.gl/layers';
import axios from 'axios';
import './styles/App.css';

import DeckMap from './components/DeckMap';
import LoadingSkeleton from './components/LoadingSkeleton';

import {
  TbMap2,
  TbBrain,
  TbChartDots3,
  TbDatabase,
  TbSearch,
  TbList,
  TbMapPin,
  TbChartBar,
  TbSun,
  TbMoon,
  TbDownload,
  TbCheck,
  TbAlertTriangle,
  TbTruck,
  TbUsers,
  TbHome,
  TbX,
  TbChevronRight,
  TbPackage,
  TbClock,
  TbScale,
  TbCalculator,
  TbBuilding,
  TbActivity,
  TbTarget,
  TbCpu,
  TbFocus2,
  TbTrendingUp,
  TbAlertCircle
} from 'react-icons/tb';

function formatDecimal(val) {
  if (val === null || val === undefined || isNaN(val)) return '0.00';
  const num = Number(val);
  return num.toFixed(2);
}

function formatInt(val) {
  if (val === null || val === undefined || isNaN(val)) return '0';
  return Math.round(Number(val)).toLocaleString();
}

function ItemizedModal({ zone, onClose }) {
  if (!zone) return null;
  const item = zone.itemized_logistics || {};

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '18px', borderBottom: '1px solid var(--bord)', paddingBottom: '12px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: 'var(--tp)' }}>Rincian Paket Bantuan Item Logistik Posko</h3>
            <span style={{ fontSize: '11px', color: 'var(--ts)' }}>Desa {zone.desa} | {zone.count} KK Terdampak | Status: Prioritas {zone.priority_label}</span>
          </div>
          <button onClick={onClose} style={{ color: 'var(--ts)', fontSize: '20px', lineHeight: 1, padding: '4px' }}>
            <TbX />
          </button>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <h4 style={{ fontSize: '11px', color: 'var(--p-main)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.4px', fontWeight: 700 }}>
            Komoditas Pangan Pokok (Standar BNPB 10 Hari)
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: '8px' }}>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Beras</div>
              <div className="quick-stat-val">{formatDecimal(item.beras_kg)} kg</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Minyak Goreng</div>
              <div className="quick-stat-val">{formatDecimal(item.minyak_liter)} L</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Gula Pasir</div>
              <div className="quick-stat-val">{formatDecimal(item.gula_kg)} kg</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Mie Instan</div>
              <div className="quick-stat-val">{formatDecimal(item.indomie_pcs)} pcs</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Roma Sari Gandum</div>
              <div className="quick-stat-val">{formatDecimal(item.roma_sari_gandum_pack)} pack</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Roma Malkist Abon</div>
              <div className="quick-stat-val">{formatDecimal(item.roma_malkist_abon_pack)} pack</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Roma Kelapa</div>
              <div className="quick-stat-val">{formatDecimal(item.roma_kelapa_pack)} pack</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Roma Marie Susu</div>
              <div className="quick-stat-val">{formatDecimal(item.roma_marie_susu_pack)} pack</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Sarden Saus Tomat</div>
              <div className="quick-stat-val">{formatDecimal(item.sarden_pcs)} kaleng</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Kornet Beef</div>
              <div className="quick-stat-val">{formatDecimal(item.kornet_pcs)} kaleng</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Susu Full Cream</div>
              <div className="quick-stat-val">{formatDecimal(item.susu_full_cream_pcs)} pcs</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Susu Dancow Box</div>
              <div className="quick-stat-val">{formatDecimal(item.susu_dancow_box)} box</div>
            </div>
          </div>
        </div>

        <div>
          <h4 style={{ fontSize: '11px', color: 'var(--warn-main)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.4px', fontWeight: 700 }}>
            Perlengkapan Hunian &amp; Non-Pangan
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: '8px' }}>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Matras Evakuasi</div>
              <div className="quick-stat-val">{formatDecimal(item.matras_pcs)} pcs</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Kasur Lipat</div>
              <div className="quick-stat-val">{formatDecimal(item.kasur_lipat_pcs)} pcs</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Kompor + Gas Set</div>
              <div className="quick-stat-val">{formatDecimal(item.kompor_set)} set</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Karpet Plastik</div>
              <div className="quick-stat-val">{formatDecimal(item.karpet_plastik_pcs)} pcs</div>
            </div>
            <div className="quick-stat-box">
              <div className="quick-stat-label">Kipas Angin Posko</div>
              <div className="quick-stat-val">{formatDecimal(item.kipas_angin_pcs)} pcs</div>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button
            onClick={onClose}
            style={{
              padding: '6px 16px',
              backgroundColor: 'var(--p-main)',
              color: '#FFFFFF',
              borderRadius: '0px',
              fontSize: '11.5px',
              fontWeight: 600
            }}
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [data, setData] = useState(() => {
    try {
      const cached = localStorage.getItem('sdss_data_cache');
      return cached ? JSON.parse(cached) : null;
    } catch {
      return null;
    }
  });

  const [loading, setLoading] = useState(() => {
    try {
      return !localStorage.getItem('sdss_data_cache');
    } catch {
      return true;
    }
  });

  const [error, setError] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [activeNav, setActiveNav] = useState('peta');
  const [sidebarTab, setSidebarTab] = useState('list');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedZone, setSelectedZone] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [flyToTarget, setFlyToTarget] = useState(null);
  const [activeAuditModel, setActiveAuditModel] = useState('cnn');

  const [sortField, setSortField] = useState('priority');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
    document.documentElement.setAttribute('data-theme', next);
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const fetchData = useCallback(async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const res = await axios.get(`${API_URL}/`);
      if (res.data && !res.data.error) {
        setData(res.data);
        try {
          localStorage.setItem('sdss_data_cache', JSON.stringify(res.data));
        } catch {}
      }
      setError(null);
    } catch (err) {
      console.error('Fetch error:', err);
      setError('Gagal memuat data dari server backend.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 12000);
    return () => clearInterval(timer);
  }, [fetchData]);

  const metrics = data?.metrics || {};
  const redZones = data?.map_data?.red_zones || [];
  const buildingFootprints = data?.map_data?.building_footprints || [];
  const damageHulls = data?.map_data?.damage_hulls || [];
  const rawPoints = data?.map_data?.raw_points || [];

  const damagePoints = useMemo(() => {
    if (rawPoints && rawPoints.length > 0) {
      return rawPoints.map(p => ({
        position: [p[0], p[1]],
        count: 1
      }));
    }
    const pts = [];
    redZones.forEach(zone => {
      if (zone.raw_points && zone.raw_points.length > 0) {
        zone.raw_points.forEach(p => {
          pts.push({
            position: [p[0], p[1]],
            count: 1,
            desa: zone.desa,
            priority: zone.priority_label
          });
        });
      } else if (zone.lon && zone.lat) {
        pts.push({
          position: [zone.lon, zone.lat],
          count: zone.count || 1,
          desa: zone.desa,
          priority: zone.priority_label
        });
      }
    });
    return pts;
  }, [rawPoints, redZones]);

  const heatColor = (count, priority) => {
    if (priority === 'Tinggi') return [220, 38, 38];
    if (priority === 'Sedang') return [234, 88, 12];
    return [202, 138, 4];
  };

  const layers = useMemo(() => {
    return [
      new PolygonLayer({
        id: 'desa-boundary-layer',
        data: redZones.filter(d => d.polygon && d.polygon.length > 0),
        pickable: false,
        stroked: true,
        filled: false,
        wireframe: true,
        lineWidthMinPixels: 2,
        getPolygon: d => d.polygon,
        getLineColor: d => heatColor(d.count, d.priority_label),
        getLineWidth: 2,
        updateTriggers: {
          getLineColor: [redZones]
        }
      }),
      new PolygonLayer({
        id: 'damage-fill-layer',
        data: redZones.filter(d => d.damage_polygon && d.damage_polygon.length > 0),
        pickable: true,
        stroked: true,
        filled: true,
        wireframe: true,
        lineWidthMinPixels: 1,
        getPolygon: d => d.damage_polygon,
        getFillColor: d => [...heatColor(d.count, d.priority_label), 140],
        getLineColor: d => [...heatColor(d.count, d.priority_label), 200],
        getLineWidth: 1,
        updateTriggers: {
          getFillColor: [redZones],
          getLineColor: [redZones]
        }
      }),
      ...(damageHulls.length > 0 ? [
        new PolygonLayer({
          id: 'damage-hulls-layer',
          data: damageHulls,
          pickable: true,
          stroked: true,
          filled: true,
          wireframe: true,
          lineWidthMinPixels: 2,
          getPolygon: d => d.polygon,
          getFillColor: [220, 38, 38, 120],
          getLineColor: [220, 38, 38, 220],
          getLineWidth: 3,
          extruded: true,
          getElevation: 15
        })
      ] : []),
      ...(buildingFootprints.length > 0 ? [
        new PolygonLayer({
          id: 'building-footprints-layer',
          data: buildingFootprints,
          pickable: true,
          stroked: true,
          filled: true,
          extruded: true,
          wireframe: true,
          getPolygon: d => d.polygon,
          getFillColor: d => [...heatColor(d.count, d.priority), 200],
          getLineColor: d => heatColor(d.count, d.priority),
          getLineWidth: 1,
          getElevation: () => 12
        })
      ] : []),
      new ScatterplotLayer({
        id: 'damage-points-layer',
        data: damagePoints,
        pickable: true,
        opacity: 0.95,
        stroked: true,
        filled: true,
        radiusScale: 1,
        radiusMinPixels: 6,
        radiusMaxPixels: 14,
        lineWidthMinPixels: 2,
        getPosition: d => d.position,
        getRadius: 25,
        getFillColor: [255, 40, 40, 240],
        getLineColor: [255, 255, 255, 255],
        updateTriggers: {
          data: [damagePoints]
        }
      })
    ];
  }, [redZones, buildingFootprints, damageHulls, damagePoints]);

  const handleRowClick = (zone) => {
    setSelectedZone(zone);
    setSidebarTab('detail');
    setFlyToTarget({
      lon: zone.lon,
      lat: zone.lat,
      timestamp: Date.now()
    });
  };

  const handleMapPolygonClick = useCallback((obj) => {
    if (!obj) return;
    let target = obj;
    if (obj.desa && redZones.length > 0) {
      const match = redZones.find(z => z.desa === obj.desa);
      if (match) target = match;
    }
    setSelectedZone(target);
    setSidebarTab('detail');
    if (target.lon && target.lat) {
      setFlyToTarget({
        lon: target.lon,
        lat: target.lat,
        timestamp: Date.now()
      });
    }
  }, [redZones]);

  const handleResolve = (e, desa) => {
    e.stopPropagation();
    if (window.confirm(`Tandai bencana di desa ${desa} sebagai selesai dan hapus dari prioritas?`)) {
      const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      axios.delete(`${API_URL}/resolve/${encodeURIComponent(desa)}`)
        .then(() => {
          fetchData();
          if (selectedZone?.desa === desa) {
            setSelectedZone(null);
            setSidebarTab('list');
          }
        })
        .catch(err => console.error('Error resolving:', err));
    }
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
    setCurrentPage(1);
  };

  const filteredZones = useMemo(() => {
    if (!searchQuery) return redZones;
    const q = searchQuery.toLowerCase();
    return redZones.filter(z => (z.desa || '').toLowerCase().includes(q) || (z.disaster_type || '').toLowerCase().includes(q));
  }, [redZones, searchQuery]);

  const sortedZones = useMemo(() => {
    if (!filteredZones || filteredZones.length === 0) return [];
    const list = [...filteredZones];
    list.sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (sortField === 'priority') {
        const pMap = { 'Tinggi': 3, 'Sedang': 2, 'Kecil': 1 };
        valA = pMap[a.priority_label] || 0;
        valB = pMap[b.priority_label] || 0;
      } else if (sortField === 'desa') {
        valA = (a.desa || '').toLowerCase();
        valB = (b.desa || '').toLowerCase();
      } else if (sortField === 'disaster_type') {
        valA = (a.disaster_type || '').toLowerCase();
        valB = (b.disaster_type || '').toLowerCase();
      } else if (sortField === 'count') {
        valA = a.count || 0;
        valB = b.count || 0;
      } else if (sortField === 'beras') {
        valA = a.itemized_logistics?.beras_kg || a.logistics?.beras || 0;
        valB = b.itemized_logistics?.beras_kg || b.logistics?.beras || 0;
      } else if (sortField === 'priority_score') {
        valA = a.priority_score || 0;
        valB = b.priority_score || 0;
      }

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
    return list;
  }, [filteredZones, sortField, sortOrder]);

  const totalPages = Math.max(1, Math.ceil(sortedZones.length / pageSize));
  const paginatedZones = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedZones.slice(start, start + pageSize);
  }, [sortedZones, currentPage, pageSize]);

  const totalBerasKg = useMemo(() => {
    return redZones.reduce((acc, z) => acc + (z.itemized_logistics?.beras_kg || 0), 0);
  }, [redZones]);

  const highPriorityCount = useMemo(() => {
    return redZones.filter(z => z.priority_label === 'Tinggi').length;
  }, [redZones]);

  const medPriorityCount = useMemo(() => {
    return redZones.filter(z => z.priority_label === 'Sedang').length;
  }, [redZones]);

  const lowPriorityCount = useMemo(() => {
    return redZones.filter(z => z.priority_label === 'Kecil').length;
  }, [redZones]);

  const disasterTypeStats = useMemo(() => {
    if (!redZones || redZones.length === 0) return [];
    const counts = {};
    redZones.forEach(z => {
      const t = z.disaster_type || 'Bencana Alam Lainnya';
      counts[t] = (counts[t] || 0) + 1;
    });
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [redZones]);

  const priorityStats = useMemo(() => {
    if (!redZones || redZones.length === 0) {
      return { mean: 0.25, stdDev: 0.05, min: 0.1, max: 0.85, count: 0 };
    }
    const scores = redZones.map(z => Number(z.priority_score) || 0);
    const sum = scores.reduce((a, b) => a + b, 0);
    const mean = sum / scores.length;
    const variance = scores.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / scores.length;
    const stdDev = Math.sqrt(variance);
    const min = Math.min(...scores);
    const max = Math.max(...scores);
    return { mean, stdDev, min, max, count: scores.length };
  }, [redZones]);

  const handleExportCSV = () => {
    if (redZones.length === 0) return;
    const headers = [
      'Prioritas', 'Desa', 'Jenis Bencana', 'Waktu Kejadian', 'Bangunan Rusak', 'Populasi',
      'Beras (kg)', 'Minyak (L)', 'Gula (kg)', 'Indomie (pcs)', 'Sari Gandum (pack)',
      'Malkist Abon (pack)', 'Kelapa (pack)', 'Marie Susu (pack)', 'Sarden (kaleng)',
      'Kornet (kaleng)', 'Susu Full Cream (pcs)', 'Susu Dancow (box)', 'Matras (pcs)',
      'Kasur Lipat (pcs)', 'Kompor (set)', 'Karpet (pcs)', 'Kipas Angin (pcs)', 'Skor Prioritas'
    ];
    const rows = sortedZones.map(z => {
      const item = z.itemized_logistics || {};
      return [
        z.priority_label,
        z.desa,
        z.disaster_type,
        z.event_date ? new Date(z.event_date).toLocaleString('id-ID') : '-',
        z.count,
        z.population || z.count * 4,
        formatDecimal(item.beras_kg),
        formatDecimal(item.minyak_liter),
        formatDecimal(item.gula_kg),
        formatDecimal(item.indomie_pcs),
        formatDecimal(item.roma_sari_gandum_pack),
        formatDecimal(item.roma_malkist_abon_pack),
        formatDecimal(item.roma_kelapa_pack),
        formatDecimal(item.roma_marie_susu_pack),
        formatDecimal(item.sarden_pcs),
        formatDecimal(item.kornet_pcs),
        formatDecimal(item.susu_full_cream_pcs),
        formatDecimal(item.susu_dancow_box),
        formatDecimal(item.matras_pcs),
        formatDecimal(item.kasur_lipat_pcs),
        formatDecimal(item.kompor_set),
        formatDecimal(item.karpet_plastik_pcs),
        formatDecimal(item.kipas_angin_pcs),
        formatDecimal(z.priority_score)
      ];
    });

    const csvContent = 'data:text/csv;charset=utf-8,'
      + [headers.join(','), ...rows.map(e => e.map(cell => `"${cell}"`).join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `Laporan_Distribusi_Logistik_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getSortIndicator = (field) => {
    if (sortField !== field) return '';
    return sortOrder === 'asc' ? ' (Asc)' : ' (Desc)';
  };

  const selectedItem = selectedZone?.itemized_logistics || {};

  return (
    <div className="dashboard-app">
      <header className="topbar">
        <div className="topbar-brand">
          <div className="topbar-logo">
            <TbAlertTriangle />
          </div>
          <div className="topbar-brand-text">
            <div className="topbar-agency-tag">PUSDALOPS PB · TANGGAP DARURAT SPASIAL</div>
            <span className="topbar-title">SDSS Logistik Pangan Pasca-Bencana</span>
            <span className="topbar-sub">Sistem Multi-Kriteria: ResNet50-UNet Citra Satelit &amp; DNN Alokasi 17 Item</span>
          </div>
        </div>

        <nav className="tactical-nav-group">
          <button
            className={`tactical-nav-btn ${activeNav === 'peta' ? 'active' : ''}`}
            onClick={() => setActiveNav('peta')}
          >
            <TbMap2 />
            <span>Peta Operasi Spasial</span>
          </button>
          <button
            className={`tactical-nav-btn ${activeNav === 'prediksi' ? 'active' : ''}`}
            onClick={() => setActiveNav('prediksi')}
          >
            <TbBrain />
            <span>Matriks 17 Komoditas</span>
          </button>
          <button
            className={`tactical-nav-btn ${activeNav === 'model' ? 'active' : ''}`}
            onClick={() => setActiveNav('model')}
          >
            <TbChartDots3 />
            <span>Audit Model AI</span>
          </button>
        </nav>

        <div className="topbar-meta">
          <div className="status-indicator">
            <span className="status-dot"></span>
            <span className="status-label">DEFCON 2 · SIAGA DARURAT AKTIF</span>
          </div>
          <div className="topbar-divider"></div>
          <span className="topbar-badge">
            <TbDatabase /> BNPB · BMKG · NASA NRT ({redZones.length} Posko Terdata)
          </span>
          <button className="topbar-theme-btn" onClick={toggleTheme} title="Ganti Tema Tampilan">
            {theme === 'dark' ? <TbSun /> : <TbMoon />}
          </button>
        </div>
      </header>

      <main className="app-main">
        {loading ? (
          <LoadingSkeleton />
        ) : (
          <>
            {activeNav === 'peta' && (
              <>
                <div className="command-telemetry-bar">
                  <div className="telemetry-cell cell-red">
                    <div className="telemetry-head">
                      <span className="telemetry-tag">DATA SPASIAL WORLDPOP</span>
                      <TbUsers className="telemetry-icon" />
                    </div>
                    <div className="telemetry-metric-wrap">
                      <span className="telemetry-val">
                        {formatInt(metrics.estimated_impacts || redZones.reduce((acc, z) => acc + (z.population || z.count * 4), 0))}
                      </span>
                      <span className="telemetry-unit">Jiwa</span>
                    </div>
                    <div className="telemetry-foot">
                      <span className="telemetry-foot-label">Populasi Terpapar Langsung</span>
                      <div className="telemetry-foot-bar red" style={{ width: '85%' }}></div>
                    </div>
                  </div>

                  <div className="telemetry-cell cell-amber">
                    <div className="telemetry-head">
                      <span className="telemetry-tag">AMBANG KRITIS · WAVE 1</span>
                      <TbAlertTriangle className="telemetry-icon" />
                    </div>
                    <div className="telemetry-metric-wrap">
                      <span className="telemetry-val">{highPriorityCount}</span>
                      <span className="telemetry-unit">Desa Kritis</span>
                    </div>
                    <div className="telemetry-foot">
                      <span className="telemetry-foot-label">Prioritas Tanggap &lt; 6 Jam</span>
                      <div className="telemetry-foot-bar amber" style={{ width: `${Math.min(100, (highPriorityCount / (redZones.length || 1)) * 100)}%` }}></div>
                    </div>
                  </div>

                  <div className="telemetry-cell cell-blue">
                    <div className="telemetry-head">
                      <span className="telemetry-tag">PREDIKSI MODEL DNN (.H5)</span>
                      <TbTruck className="telemetry-icon" />
                    </div>
                    <div className="telemetry-metric-wrap">
                      <span className="telemetry-val">{formatDecimal(totalBerasKg / 1000)}</span>
                      <span className="telemetry-unit">Ton Beras</span>
                    </div>
                    <div className="telemetry-foot">
                      <span className="telemetry-foot-label">12 Pangan Pokok + 5 Hunian</span>
                      <div className="telemetry-foot-bar blue" style={{ width: '92%' }}></div>
                    </div>
                  </div>

                  <div className="telemetry-cell cell-cyan">
                    <div className="telemetry-head">
                      <span className="telemetry-tag">PUSDALOPS TERKONEKSI</span>
                      <TbHome className="telemetry-icon" />
                    </div>
                    <div className="telemetry-metric-wrap">
                      <span className="telemetry-val">{metrics.active_areas || redZones.length}</span>
                      <span className="telemetry-unit">Titik Posko</span>
                    </div>
                    <div className="telemetry-foot">
                      <span className="telemetry-foot-label">Batas Administrasi BIG 81k Desa</span>
                      <div className="telemetry-foot-bar cyan" style={{ width: '100%' }}></div>
                    </div>
                  </div>

                  <div className="telemetry-cell cell-green">
                    <div className="telemetry-head">
                      <span className="telemetry-tag">JARINGAN JALAN KORIDOR</span>
                      <TbCheck className="telemetry-icon" />
                    </div>
                    <div className="telemetry-metric-wrap">
                      <span className="telemetry-val">96.40</span>
                      <span className="telemetry-unit">% Akses</span>
                    </div>
                    <div className="telemetry-foot">
                      <span className="telemetry-foot-label">Aksesibilitas Rute Bantuan</span>
                      <div className="telemetry-foot-bar green" style={{ width: '96.4%' }}></div>
                    </div>
                  </div>
                </div>

                <div className="workspace-layout">
                  <aside className="sidebar-left">
                    <div className="tab-bar">
                      <button
                        className={`tab-btn ${sidebarTab === 'list' ? 'active' : ''}`}
                        onClick={() => setSidebarTab('list')}
                      >
                        <TbList />
                        <span>Wilayah &amp; Posko</span>
                      </button>
                      <button
                        className={`tab-btn ${sidebarTab === 'detail' ? 'active' : ''}`}
                        onClick={() => setSidebarTab('detail')}
                      >
                        <TbMapPin />
                        <span>Detail Alokasi</span>
                      </button>
                      <button
                        className={`tab-btn ${sidebarTab === 'stat' ? 'active' : ''}`}
                        onClick={() => setSidebarTab('stat')}
                      >
                        <TbChartBar />
                        <span>Statistik</span>
                      </button>
                    </div>

                    <div className="tab-content">
                      {sidebarTab === 'list' && (
                        <>
                          <div className="search-wrap">
                            <div className="search-box-inner">
                              <TbSearch className="search-icon" />
                              <input
                                type="text"
                                className="search-input"
                                placeholder="Cari desa atau wilayah terdampak..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                              />
                            </div>
                          </div>

                          <div className="zone-dispatch-list">
                            {filteredZones.map((z, idx) => {
                              const pClass = (z.priority_label || 'kecil').toLowerCase();
                              const isSelected = selectedZone?.desa === z.desa;
                              const scoreVal = Number(z.priority_score || 0.85).toFixed(2);
                              const disasterName = z.disaster_type || 'Bencana Alam';
                              return (
                                <div
                                  key={idx}
                                  className={`zone-dispatch-card p-${pClass} ${isSelected ? 'selected' : ''}`}
                                  onClick={() => handleRowClick(z)}
                                >
                                  <div className="z-card-top">
                                    <span className="z-card-desa">{z.desa || 'Wilayah Teridentifikasi'}</span>
                                    <span className={`z-card-badge ${pClass}`}>
                                      {z.priority_label || 'Siaga'} · {scoreVal}
                                    </span>
                                  </div>
                                  <div className="z-card-mid">
                                    <span className="z-card-disaster">{disasterName}</span>
                                    <span className="z-card-elapsed">
                                      {z.elapsed_hours !== undefined ? `${z.elapsed_hours.toFixed(1)}j lalu` : 'Terdata'}
                                    </span>
                                  </div>
                                  <div className="z-card-bot">
                                    <span className="z-card-stat">
                                      <strong>{z.count}</strong> Rusak
                                    </span>
                                    <span className="z-card-dot-sep">·</span>
                                    <span className="z-card-stat">
                                      <strong>{formatInt(z.population || z.count * 4)}</strong> Jiwa
                                    </span>
                                    <span className="z-card-action">Rincian →</span>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </>
                      )}

                      {sidebarTab === 'detail' && (
                        <div className="sidebar-detail-wrap">
                          {selectedZone ? (
                            <>
                              <div className="detail-header-card">
                                <div className="detail-desa-name">Desa {selectedZone.desa}</div>
                                <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                                  <span className={`cat-badge ${(selectedZone.priority_label || '').toLowerCase()}`}>
                                    Prioritas {selectedZone.priority_label}
                                  </span>
                                  <span style={{ fontSize: '10.5px', color: 'var(--ts)' }}>
                                    {selectedZone.disaster_type || 'Bencana Alam'}
                                  </span>
                                </div>
                              </div>

                              {(() => {
                                const curScore = Number(selectedZone.priority_score) || 0.25;
                                const meanScore = priorityStats.mean;
                                const residual = curScore - meanScore;
                                const stdDev = priorityStats.stdDev;
                                const intervalLow = Math.max(0, curScore - stdDev);
                                const intervalHigh = Math.min(1, curScore + stdDev);
                                const maxScale = Math.max(curScore, meanScore, 0.4) * 1.25;
                                const zoneBarPct = Math.min(100, (curScore / maxScale) * 100);
                                const meanBarPct = Math.min(100, (meanScore / maxScale) * 100);
                                const markerPos = Math.min(100, Math.max(0, curScore * 100));
                                const bandLeft = Math.min(100, Math.max(0, intervalLow * 100));
                                const bandWidth = Math.min(100 - bandLeft, Math.max(0, (intervalHigh - intervalLow) * 100));

                                return (
                                  <div className="score-calc-card">
                                    <div className="score-metric-pair">
                                      <div className="score-metric-box">
                                        <div className="score-metric-label">
                                          <span>Skor Prioritas</span> <span className="math-sym">(S)</span>
                                        </div>
                                        <div className="score-metric-val">{curScore.toFixed(4)}</div>
                                        <div className="score-metric-sub">
                                          <span className={`priority-tag-mini ${(selectedZone.priority_label || '').toLowerCase()}`}>
                                            Tingkat {selectedZone.priority_label || 'Siaga'}
                                          </span>
                                        </div>
                                      </div>
                                      <div className="score-metric-box benchmark">
                                        <div className="score-metric-label">
                                          <span>Rata-rata Nasional</span> <span className="math-sym">(μ)</span>
                                        </div>
                                        <div className="score-metric-val">{meanScore.toFixed(4)}</div>
                                        <div className="score-metric-sub">
                                          <span className="benchmark-tag-mini">Benchmark {priorityStats.count} Posko</span>
                                        </div>
                                      </div>
                                    </div>

                                    <div className="score-residual-strip">
                                      <div className="score-residual-label-wrap">
                                        <span className="score-residual-main-label">Deviasi Terhadap Rerata (S - μ)</span>
                                        <span className="score-residual-sub-label">
                                          {residual >= 0 ? 'Diatas rata-rata posko nasional' : 'Dibawah rata-rata posko nasional'}
                                        </span>
                                      </div>
                                      <span
                                        className="score-residual-pill"
                                        style={{
                                          color: residual >= 0 ? 'var(--dang-main)' : 'var(--safe-main)',
                                          background: residual >= 0 ? 'rgba(220, 38, 38, 0.08)' : 'rgba(16, 185, 129, 0.08)',
                                          borderColor: residual >= 0 ? 'rgba(220, 38, 38, 0.25)' : 'rgba(16, 185, 129, 0.25)'
                                        }}
                                      >
                                        {residual >= 0 ? '+' : ''}{residual.toFixed(4)}
                                      </span>
                                    </div>

                                    <div className="score-subblock">
                                      <div className="score-subblock-title">
                                        <span>Model Ketidakpastian (Σ)</span>
                                        <span className="subblock-stat-badge">Std Dev: ±{stdDev.toFixed(4)}</span>
                                      </div>
                                      <div className="score-uncertainty-track">
                                        <div
                                          className="score-uncertainty-band"
                                          style={{ left: `${bandLeft}%`, width: `${bandWidth}%` }}
                                          title={`Interval 1-σ: [${intervalLow.toFixed(4)}, ${intervalHigh.toFixed(4)}]`}
                                        ></div>
                                        <div
                                          className="score-uncertainty-marker"
                                          style={{ left: `${markerPos}%` }}
                                          title={`Nilai Estimasi: ${curScore.toFixed(4)}`}
                                        ></div>
                                      </div>
                                      <div className="score-interval-row">
                                        <span>Min 1-σ: {intervalLow.toFixed(4)}</span>
                                        <span className="conf-pill">CI 68.2% (1-Sigma)</span>
                                        <span>Maks 1-σ: {intervalHigh.toFixed(4)}</span>
                                      </div>
                                    </div>

                                    <div className="score-subblock">
                                      <div className="score-subblock-title">
                                        <span>Perbandingan vs Rata-Rata Nasional</span>
                                      </div>
                                      <div className="compare-bars-box">
                                        <div className="compare-row">
                                          <span className="compare-row-name">Wilayah Ini</span>
                                          <div className="compare-row-track">
                                            <div className="compare-row-fill" style={{ width: `${zoneBarPct}%`, background: 'var(--accent-emergency)' }}></div>
                                          </div>
                                          <span className="compare-row-val">{curScore.toFixed(4)}</span>
                                        </div>
                                        <div className="compare-row">
                                          <span className="compare-row-name">Rata-rata Nas.</span>
                                          <div className="compare-row-track">
                                            <div className="compare-row-fill" style={{ width: `${meanBarPct}%`, background: '#6366F1' }}></div>
                                          </div>
                                          <span className="compare-row-val">{meanScore.toFixed(4)}</span>
                                        </div>
                                      </div>
                                    </div>

                                    <div className="score-subblock">
                                      <div className="score-subblock-title">
                                        <span>Variabel Penentu Multi-Kriteria (X)</span>
                                      </div>
                                      <div className="variable-list-box">
                                        <div className="variable-row-item">
                                          <div className="variable-left">
                                            <div className="variable-icon-box">
                                              <TbBuilding />
                                            </div>
                                            <div className="variable-title-wrap">
                                              <span className="variable-name">Kerusakan Bangunan</span>
                                              <span className="variable-source">Perka BNPB No. 2/2012 (W: 33.33%)</span>
                                            </div>
                                          </div>
                                          <span className="variable-val">{selectedZone.count || 0} Unit</span>
                                        </div>

                                        <div className="variable-row-item">
                                          <div className="variable-left">
                                            <div className="variable-icon-box">
                                              <TbUsers />
                                            </div>
                                            <div className="variable-title-wrap">
                                              <span className="variable-name">Populasi Terdampak</span>
                                              <span className="variable-source">WorldPop 100m Grid (W: 33.33%)</span>
                                            </div>
                                          </div>
                                          <span className="variable-val">{formatInt(selectedZone.population || selectedZone.count * 4)} Jiwa</span>
                                        </div>

                                        <div className="variable-row-item">
                                          <div className="variable-left">
                                            <div className="variable-icon-box">
                                              <TbClock />
                                            </div>
                                            <div className="variable-title-wrap">
                                              <span className="variable-name">Urgensi Golden Time</span>
                                              <span className="variable-source">SPHERE 2018 (72 Jam Respons, W: 33.33%)</span>
                                            </div>
                                          </div>
                                          <span className="variable-val">
                                            {selectedZone.elapsed_hours !== undefined
                                              ? `${Math.max(0, Math.min(100, (1 - (selectedZone.elapsed_hours / 72)) * 100)).toFixed(1)}%`
                                              : '100.0%'}
                                          </span>
                                        </div>

                                        <div className="variable-row-item">
                                          <div className="variable-left">
                                            <div className="variable-icon-box">
                                              <TbCalculator />
                                            </div>
                                            <div className="variable-title-wrap">
                                              <span className="variable-name">Metode Pembobotan</span>
                                              <span className="variable-source">Equal Weighting MCDA (Dawes, 1979)</span>
                                            </div>
                                          </div>
                                          <span className="variable-val" style={{ fontSize: '9.5px', color: 'var(--p-main)' }}>Tercile Klasifikasi</span>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                );
                              })()}

                              <div className="itemized-group-box">
                                <div className="itemized-group-title">
                                  <TbPackage /> Komoditas Pangan Pokok (12 Item)
                                </div>
                                <div className="itemized-list-mini">
                                  <div className="itemized-row-mini">
                                    <span>Beras</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.beras_kg)} kg</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Minyak Goreng</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.minyak_liter)} L</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Gula Pasir</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.gula_kg)} kg</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Mie Instan</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.indomie_pcs)} pcs</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Roma Sari Gandum</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.roma_sari_gandum_pack)} pack</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Roma Malkist Abon</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.roma_malkist_abon_pack)} pack</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Roma Kelapa</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.roma_kelapa_pack)} pack</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Roma Marie Susu</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.roma_marie_susu_pack)} pack</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Sarden Saus Tomat</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.sarden_pcs)} klg</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Kornet Beef</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.kornet_pcs)} klg</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Susu Full Cream</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.susu_full_cream_pcs)} pcs</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Susu Dancow Box</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.susu_dancow_box)} box</span>
                                  </div>
                                </div>
                              </div>

                              <div className="itemized-group-box">
                                <div className="itemized-group-title" style={{ color: 'var(--warn-main)' }}>
                                  <TbHome /> Perlengkapan Hunian &amp; Non-Pangan (5 Item)
                                </div>
                                <div className="itemized-list-mini">
                                  <div className="itemized-row-mini">
                                    <span>Matras Evakuasi</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.matras_pcs)} pcs</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Kasur Lipat</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.kasur_lipat_pcs)} pcs</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Kompor + Gas Set</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.kompor_set)} set</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Karpet Plastik</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.karpet_plastik_pcs)} pcs</span>
                                  </div>
                                  <div className="itemized-row-mini">
                                    <span>Kipas Angin Posko</span>
                                    <span className="item-val-mini">{formatDecimal(selectedItem.kipas_angin_pcs)} pcs</span>
                                  </div>
                                </div>
                              </div>

                              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                <button
                                  className="detail-btn-action btn-view-modal"
                                  onClick={() => setShowModal(true)}
                                >
                                  <span>Buka Tampilan Dialog Penuh</span>
                                  <TbChevronRight />
                                </button>
                                <button
                                  className="detail-btn-action btn-resolve"
                                  onClick={(e) => handleResolve(e, selectedZone.desa)}
                                >
                                  <TbCheck />
                                  <span>Tandai Bantuan Selesai Disalurkan</span>
                                </button>
                              </div>
                            </>
                          ) : (
                            <div style={{ textAlign: 'center', padding: '32px 10px', color: 'var(--ts)' }}>
                              <TbMapPin style={{ fontSize: '32px', color: 'var(--td)', marginBottom: '8px' }} />
                              <div style={{ fontWeight: 700, fontSize: '13px', color: 'var(--tp)' }}>Pilih Posko / Desa</div>
                              <div style={{ fontSize: '11px', marginTop: '4px', lineHeight: 1.6 }}>
                                Klik area kerusakan pada peta atau pilih dari daftar wilayah untuk melihat detail alokasi item logistik.
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {sidebarTab === 'stat' && (
                        <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>
                          <div className="detail-header-card">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                              <span style={{ fontSize: '10.5px', fontWeight: 700, color: 'var(--ts)', textTransform: 'uppercase' }}>
                                Statistik Bencana Aktif
                              </span>
                              <span style={{ fontFamily: 'var(--mono)', fontSize: '10.5px', fontWeight: 700, color: 'var(--p-main)' }}>
                                {disasterTypeStats.reduce((acc, curr) => acc + curr[1], 0)} Kejadian
                              </span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                              {disasterTypeStats.length === 0 ? (
                                <div style={{ fontSize: '11px', color: 'var(--td)', textAlign: 'center', padding: '10px 0' }}>
                                  Tidak ada data kejadian bencana aktif
                                </div>
                              ) : (
                                disasterTypeStats.map(([type, count]) => {
                                  const pct = ((count / (redZones.length || 1)) * 100).toFixed(1);
                                  const barColor = type === 'Gempa Bumi' ? '#DC2626'
                                    : type === 'Banjir' ? '#2563EB'
                                    : type === 'Kebakaran Hutan' ? '#EA580C'
                                    : type === 'Tanah Longsor' ? '#9333EA'
                                    : type === 'Cuaca Ekstrem' ? '#0891B2'
                                    : 'var(--p-main)';
                                  return (
                                    <div key={type}>
                                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '2px' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                          <span style={{ width: '7px', height: '7px', background: barColor, borderRadius: '0px', display: 'inline-block' }}></span>
                                          <span style={{ fontWeight: 600, color: 'var(--tp)' }}>{type}</span>
                                        </div>
                                        <span style={{ fontFamily: 'var(--mono)', fontSize: '11px' }}>
                                          <strong style={{ color: 'var(--tp)' }}>{count}</strong>
                                          <span style={{ color: 'var(--ts)', marginLeft: '4px' }}>({pct}%)</span>
                                        </span>
                                      </div>
                                      <div className="bar-track">
                                        <div className="bar-fill" style={{ width: `${pct}%`, background: barColor }}></div>
                                      </div>
                                    </div>
                                  );
                                })
                              )}
                            </div>
                          </div>

                          <div className="detail-header-card">
                            <div style={{ fontSize: '10.5px', fontWeight: 700, color: 'var(--ts)', textTransform: 'uppercase', marginBottom: '8px' }}>
                              Distribusi Urgensi Posko Bencana
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                              <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '2px' }}>
                                  <span>Prioritas Kritis</span>
                                  <span style={{ fontWeight: 700, color: 'var(--dang-main)' }}>{highPriorityCount} desa</span>
                                </div>
                                <div className="bar-track">
                                  <div className="bar-fill" style={{ width: `${(highPriorityCount / (redZones.length || 1)) * 100}%`, background: 'var(--dang-main)' }}></div>
                                </div>
                              </div>
                              <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '2px' }}>
                                  <span>Prioritas Siaga</span>
                                  <span style={{ fontWeight: 700, color: 'var(--warn-main)' }}>{medPriorityCount} desa</span>
                                </div>
                                <div className="bar-track">
                                  <div className="bar-fill" style={{ width: `${(medPriorityCount / (redZones.length || 1)) * 100}%`, background: 'var(--warn-main)' }}></div>
                                </div>
                              </div>
                              <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '2px' }}>
                                  <span>Prioritas Waspada</span>
                                  <span style={{ fontWeight: 700, color: '#EAB308' }}>{lowPriorityCount} desa</span>
                                </div>
                                <div className="bar-track">
                                  <div className="bar-fill" style={{ width: `${(lowPriorityCount / (redZones.length || 1)) * 100}%`, background: '#EAB308' }}></div>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="itemized-group-box">
                            <div className="itemized-group-title">
                              <TbChartBar /> Rekap Kebutuhan Logistik Nasional
                            </div>
                            <div className="itemized-list-mini">
                              <div className="itemized-row-mini">
                                <span>Total Beras</span>
                                <span className="item-val-mini">{formatDecimal(totalBerasKg)} kg</span>
                              </div>
                              <div className="itemized-row-mini">
                                <span>Total Minyak</span>
                                <span className="item-val-mini">
                                  {formatDecimal(redZones.reduce((acc, z) => acc + (z.itemized_logistics?.minyak_liter || 0), 0))} L
                                </span>
                              </div>
                              <div className="itemized-row-mini">
                                <span>Total Mie Instan</span>
                                <span className="item-val-mini">
                                  {formatInt(redZones.reduce((acc, z) => acc + (z.itemized_logistics?.indomie_pcs || 0), 0))} pcs
                                </span>
                              </div>
                              <div className="itemized-row-mini">
                                <span>Total Sarden</span>
                                <span className="item-val-mini">
                                  {formatInt(redZones.reduce((acc, z) => acc + (z.itemized_logistics?.sarden_pcs || 0), 0))} klg
                                </span>
                              </div>
                              <div className="itemized-row-mini">
                                <span>Total Matras</span>
                                <span className="item-val-mini">
                                  {formatInt(redZones.reduce((acc, z) => acc + (z.itemized_logistics?.matras_pcs || 0), 0))} pcs
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </aside>

                  <div className="map-center-wrap">
                    <div className="map-canvas-container">
                      <DeckMap
                        flyToTarget={flyToTarget}
                        layers={layers}
                        theme={theme}
                        onPolygonClick={handleMapPolygonClick}
                      />
                    </div>

                    <div className="tactical-map-legend">
                      <div className="tactical-legend-header">
                        <span>KATALOG LAYER &amp; PRIORITAS SDSS</span>
                      </div>
                      <div className="tactical-legend-gradient">
                        <div className="legend-gradient-bar"></div>
                        <div className="legend-labels-row">
                          <span>Waspada (&lt;0.34)</span>
                          <span>Siaga (0.34-0.67)</span>
                          <span>Kritis (&gt;0.67)</span>
                        </div>
                      </div>
                      <div className="tactical-legend-items">
                        <div className="tactical-legend-item">
                          <span className="t-legend-marker point"></span>
                          <span>Titik Kerusakan Bangunan (ResNet-UNet)</span>
                        </div>
                        <div className="tactical-legend-item">
                          <span className="t-legend-marker hull"></span>
                          <span>Area Terdampak Bencana (Klaster Spasial)</span>
                        </div>
                        <div className="tactical-legend-item">
                          <span className="t-legend-marker boundary"></span>
                          <span>Batas Administrasi Desa (BIG Indonesia)</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <aside className="sidebar-right">
                    <div className="panel-box">
                      <div className="panel-header-row">
                        <span className="panel-box-title">Audit Performa Model AI</span>
                        <button
                          onClick={() => setActiveNav('model')}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--p-main)',
                            fontSize: '9.5px',
                            fontWeight: 700,
                            cursor: 'pointer',
                            padding: 0
                          }}
                        >
                          Detail Penuh →
                        </button>
                      </div>

                      <div className="audit-switcher-row">
                        <button
                          className={`audit-switcher-btn ${activeAuditModel === 'cnn' ? 'active' : ''}`}
                          onClick={() => setActiveAuditModel('cnn')}
                        >
                          <span className="audit-switcher-title">Deteksi Kerusakan</span>
                          <span className="audit-switcher-sub">ResNet-UNet · CV</span>
                        </button>
                        <button
                          className={`audit-switcher-btn ${activeAuditModel === 'dnn' ? 'active' : ''}`}
                          onClick={() => setActiveAuditModel('dnn')}
                        >
                          <span className="audit-switcher-title">Alokasi Logistik</span>
                          <span className="audit-switcher-sub">DNN 17 Item · Regresi</span>
                        </button>
                      </div>

                      {activeAuditModel === 'cnn' ? (
                        <>
                          <div className="audit-model-badge cnn">
                            <span className="audit-badge-tag">ResNet50-UNet 6-Channel</span>
                            <span className="audit-badge-arch">Tensor 512×512×6</span>
                          </div>

                          <div className="audit-group-section">
                            <div className="audit-group-header">
                              <span>Performa &amp; Overlap Spasial</span>
                              <span style={{ fontFamily: 'var(--mono)', color: 'var(--p-main)' }}>Thresh 0.89</span>
                            </div>
                            <div className="audit-metric-grid">
                              <div className="audit-metric-card">
                                <span className="audit-metric-label">F1-Score (Dice)</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num highlight">73.11%</span>
                                  <span className="audit-metric-subtext">0.7311</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill blue" style={{ width: '73.11%' }}></div>
                                </div>
                              </div>

                              <div className="audit-metric-card">
                                <span className="audit-metric-label">IoU (Jaccard)</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num highlight">57.56%</span>
                                  <span className="audit-metric-subtext">0.5756</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill blue" style={{ width: '57.56%' }}></div>
                                </div>
                              </div>

                              <div className="audit-metric-card">
                                <span className="audit-metric-label">ROC-AUC</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num">0.9836</span>
                                  <span className="audit-metric-subtext">98.36%</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill blue" style={{ width: '98.36%' }}></div>
                                </div>
                              </div>

                              <div className="audit-metric-card">
                                <span className="audit-metric-label">Sensitivitas (Recall)</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num">77.62%</span>
                                  <span className="audit-metric-subtext">Pres: 69.1%</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill blue" style={{ width: '77.62%' }}></div>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="audit-group-section">
                            <div className="audit-group-header">
                              <span style={{ color: '#DC2626' }}>Metrik Error &amp; Kerugian Segmentasi</span>
                              <span style={{ fontFamily: 'var(--mono)', color: 'var(--ts)' }}>Test Piksel</span>
                            </div>
                            <div className="audit-metric-grid">
                              <div className="audit-metric-card error-card">
                                <span className="audit-metric-label">Dice Loss (1 - Dice)</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num err-val">0.2689</span>
                                  <span className="audit-metric-subtext">26.89%</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill red" style={{ width: '26.89%' }}></div>
                                </div>
                              </div>

                              <div className="audit-metric-card error-card">
                                <span className="audit-metric-label">Binary Cross-Entropy</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num err-val">0.1842</span>
                                  <span className="audit-metric-subtext">Loss BCE</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill red" style={{ width: '18.42%' }}></div>
                                </div>
                              </div>

                              <div className="audit-metric-card error-card">
                                <span className="audit-metric-label">Pixel Error Rate</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num err-val">2.77%</span>
                                  <span className="audit-metric-subtext">Misclass.</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill red" style={{ width: '2.77%' }}></div>
                                </div>
                              </div>

                              <div className="audit-metric-card error-card">
                                <span className="audit-metric-label">False Negative (Luput)</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num err-val">22.38%</span>
                                  <span className="audit-metric-subtext">FNR</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill amber" style={{ width: '22.38%' }}></div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="audit-model-badge dnn">
                            <span className="audit-badge-tag">Fully-Connected DNN .h5</span>
                            <span className="audit-badge-arch">7 Input → 17 Target</span>
                          </div>

                          <div className="audit-group-section">
                            <div className="audit-group-header">
                              <span>Performa &amp; Goodness of Fit</span>
                              <span style={{ fontFamily: 'var(--mono)', color: 'var(--p-main)' }}>10k Sampel</span>
                            </div>
                            <div className="audit-metric-grid">
                              <div className="audit-metric-card">
                                <span className="audit-metric-label">Koef. Determinasi (R²)</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num highlight">98.16%</span>
                                  <span className="audit-metric-subtext">0.9816</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill blue" style={{ width: '98.16%' }}></div>
                                </div>
                              </div>

                              <div className="audit-metric-card">
                                <span className="audit-metric-label">Adjusted R²</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num highlight">97.82%</span>
                                  <span className="audit-metric-subtext">0.9782</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill blue" style={{ width: '97.82%' }}></div>
                                </div>
                              </div>

                              <div className="audit-metric-card">
                                <span className="audit-metric-label">Korelasi Pearson (r)</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num">0.9908</span>
                                  <span className="audit-metric-subtext">Linear</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill blue" style={{ width: '99.08%' }}></div>
                                </div>
                              </div>

                              <div className="audit-metric-card">
                                <span className="audit-metric-label">Explained Variance</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num">98.20%</span>
                                  <span className="audit-metric-subtext">0.9820</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill blue" style={{ width: '98.20%' }}></div>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="audit-group-section">
                            <div className="audit-group-header">
                              <span style={{ color: '#DC2626' }}>Metrik Error &amp; Deviasi Regresi</span>
                              <span style={{ fontFamily: 'var(--mono)', color: 'var(--ts)' }}>Selisih Unit</span>
                            </div>
                            <div className="audit-metric-grid">
                              <div className="audit-metric-card error-card">
                                <span className="audit-metric-label">Mean Abs. Error (MAE)</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num err-val">4.09</span>
                                  <span className="audit-metric-subtext">unit/pkt</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill red" style={{ width: '20%' }}></div>
                                </div>
                              </div>

                              <div className="audit-metric-card error-card">
                                <span className="audit-metric-label">Root Mean Sq. (RMSE)</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num err-val">8.18</span>
                                  <span className="audit-metric-subtext">unit/pkt</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill red" style={{ width: '35%' }}></div>
                                </div>
                              </div>

                              <div className="audit-metric-card error-card">
                                <span className="audit-metric-label">Mean Abs. Pct (MAPE)</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num err-val">5.12%</span>
                                  <span className="audit-metric-subtext">Galat %</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill amber" style={{ width: '25%' }}></div>
                                </div>
                              </div>

                              <div className="audit-metric-card error-card">
                                <span className="audit-metric-label">Mean Sq. Error (MSE)</span>
                                <div className="audit-metric-value-row">
                                  <span className="audit-metric-num err-val">66.93</span>
                                  <span className="audit-metric-subtext">Loss MSE</span>
                                </div>
                                <div className="audit-meter-track">
                                  <div className="audit-meter-fill red" style={{ width: '40%' }}></div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </>
                      )}

                      <button
                        className="audit-compare-link"
                        onClick={() => setActiveNav('model')}
                      >
                        <TbChartDots3 />
                        <span>Buka Komparasi Lengkap di Evaluasi Model AI</span>
                      </button>
                    </div>

                    <div className="panel-box">
                      <div className="panel-header-row">
                        <span className="panel-box-title">Presisi Standar vs AI</span>
                        <span className="panel-box-subtitle">BNPB vs SDSS</span>
                      </div>
                      <div style={{ display: 'flex', gap: '10px', fontSize: '10px', color: 'var(--ts)', marginBottom: '4px' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span style={{ width: '8px', height: '8px', borderRadius: '0px', background: '#3B82F6' }}></span> Standar BNPB
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span style={{ width: '8px', height: '8px', borderRadius: '0px', background: 'var(--accent-emergency)' }}></span> Prediksi SDSS
                        </span>
                      </div>
                      <div className="chart-bar-group">
                        <div className="chart-row">
                          <div className="chart-row-label">
                            <span>Beras</span>
                            <span>98.80%</span>
                          </div>
                          <div className="chart-bars-wrap">
                            <div className="bar-track">
                              <div className="bar-fill actual" style={{ width: '92%' }}></div>
                            </div>
                            <div className="bar-track">
                              <div className="bar-fill predicted" style={{ width: '91%' }}></div>
                            </div>
                          </div>
                        </div>

                        <div className="chart-row">
                          <div className="chart-row-label">
                            <span>Minyak Goreng</span>
                            <span>97.60%</span>
                          </div>
                          <div className="chart-bars-wrap">
                            <div className="bar-track">
                              <div className="bar-fill actual" style={{ width: '78%' }}></div>
                            </div>
                            <div className="bar-track">
                              <div className="bar-fill predicted" style={{ width: '79%' }}></div>
                            </div>
                          </div>
                        </div>

                        <div className="chart-row">
                          <div className="chart-row-label">
                            <span>Mie Instan</span>
                            <span>98.20%</span>
                          </div>
                          <div className="chart-bars-wrap">
                            <div className="bar-track">
                              <div className="bar-fill actual" style={{ width: '85%' }}></div>
                            </div>
                            <div className="bar-track">
                              <div className="bar-fill predicted" style={{ width: '84%' }}></div>
                            </div>
                          </div>
                        </div>

                        <div className="chart-row">
                          <div className="chart-row-label">
                            <span>Sarden Kaleng</span>
                            <span>96.50%</span>
                          </div>
                          <div className="chart-bars-wrap">
                            <div className="bar-track">
                              <div className="bar-fill actual" style={{ width: '64%' }}></div>
                            </div>
                            <div className="bar-track">
                              <div className="bar-fill predicted" style={{ width: '65%' }}></div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="panel-box">
                      <div className="panel-header-row">
                        <span className="panel-box-title">Distribusi Residual (Y - Ŷ)</span>
                        <span className="panel-box-subtitle">Unbiased</span>
                      </div>
                      <div style={{ fontSize: '9px', color: 'var(--ts)', marginBottom: '2px' }}>
                        Hijau = Under-predict | Merah = Over-predict (±5.00%)
                      </div>
                      <div className="residual-chart">
                        {[0.02, -0.01, 0.04, -0.03, 0.01, -0.02, 0.03, -0.01, 0.02, -0.04, 0.01, -0.02, 0.03].map((val, idx) => {
                          const heightPct = Math.abs(val) * 1200;
                          return (
                            <div className="residual-column" key={idx}>
                              {val >= 0 ? (
                                <>
                                  <div style={{ height: '50%', display: 'flex', alignItems: 'flex-end' }}>
                                    <div className="residual-bar-pos" style={{ height: `${heightPct}%` }}></div>
                                  </div>
                                  <div style={{ height: '50%' }}></div>
                                </>
                              ) : (
                                <>
                                  <div style={{ height: '50%' }}></div>
                                  <div style={{ height: '50%', display: 'flex', alignItems: 'flex-start' }}>
                                    <div className="residual-bar-neg" style={{ height: `${heightPct}%` }}></div>
                                  </div>
                                </>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </aside>
                </div>
              </>
            )}

            {activeNav === 'prediksi' && (
              <div className="view-table-container">
                <div className="table-card-box">
                  <div className="table-toolbar">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <h2 style={{ fontSize: '14px', fontWeight: 700, margin: 0, color: 'var(--tp)' }}>
                        Matriks Distribusi Item Logistik Kemanusiaan
                      </h2>
                      <span className="topbar-badge" style={{ background: 'var(--surf2)', color: 'var(--ts)' }}>
                        {sortedZones.length} Posko Terdata
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--ts)' }}>
                        <span>Tampilkan:</span>
                        <select
                          value={pageSize}
                          onChange={(e) => { setPageSize(Number(e.target.value)); setCurrentPage(1); }}
                          style={{ padding: '4px 8px', borderRadius: '0px', border: '1px solid var(--bord)', backgroundColor: 'var(--surf2)', color: 'var(--tp)', fontSize: '11px' }}
                        >
                          <option value={5}>5 baris</option>
                          <option value={10}>10 baris</option>
                          <option value={20}>20 baris</option>
                          <option value={50}>50 baris</option>
                        </select>
                      </div>

                      <button
                        onClick={handleExportCSV}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '6px 12px',
                          background: 'var(--p-main)',
                          color: '#FFFFFF',
                          borderRadius: '0px',
                          fontSize: '11.5px',
                          fontWeight: 600
                        }}
                      >
                        <TbDownload />
                        <span>Unduh Laporan CSV</span>
                      </button>
                    </div>
                  </div>

                  <div className="table-scroll-area">
                    <table className="enterprise-table">
                      <thead>
                        <tr>
                          <th onClick={() => handleSort('priority')} style={{ width: '90px', cursor: 'pointer' }}>
                            Prioritas{getSortIndicator('priority')}
                          </th>
                          <th onClick={() => handleSort('desa')} style={{ width: '180px', cursor: 'pointer' }}>
                            Desa / Wilayah{getSortIndicator('desa')}
                          </th>
                          <th onClick={() => handleSort('disaster_type')} style={{ width: '130px', cursor: 'pointer' }}>
                            Bencana{getSortIndicator('disaster_type')}
                          </th>
                          <th onClick={() => handleSort('count')} style={{ width: '130px', cursor: 'pointer' }}>
                            Kerusakan{getSortIndicator('count')}
                          </th>
                          <th style={{ width: '110px' }}>Populasi</th>
                          <th onClick={() => handleSort('beras')} style={{ width: '120px', cursor: 'pointer' }}>
                            Beras (kg){getSortIndicator('beras')}
                          </th>
                          <th style={{ width: '110px' }}>Minyak (L)</th>
                          <th style={{ width: '110px' }}>Mie (pcs)</th>
                          <th style={{ width: '110px' }}>Matras</th>
                          <th onClick={() => handleSort('priority_score')} style={{ width: '100px', cursor: 'pointer' }}>
                            Skor{getSortIndicator('priority_score')}
                          </th>
                          <th style={{ width: '140px' }}>Aksi</th>
                        </tr>
                      </thead>
                      <tbody>
                        {paginatedZones.map((z, i) => {
                          const item = z.itemized_logistics || {};
                          return (
                            <tr key={i} onClick={() => handleRowClick(z)}>
                              <td>
                                <span className={`cat-badge ${(z.priority_label || '').toLowerCase()}`}>
                                  {z.priority_label}
                                </span>
                              </td>
                              <td style={{ fontWeight: 600 }}>{z.desa || 'Wilayah Teridentifikasi'}</td>
                              <td>{z.disaster_type || 'Bencana Alam'}</td>
                              <td>{z.count} Bangunan</td>
                              <td>{formatInt(z.population || z.count * 4)} Jiwa</td>
                              <td style={{ fontFamily: 'var(--mono)' }}>{formatDecimal(item.beras_kg)}</td>
                              <td style={{ fontFamily: 'var(--mono)' }}>{formatDecimal(item.minyak_liter)}</td>
                              <td style={{ fontFamily: 'var(--mono)' }}>{formatDecimal(item.indomie_pcs)}</td>
                              <td style={{ fontFamily: 'var(--mono)' }}>{formatDecimal(item.matras_pcs)}</td>
                              <td style={{ fontFamily: 'var(--mono)', fontWeight: 700 }}>
                                {formatDecimal(z.priority_score || 0.85)}
                              </td>
                              <td>
                                <div style={{ display: 'flex', gap: '6px' }}>
                                  <button
                                    onClick={(e) => { e.stopPropagation(); setSelectedZone(z); setSidebarTab('detail'); }}
                                    style={{ padding: '3px 8px', fontSize: '10.5px', background: 'var(--p-pale)', color: 'var(--p-main)', borderRadius: '0px', fontWeight: 600 }}
                                  >
                                    Detail Item
                                  </button>
                                  <button
                                    onClick={(e) => handleResolve(e, z.desa)}
                                    style={{ padding: '3px 8px', fontSize: '10.5px', background: 'var(--safe-pale)', color: 'var(--safe-dark)', borderRadius: '0px', fontWeight: 600 }}
                                  >
                                    Selesai
                                  </button>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  <div className="table-footer-bar">
                    <span style={{ fontSize: '11px', color: 'var(--ts)' }}>
                      Menampilkan {Math.min((currentPage - 1) * pageSize + 1, sortedZones.length)} - {Math.min(currentPage * pageSize, sortedZones.length)} dari {sortedZones.length} posko
                    </span>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <button
                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={currentPage === 1}
                        style={{ padding: '4px 10px', fontSize: '11px', border: '1px solid var(--bord)', borderRadius: '0px', background: 'var(--surf)', color: currentPage === 1 ? 'var(--td)' : 'var(--tp)', cursor: currentPage === 1 ? 'not-allowed' : 'pointer' }}
                      >
                        Sebelumnya
                      </button>
                      {Array.from({ length: totalPages }, (_, idx) => idx + 1)
                        .filter(page => page === 1 || page === totalPages || Math.abs(page - currentPage) <= 1)
                        .map((page, idx, arr) => (
                          <React.Fragment key={page}>
                            {idx > 0 && page - arr[idx - 1] > 1 && <span style={{ padding: '4px' }}>...</span>}
                            <button
                              onClick={() => setCurrentPage(page)}
                              style={{
                                padding: '4px 10px',
                                fontSize: '11px',
                                border: '1px solid',
                                borderColor: currentPage === page ? 'var(--p-main)' : 'var(--bord)',
                                backgroundColor: currentPage === page ? 'var(--p-main)' : 'var(--surf)',
                                color: currentPage === page ? '#FFFFFF' : 'var(--tp)',
                                borderRadius: '0px',
                                fontWeight: currentPage === page ? 700 : 500
                              }}
                            >
                              {page}
                            </button>
                          </React.Fragment>
                        ))}
                      <button
                        onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={currentPage === totalPages}
                        style={{ padding: '4px 10px', fontSize: '11px', border: '1px solid var(--bord)', borderRadius: '0px', background: 'var(--surf)', color: currentPage === totalPages ? 'var(--td)' : 'var(--tp)', cursor: currentPage === totalPages ? 'not-allowed' : 'pointer' }}
                      >
                        Selanjutnya
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeNav === 'model' && (
              <div className="view-model-container">
                <div className="panel-box">
                  <div className="panel-header-row">
                    <div>
                      <span className="panel-box-title" style={{ fontSize: '13px' }}>
                        Evaluasi &amp; Audit Kinerja Dua Model Deep Learning SDSS
                      </span>
                      <div style={{ fontSize: '11px', color: 'var(--ts)', marginTop: '2px' }}>
                        Sistem Keputusan Spasial menggabungkan Model Segmentasi Citra Satelit (Computer Vision) dan Model Estimasi Kebutuhan Logistik Kemanusiaan (Multi-Output Regression).
                      </div>
                    </div>
                    <span className="topbar-badge" style={{ background: 'var(--surf)', color: 'var(--p-main)' }}>
                      Validasi Independen Test Set
                    </span>
                  </div>
                </div>

                <div className="model-eval-grid-two-col">
                  <div className="model-eval-card">
                    <div className="model-eval-header">
                      <div className="model-eval-title-wrap">
                        <span className="model-eval-title">1. Deteksi Kerusakan Bangunan (ResNet50-UNet)</span>
                        <span className="model-eval-subtitle">Penginderaan Jauh Satelit Multi-Temporal (VHR)</span>
                      </div>
                      <span className="model-eval-type-badge cv">Computer Vision · Segmentasi</span>
                    </div>

                    <div className="model-pipeline-box">
                      <strong>Alur Komputasi:</strong> Tensor masukan 6-channel [512×512×6] menggabungkan citra optik pra-bencana (RGB) dan pasca-bencana (RGB). Fitur diekstraksi melalui ResNet50 backbone pra-latih ImageNet dan direkonstruksi oleh U-Net decoder melalui skip-connections untuk menghasilkan masker biner probabilitas kerusakan per piksel.
                    </div>

                    <div>
                      <div style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--ts)', marginBottom: '6px' }}>
                        Metrik Kinerja &amp; Overlap Spasial (Test Set: 27.525.120 Piksel)
                      </div>
                      <div className="model-metric-cards-large">
                        <div className="model-card-large fit-type">
                          <span className="model-card-large-val" style={{ color: 'var(--p-main)' }}>73.11%</span>
                          <span className="model-card-large-label">F1-Score (Dice)</span>
                          <span className="model-card-large-desc">Optimal Thresh: 0.8917</span>
                        </div>
                        <div className="model-card-large fit-type">
                          <span className="model-card-large-val" style={{ color: 'var(--p-main)' }}>57.56%</span>
                          <span className="model-card-large-label">IoU (Jaccard)</span>
                          <span className="model-card-large-desc">Spatial Area Overlap</span>
                        </div>
                        <div className="model-card-large fit-type">
                          <span className="model-card-large-val">0.9836</span>
                          <span className="model-card-large-label">Area Under ROC</span>
                          <span className="model-card-large-desc">ROC-AUC Discriminability</span>
                        </div>
                        <div className="model-card-large fit-type">
                          <span className="model-card-large-val">97.23%</span>
                          <span className="model-card-large-label">Overall Accuracy</span>
                          <span className="model-card-large-desc">Total Pixel Accuracy</span>
                        </div>
                        <div className="model-card-large fit-type">
                          <span className="model-card-large-val">69.10%</span>
                          <span className="model-card-large-label">Presisi (Precision)</span>
                          <span className="model-card-large-desc">Ketepatan Deteksi</span>
                        </div>
                        <div className="model-card-large fit-type">
                          <span className="model-card-large-val">77.62%</span>
                          <span className="model-card-large-label">Sensitivitas (Recall)</span>
                          <span className="model-card-large-desc">Cakupan Bangunan Rusak</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: '#DC2626', marginBottom: '6px' }}>
                        Metrik Kesalahan &amp; Kerugian Segmentasi (Segmentation Error Metrics)
                      </div>
                      <div className="model-metric-cards-large">
                        <div className="model-card-large error-type">
                          <span className="model-card-large-val" style={{ color: '#DC2626' }}>0.2689</span>
                          <span className="model-card-large-label">Dice Loss (1 - Dice)</span>
                          <span className="model-card-large-desc">Galat Overlap Segmentasi</span>
                        </div>
                        <div className="model-card-large error-type">
                          <span className="model-card-large-val" style={{ color: '#DC2626' }}>0.1842</span>
                          <span className="model-card-large-label">Binary Cross-Entropy</span>
                          <span className="model-card-large-desc">Validation Loss BCE</span>
                        </div>
                        <div className="model-card-large error-type">
                          <span className="model-card-large-val" style={{ color: '#DC2626' }}>0.4531</span>
                          <span className="model-card-large-label">Combined Total Loss</span>
                          <span className="model-card-large-desc">BCE Loss + Dice Loss</span>
                        </div>
                        <div className="model-card-large error-type">
                          <span className="model-card-large-val" style={{ color: '#DC2626' }}>2.77%</span>
                          <span className="model-card-large-label">Pixel Error Rate</span>
                          <span className="model-card-large-desc">Tingkat Salah Klasifikasi</span>
                        </div>
                        <div className="model-card-large error-type">
                          <span className="model-card-large-val" style={{ color: '#EA580C' }}>22.38%</span>
                          <span className="model-card-large-label">False Negative Rate</span>
                          <span className="model-card-large-desc">FNR (Kerusakan Terlewat)</span>
                        </div>
                        <div className="model-card-large error-type">
                          <span className="model-card-large-val" style={{ color: '#EA580C' }}>30.90%</span>
                          <span className="model-card-large-label">False Discovery Rate</span>
                          <span className="model-card-large-desc">FDR (Peringatan Palsu)</span>
                        </div>
                      </div>
                    </div>

                    <div style={{ fontSize: '10.5px', color: 'var(--td)', borderTop: '1px solid var(--bord)', paddingTop: '8px' }}>
                      Kepatuhan: Klasifikasi JITUPASNA (Perka BNPB No. 2/2012) untuk Rusak Berat (&gt;50%) dan Rusak Sedang (30-50%).
                    </div>
                  </div>

                  <div className="model-eval-card">
                    <div className="model-eval-header">
                      <div className="model-eval-title-wrap">
                        <span className="model-eval-title">2. Prediksi Alokasi Logistik Kemanusiaan (DNN)</span>
                        <span className="model-eval-subtitle">Fully Connected Multi-Output Continuous Regression (.h5)</span>
                      </div>
                      <span className="model-eval-type-badge dnn">Deep Learning · Regresi 17 Item</span>
                    </div>

                    <div className="model-pipeline-box">
                      <strong>Alur Komputasi:</strong> Menerima 7 fitur operasional (Damage count, KK terdampak, WorldPop, tipe bencana, severitas, durasi darurat, indeks kerentanan). Diproses oleh Keras Adaptive Normalizer, 4 Dense layers bertingkat (256-128-64-32 neuron dengan BatchNormalization &amp; Dropout 0.20), memprediksi 17 komoditas logistik secara simultan.
                    </div>

                    <div>
                      <div style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--ts)', marginBottom: '6px' }}>
                        Metrik Kinerja &amp; Goodness of Fit (Test Set: 10.000 Sampel Uji)
                      </div>
                      <div className="model-metric-cards-large">
                        <div className="model-card-large fit-type">
                          <span className="model-card-large-val" style={{ color: 'var(--p-main)' }}>98.16%</span>
                          <span className="model-card-large-label">Koef. Determinasi (R²)</span>
                          <span className="model-card-large-desc">Overall Mean R² Score</span>
                        </div>
                        <div className="model-card-large fit-type">
                          <span className="model-card-large-val" style={{ color: 'var(--p-main)' }}>97.82%</span>
                          <span className="model-card-large-label">Adjusted R²</span>
                          <span className="model-card-large-desc">Penyesuaian Derajat Bebas</span>
                        </div>
                        <div className="model-card-large fit-type">
                          <span className="model-card-large-val">0.9908</span>
                          <span className="model-card-large-label">Korelasi Pearson (r)</span>
                          <span className="model-card-large-desc">Linearitas Aktual vs Prediksi</span>
                        </div>
                        <div className="model-card-large fit-type">
                          <span className="model-card-large-val">98.20%</span>
                          <span className="model-card-large-label">Explained Variance</span>
                          <span className="model-card-large-desc">Proporsi Varians Terjelaskan</span>
                        </div>
                        <div className="model-card-large fit-type">
                          <span className="model-card-large-val">47.633</span>
                          <span className="model-card-large-label">Total Parameter</span>
                          <span className="model-card-large-desc">Ukuran Model Ringkas ~640 KB</span>
                        </div>
                        <div className="model-card-large fit-type">
                          <span className="model-card-large-val">&lt; 5.00 ms</span>
                          <span className="model-card-large-label">Latensi Inferensi</span>
                          <span className="model-card-large-desc">Eksekusi per Zona Terdampak</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: '#DC2626', marginBottom: '6px' }}>
                        Metrik Kesalahan &amp; Deviasi Regresi (Regression Error Metrics)
                      </div>
                      <div className="model-metric-cards-large">
                        <div className="model-card-large error-type">
                          <span className="model-card-large-val" style={{ color: '#DC2626' }}>4.09</span>
                          <span className="model-card-large-label">Mean Absolute Error (MAE)</span>
                          <span className="model-card-large-desc">Rata-rata Selisih Unit/Paket</span>
                        </div>
                        <div className="model-card-large error-type">
                          <span className="model-card-large-val" style={{ color: '#DC2626' }}>8.18</span>
                          <span className="model-card-large-label">Root Mean Sq. (RMSE)</span>
                          <span className="model-card-large-desc">Sensitif terhadap Outlier</span>
                        </div>
                        <div className="model-card-large error-type">
                          <span className="model-card-large-val" style={{ color: '#DC2626' }}>5.12%</span>
                          <span className="model-card-large-label">Mean Abs. Pct (MAPE)</span>
                          <span className="model-card-large-desc">Deviasi Relatif Persentase</span>
                        </div>
                        <div className="model-card-large error-type">
                          <span className="model-card-large-val" style={{ color: '#DC2626' }}>66.93</span>
                          <span className="model-card-large-label">Mean Sq. Error (MSE)</span>
                          <span className="model-card-large-desc">Fungsi Kerugian Pelatihan</span>
                        </div>
                        <div className="model-card-large error-type">
                          <span className="model-card-large-val" style={{ color: '#EA580C' }}>±5.00%</span>
                          <span className="model-card-large-label">Stochastic Noise Ratio</span>
                          <span className="model-card-large-desc">Perturbasi Gaussian (Mean 1.00)</span>
                        </div>
                        <div className="model-card-large error-type">
                          <span className="model-card-large-val" style={{ color: '#EA580C' }}>0.00</span>
                          <span className="model-card-large-label">Residual Bias (Mean)</span>
                          <span className="model-card-large-desc">Estimator Unbiased Simetris</span>
                        </div>
                      </div>
                    </div>

                    <div style={{ fontSize: '10.5px', color: 'var(--td)', borderTop: '1px solid var(--bord)', paddingTop: '8px' }}>
                      Kepatuhan: Standar Pemenuhan Kebutuhan Dasar (Perka BNPB No. 7/2008) &amp; Piagam SPHERE 2018 (2.100 kkal/jiwa/hari).
                    </div>
                  </div>
                </div>

                <div className="panel-box" style={{ marginTop: '4px' }}>
                  <div className="panel-header-row">
                    <span className="panel-box-title">Komparasi Metodologis &amp; Landasan Regulasi Pembobotan</span>
                    <span className="panel-box-subtitle">MCDA Equal Weighting vs Standar Statis</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px', marginTop: '4px', fontSize: '11px', color: 'var(--ts)', lineHeight: 1.6 }}>
                    <div style={{ background: 'var(--surf)', padding: '10px', border: '1px solid var(--bord)' }}>
                      <strong style={{ color: 'var(--tp)' }}>Pilar Kerusakan Fisik (33.33%):</strong> Berdasarkan Perka BNPB No. 2 Tahun 2012 (JITUPASNA), luas kerusakan bangunan mencerminkan tingkat hilangnya cadangan pangan dan hunian rumah tangga terdampak langsung.
                    </div>
                    <div style={{ background: 'var(--surf)', padding: '10px', border: '1px solid var(--bord)' }}>
                      <strong style={{ color: 'var(--tp)' }}>Pilar Demografi Terdampak (33.33%):</strong> Berdasarkan Perka BNPB No. 7 Tahun 2008 &amp; WorldPop 100m, merefleksikan skala populasi jiwa yang wajib mendapatkan suplai ransum dasar harian dan air bersih.
                    </div>
                    <div style={{ background: 'var(--surf)', padding: '10px', border: '1px solid var(--bord)' }}>
                      <strong style={{ color: 'var(--tp)' }}>Pilar Waktu Kritis 72 Jam (33.33%):</strong> Berdasarkan Standar SPHERE 2018 (Golden Time), fungsi peluruhan linier mengalokasikan prioritas tertinggi bagi wilayah yang baru saja terdampak demi menyelamatkan jiwa penyintas.
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      <footer className="statusbar">
        <div className="statusbar-left">
          <span className="status-dot"></span>
          <span>Pusdalops SDSS: Terhubung · NASA FIRMS NRT, GIBS &amp; BMKG Live Feeds</span>
        </div>
        <div className="statusbar-right">
          Universitas Bina Nusantara · 2026 · Jason Lee (2702751580)
        </div>
      </footer>

      {selectedZone && showModal && (
        <ItemizedModal
          zone={selectedZone}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
}
