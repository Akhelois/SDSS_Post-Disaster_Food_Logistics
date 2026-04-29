import React, { useState } from 'react';
import DeckGL from '@deck.gl/react';
import { Map } from 'react-map-gl/maplibre';
import { LuMoon, LuSun } from 'react-icons/lu';
import 'maplibre-gl/dist/maplibre-gl.css';
import '../styles/DeckMap.css';

export default function DeckMap({ viewState, setViewState, layers }) {
  const [mapMode, setMapMode] = useState('light');

  const mapStyle = {
    version: 8,
    sources: {
      'basemap': {
        type: 'raster',
        tiles: [
          mapMode === 'dark'
            ? 'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'
            : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
        ],
        tileSize: 256,
      }
    },
    layers: [
      {
        id: 'basemap-layer',
        type: 'raster',
        source: 'basemap',
        minzoom: 0,
        maxzoom: 19
      }
    ]
  };

  return (
    <>
      <DeckGL
        viewState={viewState}
        onViewStateChange={({viewState}) => setViewState(viewState)}
        controller={true}
        layers={layers}
        getTooltip={({object}) => {
          if (!object) return null;
          if (object.count !== undefined) {
            const type = object.disaster_type || 'Bencana Alam';
            const desa = object.desa || 'Tidak Diketahui';
            let text = `${type.toUpperCase()}\n\nDesa: ${desa}\nKerusakan: ${object.count} unit\nEst. Terdampak: ${object.count * 4} jiwa`;
            if (object.logistics) {
              text += `\n\nKebutuhan Logistik`;
              text += `\nBeras: ${object.logistics.beras} kg`;
              text += `\nAir: ${object.logistics.air} L`;
              text += `\nMie: ${object.logistics.mie} dus`;
              text += `\nLauk: ${object.logistics.lauk} pkt`;
            }
            return text;
          }
          return null;
        }}
      >
        <Map mapStyle={mapStyle} />
      </DeckGL>

      <button 
        className="map-mode-toggle"
        onClick={() => setMapMode(prev => prev === 'light' ? 'dark' : 'light')}
        title="Toggle Map Mode"
      >
        {mapMode === 'light' ? <LuMoon size={18} /> : <LuSun size={18} />}
      </button>
    </>
  );
}
