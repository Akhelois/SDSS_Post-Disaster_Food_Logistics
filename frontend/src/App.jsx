import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { PolygonLayer } from '@deck.gl/layers';
import axios from 'axios';
import { LuRadar, LuMoon, LuSun, LuTriangleAlert, LuMap, LuUsers, LuTable2 } from 'react-icons/lu';
import './styles/App.css';

import DeckMap from './components/DeckMap';
import LoadingSkeleton from './components/LoadingSkeleton';

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [flyToTarget, setFlyToTarget] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem('app-theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const fetchData = useCallback(() => {
    setLoading(true);
    const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    axios.get(`${API_URL}/`)
      .then(res => {
        setData(res.data);
        setLoading(false);

        const zones = res.data?.map_data?.red_zones || [];
        if (zones.length > 0) {
          const avgLon = zones.reduce((s, z) => s + z.lon, 0) / zones.length;
          const avgLat = zones.reduce((s, z) => s + z.lat, 0) / zones.length;
          setFlyToTarget({
            lon: avgLon,
            lat: avgLat
          });
        }
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const toggleTheme = useCallback(() => {
    setTheme(prev => {
      const newTheme = prev === 'dark' ? 'light' : 'dark';
      localStorage.setItem('app-theme', newTheme);
      return newTheme;
    });
  }, []);

  const mapData = data?.map_data || {};
  const metrics = data?.metrics || {};
  const redZones = mapData.red_zones || [];

  // Hapus semua raw points karena user tidak ingin melihat titik atau heatmap
  const allRawPoints = [];

  const layers = useMemo(() => {
    const filteredZones = redZones.filter(d => d.polygon);
    
    return [
      ...(filteredZones.length > 0 ? [
        new PolygonLayer({
          id: 'damage-zones',
          data: filteredZones,
          getPolygon: d => d.polygon,
          getFillColor: d => {
            if (d.priority_label === 'Kritis') return [239, 68, 68, 120];
            if (d.priority_label === 'Tinggi') return [249, 115, 22, 120];
            if (d.priority_label === 'Sedang') return [234, 179, 8, 120];
            return [34, 197, 94, 120];
          },
          getLineColor: d => {
            if (d.priority_label === 'Kritis') return [239, 68, 68, 255];
            if (d.priority_label === 'Tinggi') return [249, 115, 22, 255];
            if (d.priority_label === 'Sedang') return [234, 179, 8, 255];
            return [34, 197, 94, 255];
          },
          lineWidthMinPixels: 1.5,
          filled: true,
          stroked: true,
          pickable: true,
          extruded: false
        })
      ] : [])
    ];
  }, [allRawPoints, redZones]);

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
      axios.delete(`${API_URL}/resolve/${desa}`)
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

  return (
    <div className="dashboard-layout">

      <header className="dashboard-header" id="dashboard-header">
        <div className="header-left">
          <div className="header-icon">
            <LuRadar />
          </div>
          <div>
            <h1 className="header-title">SDSS Logistik Bencana Nasional</h1>
            <p className="header-subtitle">
              Sistem Pendukung Keputusan Otomatis: Peta Prioritas Distribusi (Data Realtime hingga H+5 Pasca-Bencana)
            </p>
          </div>
        </div>
        <div className="header-right">
          {data?.disaster_info?.summary && (
            <div className="disaster-badge">
              <LuTriangleAlert size={13} />
              <span>{data.disaster_info.summary}</span>
            </div>
          )}
          <button className="theme-toggle" onClick={toggleTheme} title="Toggle Theme" id="theme-toggle-btn">
            {theme === 'dark' ? <LuSun size={17} /> : <LuMoon size={17} />}
          </button>
        </div>
      </header>

      <main className="dashboard-content">
        {loading ? <LoadingSkeleton /> : (<>

        <div className="metrics-row" id="metrics-section">
          <div className="metric-card" id="metric-wilayah">
            <div className="metric-icon-wrapper accent">
              <LuMap />
            </div>
            <div className="metric-info">
              <span className="metric-label">Wilayah Terdampak</span>
              <span className="metric-value">{metrics.active_areas || 0}</span>
              <span className="metric-unit">Desa</span>
            </div>
          </div>

          <div className="metric-card" id="metric-terdampak">
            <div className="metric-icon-wrapper success">
              <LuUsers />
            </div>
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
                <span className="legend-dot red"></span> Kritis
              </span>
              <span className="legend-item">
                <span className="legend-dot orange"></span> Tinggi
              </span>
              <span className="legend-item">
                <span className="legend-dot yellow"></span> Sedang
              </span>
              <span className="legend-item">
                <span className="legend-dot green"></span> Rendah
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

          <div className="map-caption">
            <strong>Logika SDSS:</strong> Menggunakan analisis spasial (GIS) untuk menentukan Peta Prioritas Distribusi Pangan berdasarkan densitas kerusakan, estimasi populasi terdampak, dan kedekatan jarak dengan gudang logistik BNPB/BPBD.
          </div>
        </div>

        <div className="table-section" id="data-table-section">
          <div className="table-header">
            <div className="table-title">
              <LuTable2 className="table-title-icon" />
              <h2>Prioritas Distribusi Pangan</h2>
            </div>
            {redZones.length > 0 && (
              <span className="table-count">{redZones.length} zona</span>
            )}
          </div>

          {redZones.length === 0 ? (
            <div className="table-empty">Menunggu data dari backend...</div>
          ) : (
            <div className="table-scrollable">
              <table className="data-table" id="damage-data-table">
                <thead>
                  <tr>
                    <th>Prioritas</th>
                    <th>ADM4_EN (Desa)</th>
                    <th>Informasi Bencana</th>
                    <th>Titik Kerusakan Bangunan</th>
                    <th>Kebutuhan Logistik</th>
                    <th>Gudang Terdekat</th>
                    <th>Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  {redZones.map((zone, i) => (
                    <tr key={i} onClick={() => handleRowClick(zone)}>
                      <td>
                        <span className={`priority-badge ${zone.priority_label?.toLowerCase()}`}>
                          {zone.priority_label}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>{zone.desa || 'Tidak Diketahui'}</td>
                      <td>
                        <span className="disaster-type-badge">
                          <LuTriangleAlert size={11} />
                          {zone.disaster_type || 'Banjir / Tanah Longsor'}
                        </span>
                      </td>
                      <td>
                        <span className={`unit-badge ${getUnitLevel(zone.count)}`} style={{ padding: '4px 8px', borderRadius: '4px' }}>
                          {zone.count} Bangunan Rusak | {zone.population || zone.count * 4} Jiwa
                        </span>
                      </td>
                      <td>
                        {zone.logistics && (
                          <div className="logistics-mini">
                            <span>🍚 {zone.logistics.beras} kg</span>
                            <span>💧 {zone.logistics.air} L</span>
                            <span>📦 {zone.logistics.mie} dus</span>
                          </div>
                        )}
                      </td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {zone.gudang_terdekat || '-'} <br/>
                        <span style={{fontSize: '0.7rem', opacity: 0.8}}>({zone.jarak_gudang_km ? `${zone.jarak_gudang_km} km` : '-'})</span>
                      </td>
                      <td>
                        <button 
                          className="resolve-btn"
                          onClick={(e) => handleResolve(e, zone.desa)}
                        >
                          Selesai
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        </>)}
      </main>
    </div>
  );
}
