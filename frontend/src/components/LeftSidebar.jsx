import React, { useState } from "react";
import {
  LuMap,
  LuBell,
  LuTrendingUp,
  LuEye,
  LuEyeOff,
  LuChevronDown,
} from "react-icons/lu";
import "../styles/LeftSidebar.css";

export default function LeftSidebar({ visibleLayers, onLayerToggle }) {
  const [expandedCategory, setExpandedCategory] = useState("layers");

  const layerCategories = {
    layers: {
      title: "Map Layers",
      icon: <LuMap size={16} />,
      items: [
        { id: "disaster_zones", label: "Disaster Zones", color: "#ef4444" },
        { id: "damage_points", label: "Damage Points", color: "#f97316" },
        { id: "relief_hubs", label: "Relief Hubs", color: "#10b981" },
        {
          id: "evacuation_routes",
          label: "Evacuation Routes",
          color: "#3b82f6",
        },
      ],
    },
    alerts: {
      title: "Alerts & Events",
      icon: <LuBell size={16} />,
      items: [
        { id: "critical_alerts", label: "Critical Alerts", color: "#ef4444" },
        { id: "warnings", label: "Warnings", color: "#f97316" },
        { id: "updates", label: "Updates", color: "#3b82f6" },
      ],
    },
    analytics: {
      title: "Analytics",
      icon: <LuTrendingUp size={16} />,
      items: [
        { id: "heatmap", label: "Damage Heatmap", color: "#a855f7" },
        { id: "population", label: "Affected Population", color: "#06b6d4" },
        { id: "logistics", label: "Logistics Flow", color: "#eab308" },
      ],
    },
  };

  const toggleCategory = (category) => {
    setExpandedCategory(expandedCategory === category ? null : category);
  };

  return (
    <div className="left-sidebar">
      <div className="sidebar-title">
        <h2>Layers & Filters</h2>
      </div>

      <div className="layers-container">
        {Object.entries(layerCategories).map(([categoryKey, category]) => (
          <div key={categoryKey} className="layer-category">
            <button
              className="category-header"
              onClick={() => toggleCategory(categoryKey)}
            >
              <span className="category-icon">{category.icon}</span>
              <span className="category-title">{category.title}</span>
              <LuChevronDown
                size={16}
                className={`chevron ${expandedCategory === categoryKey ? "open" : ""}`}
              />
            </button>

            {expandedCategory === categoryKey && (
              <div className="category-items">
                {category.items.map((item) => (
                  <div key={item.id} className="layer-item">
                    <button
                      className="layer-toggle"
                      onClick={() => onLayerToggle(item.id)}
                    >
                      <div className="toggle-visual">
                        {visibleLayers[item.id] ? (
                          <LuEye size={14} />
                        ) : (
                          <LuEyeOff size={14} />
                        )}
                      </div>
                      <span
                        className="layer-label"
                        style={{
                          opacity: visibleLayers[item.id] ? 1 : 0.5,
                        }}
                      >
                        {item.label}
                      </span>
                      <div
                        className="layer-color"
                        style={{ backgroundColor: item.color }}
                      />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="sidebar-stats">
        <div className="stat-item">
          <span className="stat-label">Active Layers</span>
          <span className="stat-value">
            {Object.values(visibleLayers).filter(Boolean).length}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Total Markers</span>
          <span className="stat-value">127</span>
        </div>
      </div>
    </div>
  );
}
