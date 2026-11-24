import React from 'react';
import { LuMap, LuUsers } from 'react-icons/lu';
import '../styles/MetricCards.css';

export default function MetricCards({ metrics }) {
  const items = [
    { icon: <LuMap />, label: 'Wilayah', value: metrics?.active_areas || 0, color: 'blue' },
    { icon: <LuUsers />, label: 'Terdampak', value: `${metrics?.estimated_impacts || 0} Jiwa`, color: 'gray' },
  ];

  return (
    <div className="metrics-row">
      {items.map((item, i) => (
        <div className={`metric-box metric-${item.color}`} key={i}>
          <span className="metric-icon">{item.icon}</span>
          <div>
            <span className="metric-label">{item.label}</span>
            <span className="metric-val">{item.value}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
