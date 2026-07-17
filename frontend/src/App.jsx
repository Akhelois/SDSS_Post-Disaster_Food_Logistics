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

  // Polygon hull yang mengikuti bentuk persis dari sekumpulan titik kerusakan
  const damageHulls = useMemo(() => {
    return redZones
      .filter(z => z.damage_polygon && z.damage_polygon.length > 0)
      .map(z => ({
        ...z,
        polygon: z.damage_polygon,
        priority: z.priority_label
      }));
  }, [redZones]);

  // Kumpulkan building footprints (zona DENGAN bangunan OSM)
  const buildingFootprints = useMemo(() => {
    const buildings = [];
    for (const zone of redZones) {
      const footprints = zone.building_footprints || [];
      for (const fp of footprints) {
        buildings.push({
          polygon: fp,
          priority: zone.priority_label,
          desa: zone.desa,
          disaster_type: zone.disaster_type,
          count: zone.count,
          population: zone.population,
          logistics: zone.logistics,
        });
      }
    }
    return buildings;
  }, [redZones]);

  // Heatmap color: makin tinggi prioritas -> makin merah
  const heatColor = (count, priority) => {
    if (priority === 'Tinggi')  return [200, 30, 20];    // merah
    if (priority === 'Sedang')  return [230, 120, 20];   // oranye
    return [240, 190, 40];                                // kuning
  };

  const heatOpacity = (count) => {
    if (count >= 10) return 160;
    if (count >= 5) return 120;
    if (count >= 3) return 90;
    return 60;
  };

  const layers = useMemo(() => {
    const filteredZones = redZones.filter(d => d.polygon);

    const priorityFill = (label) => {
      if (label === 'Tinggi') return [239, 68, 68];
      if (label === 'Sedang') return [249, 115, 22];
      return [234, 179, 8];
    };

    return [
      // Layer 1: Polygon desa — fill heatmap (warna mengikuti bentuk geografis desa/kerusakan)
      ...(filteredZones.length > 0 ? [
        new PolygonLayer({
          id: 'damage-zones-heat',
          data: filteredZones,
          getPolygon: d => d.polygon,
          getFillColor: d => [...heatColor(d.count, d.priority_label), heatOpacity(d.count)],
          getLineColor: d => [...priorityFill(d.priority_label), 200],
          lineWidthMinPixels: 2,
          filled: true,
          stroked: true,
          pickable: true,
          extruded: false
        })
      ] : []),

      // Layer 1.5: Heatmap Area (Polygon Khusus Kerusakan)
      ...(damageHulls.length > 0 ? [
        new PolygonLayer({
          id: 'damage-heatmap-polygon',
          data: damageHulls,
          getPolygon: d => d.polygon,
          getFillColor: d => [...heatColor(d.count, d.priority), 200], // Opacity 200/255
          getLineColor: d => [...heatColor(d.count, d.priority), 255],
          lineWidthMinPixels: 2,
          filled: true,
          stroked: true,
          pickable: true,
          extruded: false,
        })
      ] : []),

      // Layer 2: Building footprints
      ...(buildingFootprints.length > 0 ? [
        new PolygonLayer({
          id: 'building-footprints',
          data: buildingFootprints,
          getPolygon: d => d.polygon,
          getFillColor: d => [...priorityFill(d.priority), 190],
          getLineColor: d => [...priorityFill(d.priority), 255],
          lineWidthMinPixels: 2,
          filled: true,
          stroked: true,
          pickable: true,
          extruded: true,
          getElevation: 15,
        })
      ] : [])
    ];
  }, [redZones, buildingFootprints, damageHulls]);

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

  // Format elapsed time: "12.5 jam lalu" atau "2.1 hari lalu"
  const formatElapsed = (hours) => {
    if (!hours && hours !== 0) return '-';
    if (hours < 1) return `${Math.round(hours * 60)} menit lalu`;
    if (hours < 24) return `${Math.round(hours)} jam lalu`;
    return `${(hours / 24).toFixed(1)} hari lalu`;
  };

  // Urgency badge berdasarkan Golden Time 72 jam (Sphere Standards 2018)
  const getUrgencyBadge = (hours) => {
    if (!hours && hours !== 0) return { emoji: '⚪', label: 'N/A', cls: '' };
    if (hours < 24) return { emoji: '🔴', label: '< 24 jam', cls: 'urgency-high' };
    if (hours < 48) return { emoji: '🟠', label: '24-48 jam', cls: 'urgency-med' };
    if (hours < 72) return { emoji: '🟡', label: '48-72 jam', cls: 'urgency-low' };
    return { emoji: '⚪', label: '> 72 jam', cls: 'urgency-expired' };
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
            {/* <p className="header-subtitle">
              Sistem Pendukung Keputusan Otomatis: Peta Prioritas Distribusi (Data Realtime hingga H+5 Pasca-Bencana)
            </p> */}
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
                  <span className="legend-dot red"></span> Tinggi
                </span>
                <span className="legend-item">
                  <span className="legend-dot orange"></span> Sedang
                </span>
                <span className="legend-item">
                  <span className="legend-dot yellow"></span> Kecil
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

            {/* <div className="map-caption">
              <strong>Logika SDSS:</strong> Menggunakan analisis spasial (GIS) untuk menentukan Peta Prioritas Distribusi Pangan berdasarkan densitas kerusakan, estimasi populasi terdampak, dan kedekatan jarak dengan gudang logistik BNPB/BPBD.
            </div> */}
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
                      <th>Waktu Kejadian</th>
                      <th>Titik Kerusakan Bangunan</th>
                      <th>Kebutuhan Logistik</th>
                      <th>Aksi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {redZones.map((zone, i) => {
                      const ub = getUrgencyBadge(zone.elapsed_hours);
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
                              <LuTriangleAlert size={11} />
                              {zone.disaster_type || 'Bencana Alam'}
                            </span>
                            {zone.has_petabencana && (
                              <span style={{ fontSize: '0.65rem', padding: '2px 6px', background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', borderRadius: '4px', display: 'inline-flex', alignItems: 'center', gap: '4px', width: 'fit-content', fontWeight: 600 }}>
                                📱 Citizen Report
                              </span>
                            )}
                          </div>
                        </td>
                        <td>
                          <div style={{ lineHeight: 1.4 }}>
                            <span style={{ fontWeight: 600 }}>{ub.emoji} {formatElapsed(zone.elapsed_hours)}</span>
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
                          {zone.logistics && (
                            <div className="logistics-mini">
                              <span>🍚 {zone.logistics.beras} kg</span>
                              <span>💧 {zone.logistics.air} L</span>
                              <span>📦 {zone.logistics.mie} dus</span>
                            </div>
                          )}
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
                    )})}
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
