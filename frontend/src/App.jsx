import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { PolygonLayer, ScatterplotLayer } from '@deck.gl/layers';
import axios from 'axios';
import './styles/App.css';

import DeckMap from './components/DeckMap';
import LoadingSkeleton from './components/LoadingSkeleton';

function formatDecimal(val) {
  if (val === null || val === undefined || isNaN(val)) return '0';
  const num = Number(val);
  if (Number.isInteger(num)) return num.toString();
  return (Math.floor(num * 100) / 100).toFixed(2);
}

function ItemizedModal({ zone, onClose }) {
  if (!zone) return null;
  const item = zone.itemized_logistics || {};

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: 'var(--bg-card, #ffffff)',
        color: 'var(--text-primary, #1a1d26)',
        borderRadius: '14px',
        maxWidth: '750px',
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: 'var(--shadow-lg, 0 20px 25px -5px rgba(0, 0, 0, 0.5))',
        border: '1px solid var(--border, #e2e5eb)',
        padding: '28px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', borderBottom: '1px solid var(--border)', paddingBottom: '14px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>Rincian Paket Bantuan Logistik Per KK</h3>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>Desa {zone.desa} | {zone.count} KK Terdampak</span>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-secondary)',
              fontSize: '1.6rem',
              cursor: 'pointer',
              lineHeight: 1,
              padding: '0 4px'
            }}
          >&times;</button>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '0.92rem', color: 'var(--accent, #3b82f6)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 700 }}>Bantuan Pangan (Sembako 10 Hari)</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Beras</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.beras_kg)} kg</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Minyak Goreng</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.minyak_liter)} L</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Gula Pasir</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.gula_kg)} kg</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Mie Instan</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.indomie_pcs)} pcs ({Math.ceil((item.indomie_pcs || 0) / 40)} dus)</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Roma Sari Gandum</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.roma_sari_gandum_pack)} pack</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Roma Malkist Abon</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.roma_malkist_abon_pack)} pack</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Roma Kelapa</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.roma_kelapa_pack)} pack</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Roma Marie Susu</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.roma_marie_susu_pack)} pack</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Sarden Saus Tomat</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.sarden_pcs)} kaleng</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Kornet Beef</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.kornet_pcs)} kaleng</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Susu Full Cream</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.susu_full_cream_pcs)} pcs</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Susu Dancow</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.susu_dancow_box)} box</div>
            </div>
          </div>
        </div>

        <div>
          <h4 style={{ fontSize: '0.92rem', color: 'var(--danger, #dc2626)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 700 }}>Perlengkapan & Non-Pangan</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Matras</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.matras_pcs)} pcs</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Kasur Lipat</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.kasur_lipat_pcs)} pcs</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Kompor + Gas</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.kompor_set)} set</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Karpet Plastik</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.karpet_plastik_pcs)} pcs</div>
            </div>
            <div style={{ background: 'var(--bg-input, #f1f3f7)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Kipas Angin</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{formatDecimal(item.kipas_angin_pcs)} pcs</div>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '28px', textAlign: 'right' }}>
          <button
            onClick={onClose}
            style={{
              padding: '8px 20px',
              backgroundColor: 'var(--accent, #3b82f6)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >Tutup</button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [flyToTarget, setFlyToTarget] = useState(null);
  const [selectedZone, setSelectedZone] = useState(null);

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
      setData(res.data);
      setError(null);
    } catch (err) {
      console.error("Fetch error:", err);
      setError("Gagal memuat data dari server backend.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 10000);
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
          getElevation: 15,
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
          getElevation: d => 12,
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
    setFlyToTarget({
      lon: zone.lon,
      lat: zone.lat,
      timestamp: Date.now()
    });
  };

  const handleResolve = (e, desa) => {
    e.stopPropagation();
    if (window.confirm(`Tandai bencana di desa ${desa} sebagai selesai dan hapus dari prioritas?`)) {
      const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      axios.delete(`${API_URL}/resolve/${encodeURIComponent(desa)}`)
        .then(() => {
          fetchData();
        })
        .catch(err => console.error("Error resolving:", err));
    }
  };

  const getUnitLevel = (count) => {
    if (count >= 10) return 'high';
    if (count >= 5) return 'medium';
    return 'low';
  };

  const formatElapsed = (hours) => {
    if (!hours && hours !== 0) return '-';
    if (hours < 1) return `${Math.round(hours * 60)} menit lalu`;
    if (hours < 24) return `${Math.round(hours)} jam lalu`;
    return `${formatDecimal(hours / 24)} hari lalu`;
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

  const sortedZones = useMemo(() => {
    if (!redZones || redZones.length === 0) return [];
    const list = [...redZones];
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
      } else if (sortField === 'event_date') {
        valA = a.event_date ? new Date(a.event_date).getTime() : 0;
        valB = b.event_date ? new Date(b.event_date).getTime() : 0;
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
  }, [redZones, sortField, sortOrder]);

  const totalPages = Math.max(1, Math.ceil(sortedZones.length / pageSize));
  const paginatedZones = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedZones.slice(start, start + pageSize);
  }, [sortedZones, currentPage, pageSize]);

  const handleExportCSV = () => {
    if (redZones.length === 0) return;
    const headers = [
      "Prioritas", "Desa", "Jenis Bencana", "Waktu Kejadian", "Bangunan Rusak", "Populasi",
      "Beras (kg)", "Minyak (L)", "Gula (kg)", "Indomie (pcs)", "Sari Gandum (pack)",
      "Malkist Abon (pack)", "Kelapa (pack)", "Marie Susu (pack)", "Sarden (kaleng)",
      "Kornet (kaleng)", "Susu Full Cream (pcs)", "Susu Dancow (box)", "Matras (pcs)",
      "Kasur Lipat (pcs)", "Kompor (set)", "Karpet (pcs)", "Kipas Angin (pcs)", "Skor Prioritas"
    ];
    const rows = sortedZones.map(z => {
      const item = z.itemized_logistics || {};
      return [
        z.priority_label,
        z.desa,
        z.disaster_type,
        z.event_date ? new Date(z.event_date).toLocaleString('id-ID') : "-",
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

    const csvContent = "data:text/csv;charset=utf-8,"
      + [headers.join(","), ...rows.map(e => e.map(cell => `"${cell}"`).join(","))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Laporan_Distribusi_Logistik_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getSortIndicator = (field) => {
    if (sortField !== field) return '↕';
    return sortOrder === 'asc' ? '↑' : '↓';
  };

  return (
    <div className="dashboard-layout">
      <header className="dashboard-header">
        <div className="header-left">
          <div>
            <div className="header-title">SDSS Logistik Pangan Pasca Bencana</div>
            <div className="header-subtitle">Sistem Pendukung Keputusan Spasial</div>
          </div>
        </div>
        <div className="header-right">
          {data?.disaster_info?.summary && (
            <div className="disaster-badge">
              <span>{data.disaster_info.summary}</span>
            </div>
          )}
          <button className="theme-toggle" onClick={toggleTheme} title="Toggle Theme" id="theme-toggle-btn">
            {theme === 'dark' ? 'Light' : 'Dark'}
          </button>
        </div>
      </header>

      <main className="dashboard-content">
        {loading ? <LoadingSkeleton /> : (<>

          <div className="metrics-row" id="metrics-section">
            <div className="metric-card" id="metric-wilayah">
              <div className="metric-info">
                <span className="metric-label">Wilayah Terdampak</span>
                <span className="metric-value">{metrics.active_areas || 0}</span>
                <span className="metric-unit">Desa</span>
              </div>
            </div>

            <div className="metric-card" id="metric-terdampak">
              <div className="metric-info">
                <span className="metric-label">Est. Terdampak</span>
                <span className="metric-value">{(metrics.estimated_impacts || 0).toLocaleString()}</span>
                <span className="metric-unit">Jiwa</span>
              </div>
            </div>
          </div>

          <div className="map-section" id="map-section">
            <div className="map-toolbar">
              <div className="map-legend">
                <span className="legend-label">Prioritas:</span>
                <span className="legend-item">
                  <span className="legend-dot red"></span> Tinggi
                </span>
                <span className="legend-item">
                  <span className="legend-dot orange"></span> Sedang
                </span>
                <span className="legend-item">
                  <span className="legend-dot yellow"></span> Kecil
                </span>
                <span className="legend-item" style={{ marginLeft: '12px', borderLeft: '1px solid var(--border)', paddingLeft: '12px' }}>
                  <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#ff2828', border: '1.5px solid #fff', marginRight: '6px' }}></span> Titik Kerusakan
                </span>
                <span className="legend-item">
                  <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '2px', backgroundColor: 'rgba(220,38,38,0.55)', border: '1px solid rgba(220,38,38,0.8)', marginRight: '6px' }}></span> Area Kerusakan
                </span>
                <span className="legend-item">
                  <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '2px', backgroundColor: 'transparent', border: '2px solid #dc2626', marginRight: '6px' }}></span> Batas Desa
                </span>
              </div>
            </div>

            <div className="map-container">
              <DeckMap
                flyToTarget={flyToTarget}
                layers={layers}
                theme={theme}
              />
            </div>
          </div>

          <div className="table-section" id="data-table-section">
            <div className="table-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <div className="table-title">
                <h2>Prioritas Distribusi Logistik</h2>
              </div>
              {redZones.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    <span>Tampilkan:</span>
                    <select
                      value={pageSize}
                      onChange={(e) => { setPageSize(Number(e.target.value)); setCurrentPage(1); }}
                      style={{ padding: '4px 8px', borderRadius: '6px', border: '1px solid var(--border)', backgroundColor: 'var(--bg-input)', color: 'var(--text-primary)', fontSize: '0.8rem', cursor: 'pointer' }}
                    >
                      <option value={5}>5 baris</option>
                      <option value={10}>10 baris</option>
                      <option value={20}>20 baris</option>
                      <option value={50}>50 baris</option>
                    </select>
                  </div>
                  <span className="table-count">{redZones.length} zona</span>
                  <button
                    onClick={handleExportCSV}
                    style={{ fontSize: '0.75rem', padding: '6px 14px', background: 'var(--accent, #3b82f6)', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}
                  >Unduh Laporan CSV</button>
                </div>
              )}
            </div>

            {redZones.length === 0 ? (
              <div className="table-empty">Menunggu data dari backend...</div>
            ) : (
              <>
                <div className="table-scrollable">
                  <table className="data-table" id="damage-data-table">
                    <thead>
                      <tr>
                        <th onClick={() => handleSort('priority')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                          Prioritas {getSortIndicator('priority')}
                        </th>
                        <th onClick={() => handleSort('desa')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                          Desa {getSortIndicator('desa')}
                        </th>
                        <th onClick={() => handleSort('disaster_type')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                          Informasi Bencana {getSortIndicator('disaster_type')}
                        </th>
                        <th onClick={() => handleSort('event_date')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                          Waktu Kejadian {getSortIndicator('event_date')}
                        </th>
                        <th onClick={() => handleSort('count')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                          Kerusakan &amp; Populasi {getSortIndicator('count')}
                        </th>
                        <th onClick={() => handleSort('beras')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                          Alokasi Logistik DL (Beras/Minyak/Mie/Lainnya) {getSortIndicator('beras')}
                        </th>
                        <th>Aksi</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paginatedZones.map((zone, i) => {
                        const item = zone.itemized_logistics || {};
                        return (
                          <tr key={i} onClick={() => handleRowClick(zone)}>
                            <td>
                              <span className={`priority-badge ${zone.priority_label?.toLowerCase()}`}>
                                {zone.priority_label}
                              </span>
                            </td>
                            <td style={{ fontWeight: 600 }}>{zone.desa || 'Tidak Diketahui'}</td>
                            <td>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                <span className="disaster-type-badge">
                                  {zone.disaster_type || 'Bencana Alam'}
                                </span>
                                {zone.has_petabencana && (
                                  <span style={{ fontSize: '0.65rem', padding: '2px 6px', background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', borderRadius: '4px', display: 'inline-flex', alignItems: 'center', gap: '4px', width: 'fit-content', fontWeight: 600 }}>
                                    Citizen Report
                                  </span>
                                )}
                              </div>
                            </td>
                            <td>
                              <div style={{ lineHeight: 1.4 }}>
                                <span style={{ fontWeight: 600 }}>{formatElapsed(zone.elapsed_hours)}</span>
                                <br />
                                <span style={{ fontSize: '0.7rem', opacity: 0.7 }}>
                                  {zone.event_date ? new Date(zone.event_date).toLocaleString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-'}
                                </span>
                              </div>
                            </td>
                            <td>
                              <span className={`unit-badge ${getUnitLevel(zone.count)}`} style={{ padding: '4px 8px', borderRadius: '4px' }}>
                                {zone.count} Bangunan Rusak | {zone.population || zone.count * 4} Jiwa
                              </span>
                            </td>
                            <td>
                              <div
                                onClick={(e) => { e.stopPropagation(); setSelectedZone(zone); }}
                                style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '4px' }}
                                title="Klik untuk melihat rincian 17 item logistik"
                              >
                                <div className="logistics-mini">
                                  <span>Beras: {formatDecimal(item.beras_kg)} kg</span>
                                  <span>Minyak: {formatDecimal(item.minyak_liter)} L</span>
                                  <span>Mie: {formatDecimal(item.indomie_pcs)} pcs</span>
                                </div>
                                <span style={{ fontSize: '0.7rem', color: 'var(--accent, #3b82f6)', fontWeight: 600, textDecoration: 'underline' }}>
                                  Lihat Rincian 17 Item
                                </span>
                              </div>
                            </td>
                            <td>
                              <button
                                className="resolve-btn"
                                onClick={(e) => handleResolve(e, zone.desa)}
                                style={{ backgroundColor: '#10b981', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
                              >
                                Selesai Teratasi
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', padding: '8px 4px', flexWrap: 'wrap', gap: '12px' }}>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    Menampilkan {Math.min((currentPage - 1) * pageSize + 1, sortedZones.length)} - {Math.min(currentPage * pageSize, sortedZones.length)} dari {sortedZones.length} zona
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                      disabled={currentPage === 1}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '6px',
                        border: '1px solid var(--border)',
                        backgroundColor: currentPage === 1 ? 'transparent' : 'var(--bg-input)',
                        color: currentPage === 1 ? 'var(--text-tertiary)' : 'var(--text-primary)',
                        cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                        fontSize: '0.8rem',
                        fontWeight: 600
                      }}
                    >
                      Sebelumnya
                    </button>
                    {Array.from({ length: totalPages }, (_, idx) => idx + 1)
                      .filter(page => page === 1 || page === totalPages || Math.abs(page - currentPage) <= 1)
                      .map((page, idx, arr) => {
                        const showEllipsis = idx > 0 && page - arr[idx - 1] > 1;
                        return (
                          <React.Fragment key={page}>
                            {showEllipsis && <span style={{ color: 'var(--text-tertiary)', padding: '0 4px' }}>...</span>}
                            <button
                              onClick={() => setCurrentPage(page)}
                              style={{
                                padding: '6px 12px',
                                borderRadius: '6px',
                                border: '1px solid',
                                borderColor: currentPage === page ? 'var(--accent, #3b82f6)' : 'var(--border)',
                                backgroundColor: currentPage === page ? 'var(--accent, #3b82f6)' : 'var(--bg-input)',
                                color: currentPage === page ? 'white' : 'var(--text-primary)',
                                cursor: 'pointer',
                                fontSize: '0.8rem',
                                fontWeight: currentPage === page ? 700 : 500
                              }}
                            >
                              {page}
                            </button>
                          </React.Fragment>
                        );
                      })}
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                      disabled={currentPage === totalPages}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '6px',
                        border: '1px solid var(--border)',
                        backgroundColor: currentPage === totalPages ? 'transparent' : 'var(--bg-input)',
                        color: currentPage === totalPages ? 'var(--text-tertiary)' : 'var(--text-primary)',
                        cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                        fontSize: '0.8rem',
                        fontWeight: 600
                      }}
                    >
                      Selanjutnya
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </>)}
      </main>

      {selectedZone && (
        <ItemizedModal
          zone={selectedZone}
          onClose={() => setSelectedZone(null)}
        />
      )}
    </div>
  );
}
