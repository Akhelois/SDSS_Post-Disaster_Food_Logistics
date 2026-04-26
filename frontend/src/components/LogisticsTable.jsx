import React from 'react';
import { LuList, LuMapPin, LuTriangleAlert, LuPackage, LuDroplet, LuBox, LuArchive } from 'react-icons/lu';
import '../styles/LogisticsTable.css';

export default function LogisticsTable({ data, onRowClick }) {
  const redZones = data?.map_data?.red_zones || [];

  if (!redZones.length) {
    return (
      <div className="logistics-panel">
        <div className="logistics-header">
          <LuList size={15} />
          <h3>Area Terdampak</h3>
        </div>
        <p className="table-empty">Menunggu data...</p>
      </div>
    );
  }

  return (
    <div className="logistics-panel">
      <div className="logistics-header">
        <LuList size={15} />
        <h3>Area Terdampak</h3>
        <span className="logistics-count">{redZones.length}</span>
      </div>
      <div className="logistics-list">
        {redZones.map((zone, i) => (
          <div className="zone-item" key={i} onClick={() => onRowClick(zone)}>
            <div className="zone-top">
              <span className="zone-name">{zone.desa}</span>
              <span className="zone-badge">{zone.count}</span>
            </div>
            <div className="zone-info">
              <span><LuTriangleAlert size={12} /> {zone.disaster_type || 'Bencana Alam'}</span>
              <span><LuMapPin size={12} /> {zone.lon.toFixed(3)}, {zone.lat.toFixed(3)}</span>
            </div>
            {zone.logistics && (
              <div className="zone-logistics">
                <span><LuPackage size={11} /> {zone.logistics.beras} kg</span>
                <span><LuDroplet size={11} /> {zone.logistics.air} L</span>
                <span><LuBox size={11} /> {zone.logistics.mie} dus</span>
                <span><LuArchive size={11} /> {zone.logistics.lauk} pkt</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
