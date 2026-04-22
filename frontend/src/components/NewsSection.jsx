import React, { useState, useEffect } from "react";
import { LuRss, LuExternalLink, LuClock } from "react-icons/lu";
import "../styles/NewsSection.css";

export default function NewsSection({ disasterInfo }) {
  const [news, setNews] = useState([]);

  useEffect(() => {
    // Mock data berita real-time
    const mockNews = [
      {
        id: 1,
        title: "Gempa Bumi Magnitudo 6.5 Guncang Yogyakarta",
        source: "BMKG",
        time: "2 jam lalu",
        category: "Earthquake",
        severity: "high",
      },
      {
        id: 2,
        title: "Banjir Bandang di Kuningan, 500 Kepala Keluarga Terdampak",
        source: "BNPB",
        time: "4 jam lalu",
        category: "Flood",
        severity: "critical",
      },
      {
        id: 3,
        title: "Gunung Merapi: Status Siaga Diwaspadai Setiap Saat",
        source: "PVMBG",
        time: "6 jam lalu",
        category: "Volcano",
        severity: "high",
      },
      {
        id: 4,
        title: "Kemarau Panjang Ancam Ketersediaan Air Bersih di Pulau Timur",
        source: "BMKG",
        time: "8 jam lalu",
        category: "Drought",
        severity: "medium",
      },
      {
        id: 5,
        title: "Longsor Menutup Akses Jalan Puncak Bogor",
        source: "BPBD Jabar",
        time: "10 jam lalu",
        category: "Landslide",
        severity: "high",
      },
    ];

    setNews(mockNews);
  }, []);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case "critical":
        return "#ef4444";
      case "high":
        return "#f97316";
      case "medium":
        return "#eab308";
      default:
        return "#3b82f6";
    }
  };

  const getSeverityLabel = (severity) => {
    switch (severity) {
      case "critical":
        return "KRITIS";
      case "high":
        return "TINGGI";
      case "medium":
        return "SEDANG";
      default:
        return "INFO";
    }
  };

  return (
    <div className="news-section">
      <div className="news-header">
        <div className="news-header-left">
          <span className="news-header-icon">
            <LuRss />
          </span>
          <div className="news-header-text">
            <h2>Berita</h2>
            <p>Bencana & Peringatan Dini Indonesia</p>
          </div>
        </div>
        <div className="news-live-indicator">
          <span className="live-dot"></span>
          <span>LIVE</span>
        </div>
      </div>

      <div className="news-container">
        {news.map((item) => (
          <div key={item.id} className="news-card">
            <div className="news-card-header">
              <span
                className="news-severity-badge"
                style={{ borderLeftColor: getSeverityColor(item.severity) }}
              >
                {getSeverityLabel(item.severity)}
              </span>
              <span className="news-source">{item.source}</span>
            </div>
            <h3 className="news-title">{item.title}</h3>
            <div className="news-card-footer">
              <span className="news-time">
                <LuClock size={14} />
                {item.time}
              </span>
              <a href="#" className="news-link">
                <LuExternalLink size={14} />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
