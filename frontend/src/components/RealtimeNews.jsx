import React, { useState, useEffect } from "react";
import { LuBell, LuCheck, LuTrendingUp } from "react-icons/lu";
import "../styles/RealtimeNews.css";

export default function RealtimeNews() {
  const [news, setNews] = useState([]);
  const [expandedId, setExpandedId] = useState(null);

  // Mock real-time news data - in production, this would come from WebSocket or polling
  useEffect(() => {
    const mockNews = [
      {
        id: 1,
        timestamp: new Date(Date.now() - 5 * 60000),
        title: "Critical Alert: Banjir Di Kampung Baru",
        description:
          "Banjir setinggi 2 meter terdeteksi di wilayah Kampung Baru, Yogyakarta. Tim evakuasi telah dikirim.",
        type: "alert",
        severity: "high",
        location: "Yogyakarta",
        icon: LuBell,
      },
      {
        id: 2,
        timestamp: new Date(Date.now() - 15 * 60000),
        title: "Relief Supplies Arrived",
        description:
          "1,500 paket bantuan makanan dan 5,000 liter air bersih tiba di pos distribusi utama.",
        type: "success",
        severity: "normal",
        location: "Distribution Center",
        icon: LuCheck,
      },
      {
        id: 3,
        timestamp: new Date(Date.now() - 45 * 60000),
        title: "Evacuation Status Update",
        description:
          "3,200 warga telah dievakuasi dengan aman. Operasi evakuasi berlanjut di zona C dan D.",
        type: "info",
        severity: "medium",
        location: "Multiple Zones",
        icon: LuTrendingUp,
      },
      {
        id: 4,
        timestamp: new Date(Date.now() - 120 * 60000),
        title: "Emergency Response Activated",
        description:
          "Pusat Operasi Darurat telah diaktifkan. Semua tim siaga telah diperingatkan dan siap bertindak.",
        type: "alert",
        severity: "high",
        location: "Command Center",
        icon: LuBell,
      },
      {
        id: 5,
        timestamp: new Date(Date.now() - 180 * 60000),
        title: "Medical Team Deployed",
        description:
          "Regu medis profesional dikirim ke area terdampak untuk penanganan cedera dan kesehatan.",
        type: "info",
        severity: "normal",
        location: "Medical Posts",
        icon: LuCheck,
      },
    ];

    setNews(mockNews);
  }, []);

  const formatTime = (date) => {
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="realtime-news">
      <div className="news-header">
        <div className="header-content">
          <LuBell size={20} className="bell-icon" />
          <h3>Berita Terbaru</h3>
          <span className="news-count">{news.length}</span>
        </div>
      </div>

      <div className="news-list">
        {news.map((item) => {
          const IconComponent = item.icon;
          return (
            <div
              key={item.id}
              className={`news-item ${item.severity} ${expandedId === item.id ? "expanded" : ""}`}
              onClick={() =>
                setExpandedId(expandedId === item.id ? null : item.id)
              }
            >
              <div className="news-item-header">
                <div className="news-icon-wrapper">
                  <IconComponent
                    size={18}
                    className={`news-icon ${item.type}`}
                  />
                </div>

                <div className="news-content-main">
                  <div className="news-title">{item.title}</div>
                  <div className="news-meta">
                    <span className="news-location">{item.location}</span>
                    <span className="news-time">
                      {formatTime(item.timestamp)}
                    </span>
                  </div>
                </div>

                <div className={`severity-dot ${item.severity}`} />
              </div>

              {expandedId === item.id && (
                <div className="news-item-details">
                  <p>{item.description}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
