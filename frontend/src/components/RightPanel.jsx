import React from "react";
import {
  LuX,
  LuTrendingUp,
  LuUsers,
  LuMapPin,
  LuCalendar,
} from "react-icons/lu";
import "../styles/RightPanel.css";

export default function RightPanel({
  selectedMarker,
  allLocations = [],
  onClose,
  onSelectLocation,
}) {
  if (!selectedMarker) {
    return (
      <div className="right-panel empty">
        <div className="locations-list">
          <h3 className="list-title">Damaged Locations</h3>
          <div className="locations-scroll">
            {allLocations && allLocations.length > 0 ? (
              allLocations.map((location, idx) => (
                <div
                  key={idx}
                  className="location-item"
                  onClick={() => onSelectLocation(location)}
                >
                  <div className="location-header">
                    <h4>{location.desa}</h4>
                    <span
                      className={`damage-badge severity-${location.count > 100 ? "high" : location.count > 50 ? "medium" : "low"}`}
                    >
                      {location.count} units
                    </span>
                  </div>
                  <div className="location-meta">
                    <span className="disaster-type">
                      {location.disaster_type}
                    </span>
                    <span className="affected">
                      ~{location.count * 4} affected
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <LuMapPin size={48} />
                <p>No damaged locations found</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Use actual marker data from selectedMarker prop
  const data = {
    title: selectedMarker.desa || "Unknown Location",
    coordinates: [selectedMarker.lon, selectedMarker.lat],
    severity:
      selectedMarker.count > 100
        ? "High"
        : selectedMarker.count > 50
          ? "Medium"
          : "Low",
    damageCount: selectedMarker.count || 0,
    affectedPopulation: (selectedMarker.count || 0) * 4,
    lastUpdated: "Just now",
    disasterType: selectedMarker.disaster_type || "Bencana Alam",
    stats: [
      {
        label: "Buildings Damaged",
        value: selectedMarker.count || 0,
        color: "#ef4444",
      },
      {
        label: "Estimated Affected",
        value: `${(selectedMarker.count || 0) * 4}`,
        color: "#f97316",
      },
      { label: "Relief Distributed", value: "62%", color: "#10b981" },
    ],
    logistics: selectedMarker.logistics || {},
    timeline: [
      { time: "Now", event: "Data received" },
      { time: "2h ago", event: "Initial assessment" },
      { time: "4h ago", event: "Incident reported" },
    ],
  };

  return (
    <div className="right-panel active">
      <div className="panel-header">
        <div className="panel-title">
          <h2>{data.title}</h2>
          <span
            className={`severity-badge severity-${data.severity.toLowerCase()}`}
          >
            {data.severity}
          </span>
        </div>
        <button className="close-btn" onClick={onClose}>
          <LuX size={20} />
        </button>
      </div>

      <div className="panel-content">
        <div className="location-info">
          <div className="info-row">
            <LuMapPin size={16} />
            <span>
              {data.coordinates[0].toFixed(4)}, {data.coordinates[1].toFixed(4)}
            </span>
          </div>
          <div className="info-row">
            <LuCalendar size={16} />
            <span>Updated {data.lastUpdated}</span>
          </div>
        </div>

        <div className="stats-grid">
          {data.stats.map((stat, idx) => (
            <div key={idx} className="stat-card">
              <div className="stat-header">
                <span className="stat-label">{stat.label}</span>
              </div>
              <div className="stat-value" style={{ color: stat.color }}>
                {stat.value}
              </div>
              <div className="stat-bar">
                <div
                  className="stat-fill"
                  style={{
                    width: `${Math.min(parseFloat(stat.value), 100)}%`,
                    backgroundColor: stat.color,
                  }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="chart-placeholder">
          <div className="chart-header">
            <LuTrendingUp size={16} />
            <h4>Damage Assessment Trend</h4>
          </div>
          <div className="chart-bars">
            <div className="bar" style={{ height: "30%" }} />
            <div className="bar" style={{ height: "55%" }} />
            <div className="bar" style={{ height: "75%" }} />
            <div className="bar" style={{ height: "92%" }} />
            <div className="bar" style={{ height: "85%" }} />
          </div>
        </div>

        <div className="timeline-section">
          <h4>Recent Activity</h4>
          <div className="timeline">
            {data.timeline.map((item, idx) => (
              <div key={idx} className="timeline-item">
                <div className="timeline-marker" />
                <div className="timeline-content">
                  <span className="timeline-time">{item.time}</span>
                  <span className="timeline-event">{item.event}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {data.logistics && Object.keys(data.logistics).length > 0 && (
          <div className="logistics-section">
            <h4>📦 Kebutuhan Logistik</h4>
            <div className="logistics-grid">
              {data.logistics.beras && (
                <div className="logistics-item">
                  <span className="logistics-emoji">🍚</span>
                  <div className="logistics-detail">
                    <span className="logistics-name">Beras</span>
                    <span className="logistics-amount">
                      {(data.logistics.beras || 0).toLocaleString("id-ID")} kg
                    </span>
                  </div>
                </div>
              )}
              {data.logistics.air && (
                <div className="logistics-item">
                  <span className="logistics-emoji">💧</span>
                  <div className="logistics-detail">
                    <span className="logistics-name">Air Bersih</span>
                    <span className="logistics-amount">
                      {(data.logistics.air || 0).toLocaleString("id-ID")} L
                    </span>
                  </div>
                </div>
              )}
              {data.logistics.mie && (
                <div className="logistics-item">
                  <span className="logistics-emoji">🍜</span>
                  <div className="logistics-detail">
                    <span className="logistics-name">Mie Instan</span>
                    <span className="logistics-amount">
                      {(data.logistics.mie || 0).toLocaleString("id-ID")} Dus
                    </span>
                  </div>
                </div>
              )}
              {data.logistics.minyak && (
                <div className="logistics-item">
                  <span className="logistics-emoji">🫒</span>
                  <div className="logistics-detail">
                    <span className="logistics-name">Minyak Goreng</span>
                    <span className="logistics-amount">
                      {(data.logistics.minyak || 0).toLocaleString("id-ID")} L
                    </span>
                  </div>
                </div>
              )}
              {data.logistics.lauk && (
                <div className="logistics-item">
                  <span className="logistics-emoji">🥫</span>
                  <div className="logistics-detail">
                    <span className="logistics-name">Lauk Kaleng</span>
                    <span className="logistics-amount">
                      {(data.logistics.lauk || 0).toLocaleString("id-ID")} Pkt
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
