import React, { useState, useRef, useEffect, useCallback } from 'react';
import DeckGL from '@deck.gl/react';
import { FlyToInterpolator } from '@deck.gl/core';
import { Map } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';

function formatDecimal(val) {
  if (val === null || val === undefined || isNaN(val)) return '0';
  const num = Number(val);
  if (Number.isInteger(num)) return num.toString();
  return (Math.floor(num * 100) / 100).toFixed(2);
}

const MAP_STYLES = {
  satellite: {
    version: 8,
    sources: {
      'basemap': {
        type: 'raster',
        tiles: [
          'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        ],
        tileSize: 256,
        attribution: '&copy; NASA Earthdata / Esri World Imagery'
      }
    },
    layers: [{ id: 'basemap-layer', type: 'raster', source: 'basemap', minzoom: 0, maxzoom: 19 }]
  },
  light: {
    version: 8,
    sources: {
      'basemap': {
        type: 'raster',
        tiles: [
          'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
          'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
          'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png'
        ],
        tileSize: 256,
        attribution: '&copy; OpenStreetMap contributors'
      }
    },
    layers: [{ id: 'basemap-layer', type: 'raster', source: 'basemap', minzoom: 0, maxzoom: 19 }]
  },
  dark: {
    version: 8,
    sources: {
      'basemap': {
        type: 'raster',
        tiles: ['https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'],
        tileSize: 256,
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
      }
    },
    layers: [{ id: 'basemap-layer', type: 'raster', source: 'basemap', minzoom: 0, maxzoom: 19 }]
  }
};

const INITIAL_VIEW_STATE = {
  longitude: 119.84,
  latitude: -0.9,
  zoom: 9,
  pitch: 45,
  bearing: 0
};

export default function DeckMap({ flyToTarget, layers, theme = 'dark', onZoomChange }) {
  const [mapMode, setMapMode] = useState(theme);
  
  useEffect(() => {
    setMapMode(theme);
  }, [theme]);

  const currentStyle = MAP_STYLES[mapMode] || MAP_STYLES.dark;
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  const [tooltip, setTooltip] = useState(null);
  const tooltipRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (flyToTarget) {
      const newZoom = 13.5;
      setViewState(prev => ({
        ...prev,
        longitude: flyToTarget.lon,
        latitude: flyToTarget.lat,
        zoom: newZoom,
        transitionDuration: 1500,
        transitionInterpolator: new FlyToInterpolator()
      }));
      if (onZoomChange) onZoomChange(newZoom);
    }
  }, [flyToTarget]);

  const onHover = useCallback((info) => {
    if (info.object && (info.object.count !== undefined || info.object.desa !== undefined)) {
      setTooltip({
        x: info.x,
        y: info.y,
        object: info.object
      });
    } else {
      setTooltip(null);
    }
  }, []);

  const getTooltipStyle = () => {
    if (!tooltip || !tooltipRef.current || !containerRef.current) return { display: 'none' };

    const container = containerRef.current.getBoundingClientRect();
    const ttRect = tooltipRef.current.getBoundingClientRect();
    const pad = 12;

    let left = tooltip.x + pad;
    let top = tooltip.y + pad;

    if (left + ttRect.width > container.width) {
      left = tooltip.x - ttRect.width - pad;
    }
    if (top + ttRect.height > container.height) {
      top = tooltip.y - ttRect.height - pad;
    }
    left = Math.max(pad, Math.min(left, container.width - ttRect.width - pad));
    top = Math.max(pad, Math.min(top, container.height - ttRect.height - pad));

    return {
      position: 'absolute',
      left: `${left}px`,
      top: `${top}px`,
      pointerEvents: 'none',
      zIndex: 20,
    };
  };

  const obj = tooltip?.object;
  const item = obj?.itemized_logistics;

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div style={{
        position: 'absolute',
        top: '12px',
        right: '12px',
        zIndex: 10,
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(8px)',
        padding: '4px',
        borderRadius: '8px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        display: 'flex',
        gap: '4px'
      }}>
        <button
          onClick={() => setMapMode('satellite')}
          style={{
            padding: '6px 12px',
            fontSize: '0.75rem',
            fontWeight: 600,
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            backgroundColor: mapMode === 'satellite' ? '#38bdf8' : 'transparent',
            color: mapMode === 'satellite' ? '#0f172a' : '#94a3b8'
          }}
        >
          Satelit NASA
        </button>
        <button
          onClick={() => setMapMode('dark')}
          style={{
            padding: '6px 12px',
            fontSize: '0.75rem',
            fontWeight: 600,
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            backgroundColor: mapMode === 'dark' ? '#38bdf8' : 'transparent',
            color: mapMode === 'dark' ? '#0f172a' : '#94a3b8'
          }}
        >
          Peta Gelap
        </button>
        <button
          onClick={() => setMapMode('light')}
          style={{
            padding: '6px 12px',
            fontSize: '0.75rem',
            fontWeight: 600,
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            backgroundColor: mapMode === 'light' ? '#38bdf8' : 'transparent',
            color: mapMode === 'light' ? '#0f172a' : '#94a3b8'
          }}
        >
          Peta Terang
        </button>
      </div>

      <DeckGL
        viewState={viewState}
        onViewStateChange={({viewState}) => {
          const minLng = 94.0, maxLng = 141.0;
          const minLat = -11.0, maxLat = 6.0;
          viewState.longitude = Math.max(minLng, Math.min(maxLng, viewState.longitude));
          viewState.latitude = Math.max(minLat, Math.min(maxLat, viewState.latitude));
          setViewState(viewState);
          if (onZoomChange) onZoomChange(viewState.zoom);
        }}
        controller={true}
        layers={layers}
        onHover={onHover}
        getTooltip={() => null}
      >
        <Map key={mapMode} mapStyle={currentStyle} />
      </DeckGL>

      {tooltip && obj && (
        <div ref={tooltipRef} className="custom-tooltip" style={getTooltipStyle()}>
          <div className="tt-type">{(obj.disaster_type || 'Banjir / Tanah Longsor').toUpperCase()}</div>
          <div className="tt-divider" />
          <div className="tt-row"><span className="tt-label">Desa</span><span className="tt-val">{obj.desa || 'Tidak Diketahui'}</span></div>
          <div className="tt-row"><span className="tt-label">Kerusakan</span><span className="tt-val">{obj.count} unit</span></div>
          <div className="tt-row"><span className="tt-label">Est. Terdampak</span><span className="tt-val">{obj.population || obj.count * 4} jiwa</span></div>
          {item ? (
            <>
              <div className="tt-divider" />
              <div className="tt-section">Logistik Presisi (Model DL .h5)</div>
              <div className="tt-row"><span className="tt-label">Beras</span><span className="tt-val">{formatDecimal(item.beras_kg)} kg</span></div>
              <div className="tt-row"><span className="tt-label">Minyak Goreng</span><span className="tt-val">{formatDecimal(item.minyak_liter)} L</span></div>
              <div className="tt-row"><span className="tt-label">Gula Pasir</span><span className="tt-val">{formatDecimal(item.gula_kg)} kg</span></div>
              <div className="tt-row"><span className="tt-label">Mie Instan</span><span className="tt-val">{formatDecimal(item.indomie_pcs)} pcs</span></div>
              <div className="tt-row"><span className="tt-label">Biskuit Roma</span><span className="tt-val">{formatDecimal(item.roma_sari_gandum_pack)} pack</span></div>
              <div className="tt-row"><span className="tt-label">Sarden / Kornet</span><span className="tt-val">{formatDecimal(item.sarden_pcs)} / {formatDecimal(item.kornet_pcs)} klg</span></div>
              <div className="tt-row"><span className="tt-label">Susu Cream/Dancow</span><span className="tt-val">{formatDecimal(item.susu_full_cream_pcs)} pcs / {formatDecimal(item.susu_dancow_box)} box</span></div>
              <div className="tt-row"><span className="tt-label">Matras / Kompor</span><span className="tt-val">{formatDecimal(item.matras_pcs)} pcs / {formatDecimal(item.kompor_set)} set</span></div>
              <div className="tt-row"><span className="tt-label">Kasur / Karpet</span><span className="tt-val">{formatDecimal(item.kasur_lipat_pcs)} / {formatDecimal(item.karpet_plastik_pcs)} pcs</span></div>
            </>
          ) : obj.logistics && (
            <>
              <div className="tt-divider" />
              <div className="tt-section">Kebutuhan Logistik</div>
              <div className="tt-row"><span className="tt-label">Beras</span><span className="tt-val">{formatDecimal(obj.logistics.beras)} kg</span></div>
              <div className="tt-row"><span className="tt-label">Air</span><span className="tt-val">{formatDecimal(obj.logistics.air)} L</span></div>
              <div className="tt-row"><span className="tt-label">Mie Instan</span><span className="tt-val">{formatDecimal(obj.logistics.mie)} dus</span></div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
