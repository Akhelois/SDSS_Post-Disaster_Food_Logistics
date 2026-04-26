import React, { useState, useEffect } from 'react';
import { LuNewspaper, LuClock, LuMapPin, LuActivity, LuRefreshCw } from 'react-icons/lu';
import axios from 'axios';
import '../styles/NewsPanel.css';

const BMKG_URL = 'https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json';

function timeSince(dateStr) {
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const mins = Math.floor(diffMs / 60000);
    if (mins < 60) return `${mins} menit lalu`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} jam lalu`;
    const days = Math.floor(hours / 24);
    return `${days} hari lalu`;
  } catch {
    return dateStr;
  }
}

function magnitudeLevel(mag) {
  const m = parseFloat(mag);
  if (m >= 6.0) return 'critical';
  if (m >= 5.0) return 'high';
  if (m >= 4.0) return 'medium';
  return 'low';
}

export default function NewsPanel() {
  const [quakes, setQuakes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchData = () => {
    setLoading(true);
    axios.get(BMKG_URL, { timeout: 10000 })
      .then(res => {
        const data = res.data?.Infogempa?.gempa || [];
        setQuakes(data.slice(0, 8));
        setLastUpdate(new Date().toLocaleTimeString('id-ID'));
        setError(null);
        setLoading(false);
      })
      .catch(() => {
        setError('Gagal memuat data BMKG');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="news-panel">
      <div className="news-header">
        <div className="news-title">
          <LuNewspaper size={15} />
          <h3>Aktivitas Seismik Terkini</h3>
        </div>
        <button className="news-refresh" onClick={fetchData} title="Refresh">
          <LuRefreshCw size={13} className={loading ? 'spinning' : ''} />
        </button>
      </div>

      {lastUpdate && (
        <span className="news-updated">Update: {lastUpdate}</span>
      )}

      {error && <p className="news-error">{error}</p>}

      {!error && (
        <div className="news-list">
          {quakes.map((q, i) => {
            const level = magnitudeLevel(q.Magnitude);
            return (
              <div className="news-item" key={i}>
                <div className={`news-mag mag-${level}`}>
                  M{q.Magnitude}
                </div>
                <div className="news-body">
                  <p className="news-desc">{q.Wilayah}</p>
                  <div className="news-meta">
                    <span><LuActivity size={11} /> {q.Kedalaman}</span>
                    <span><LuClock size={11} /> {q.DateTime ? timeSince(q.DateTime) : `${q.Tanggal} ${q.Jam}`}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
