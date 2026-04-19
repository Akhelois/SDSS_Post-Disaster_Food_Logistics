import React from 'react';
import DeckGL from '@deck.gl/react';
import { Map } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import '../styles/DeckMap.css';

export default function DeckMap({ viewState, setViewState, layers }) {
  return (
    <DeckGL
      initialViewState={viewState}
      onViewStateChange={({viewState}) => setViewState(viewState)}
      controller={true}
      layers={layers}
      getTooltip={({object}) => {
        if (!object) return null;
        if (object.count !== undefined) {
          const type = object.disaster_type || 'Zona Kerusakan';
          return `${type}\nDesa: ${object.desa || 'Tidak Diketahui'}\nEstimasi Kerusakan: ${object.count} unit`;
        }
        return object.desa ? `Rute: ${object.desa}` : null;
      }}
    >
      <Map mapStyle={{
        version: 8,
        sources: {
          'satellite': {
            type: 'raster',
            tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
            tileSize: 256,
          }
        },
        layers: [
          {
            id: 'satellite-layer',
            type: 'raster',
            source: 'satellite',
            minzoom: 0,
            maxzoom: 19
          }
        ]
      }} />
    </DeckGL>
  );
}
