import React, { useState, useRef, useEffect, useCallback } from 'react';
import DeckGL from '@deck.gl/react';
import { FlyToInterpolator } from '@deck.gl/core';
import { Map } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';

const MAP_STYLES = {
  light: {
    version: 8,
    sources: {
      'basemap': {
        type: 'raster',
        tiles: ['https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png'],
        tileSize: 256,
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

export default function DeckMap({ flyToTarget, layers, theme = 'dark' }) {
  const mapStyle = MAP_STYLES[theme] || MAP_STYLES.dark;
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  const [tooltip, setTooltip] = useState(null);
  const tooltipRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (flyToTarget) {
      setViewState(prev => ({
        ...prev,
        longitude: flyToTarget.lon,
        latitude: flyToTarget.lat,
        zoom: 13.5,
        transitionDuration: 1500,
        transitionInterpolator: new FlyToInterpolator()
      }));
    }
  }, [flyToTarget]);

  const onHover = useCallback((info) => {
    if (info.object && info.object.count !== undefined) {
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

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%', height: '100%' }}>
      <DeckGL
        viewState={viewState}
        onViewStateChange={({viewState}) => {
          const minLng = 94.0, maxLng = 141.0;
          const minLat = -11.0, maxLat = 6.0;
          viewState.longitude = Math.max(minLng, Math.min(maxLng, viewState.longitude));
          viewState.latitude = Math.max(minLat, Math.min(maxLat, viewState.latitude));
          setViewState(viewState);
        }}
        controller={true}
        layers={layers}
        onHover={onHover}
        getTooltip={() => null}
      >
        <Map key={theme} mapStyle={mapStyle} />
      </DeckGL>

      {tooltip && obj && (
        <div ref={tooltipRef} className="custom-tooltip" style={getTooltipStyle()}>
          <div className="tt-type">{(obj.disaster_type || 'Banjir / Tanah Longsor').toUpperCase()}</div>
          <div className="tt-divider" />
          <div className="tt-row"><span className="tt-label">Desa</span><span className="tt-val">{obj.desa || 'Tidak Diketahui'}</span></div>
          <div className="tt-row"><span className="tt-label">Kerusakan</span><span className="tt-val">{obj.count} unit</span></div>
          <div className="tt-row"><span className="tt-label">Est. Terdampak</span><span className="tt-val">{obj.count * 4} jiwa</span></div>
          {obj.logistics && (
            <>
              <div className="tt-divider" />
              <div className="tt-section">Kebutuhan Logistik</div>
              <div className="tt-row"><span className="tt-label">Beras</span><span className="tt-val">{obj.logistics.beras} kg</span></div>
              <div className="tt-row"><span className="tt-label">Air</span><span className="tt-val">{obj.logistics.air} L</span></div>
              <div className="tt-row"><span className="tt-label">Mie Instan</span><span className="tt-val">{obj.logistics.mie} dus</span></div>
              <div className="tt-row"><span className="tt-label">Lauk Kaleng</span><span className="tt-val">{obj.logistics.lauk} pkt</span></div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
