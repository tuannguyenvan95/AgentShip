import React, { useState } from 'react';
import {
  Compass,
  Radio,
  Waves,
  Wind,
  Ship,
  AlertTriangle,
  Zap,
  Crosshair,
  Maximize2,
} from 'lucide-react';
import { MaritimeVoyage } from '../types/voyage';

interface MaritimeRadarHUDProps {
  voyages: MaritimeVoyage[];
  selectedVoyage: MaritimeVoyage | null;
  onSelectVoyage: (voyage: MaritimeVoyage) => void;
  isDarkTheme?: boolean;
}

export const MaritimeRadarHUD: React.FC<MaritimeRadarHUDProps> = ({
  voyages,
  selectedVoyage,
  onSelectVoyage,
  isDarkTheme = true,
}) => {
  const [radarZoom, setRadarZoom] = useState<'GLOBAL' | 'TRANSIT'>('GLOBAL');

  // Coordinates mapping for sample vessels on radar grid (0 to 100% relative coordinates)
  const vesselCoordinates: Record<string, { x: number; y: number; route: string; seaState: string }> = {
    IMO9811000: { x: 38, y: 35, route: 'Rotterdam -> Singapore', seaState: 'Typhoon Swell 8.2m' },
    IMO9732100: { x: 68, y: 58, route: 'LA -> Long Beach Feeder', seaState: 'Calm Waters 1.5m' },
    IMO9954321: { x: 75, y: 32, route: 'Tokyo Bay LNG Express', seaState: 'Moderate 2.8m' },
    IMO9991234: { x: 45, y: 65, route: 'Suez Canal Tanker', seaState: 'Rough Swell 4.2m' },
  };

  return (
    <div
      className={`rounded-2xl border p-5 relative overflow-hidden transition-all ${
        isDarkTheme
          ? 'bg-gradient-to-b from-slate-950 via-navy-950 to-slate-900 border-slate-800 text-slate-100 shadow-2xl'
          : 'bg-white border-slate-200 text-navy-900 shadow-sm'
      }`}
    >
      {/* HUD Header */}
      <div className="flex items-center justify-between mb-4 z-10 relative">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center border border-sky-500/30">
            <Radio className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <h3 className="font-space font-bold text-base tracking-wide flex items-center space-x-2">
              <span>OCEANIC FLEET RADAR & WEATHER HUD</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                LIVE AIS 12-SAT
              </span>
            </h3>
            <p className="text-[11px] text-slate-400 font-mono">
              Global Nautical Telemetry • Force Majeure Storm Track Detection (6m+ Threshold)
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setRadarZoom(radarZoom === 'GLOBAL' ? 'TRANSIT' : 'GLOBAL')}
            className={`px-2.5 py-1 text-xs font-mono rounded-lg border transition-colors ${
              isDarkTheme
                ? 'bg-slate-900 border-slate-700 text-slate-300 hover:text-white'
                : 'bg-slate-100 border-slate-200 text-slate-700 hover:text-navy-900'
            }`}
          >
            Range: {radarZoom === 'GLOBAL' ? 'Global 500nm' : 'Sector 100nm'}
          </button>
        </div>
      </div>

      {/* Radar Screen Visualizer */}
      <div className="relative w-full h-[320px] rounded-xl overflow-hidden border border-slate-800/80 bg-slate-950/90 flex items-center justify-center">
        {/* Radar Background Grid */}
        <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-40"></div>

        {/* Concentric Radar Rings */}
        <div className="absolute w-[280px] h-[280px] rounded-full border border-sky-500/15"></div>
        <div className="absolute w-[210px] h-[210px] rounded-full border border-sky-500/20"></div>
        <div className="absolute w-[140px] h-[140px] rounded-full border border-sky-500/25"></div>
        <div className="absolute w-[70px] h-[70px] rounded-full border border-sky-500/30"></div>

        {/* Crosshairs */}
        <div className="absolute w-full h-[1px] bg-sky-500/20"></div>
        <div className="absolute h-full w-[1px] bg-sky-500/20"></div>

        {/* Rotating Radar Sweep Line */}
        <div className="absolute w-full h-full flex items-center justify-center pointer-events-none">
          <div
            className="w-[280px] h-[280px] rounded-full origin-center animate-spin"
            style={{
              animationDuration: '6s',
              background:
                'conic-gradient(from 0deg, transparent 0deg, transparent 300deg, rgba(14, 165, 233, 0.25) 360deg)',
            }}
          ></div>
        </div>

        {/* Simulated Storm / Force Majeure Zone */}
        <div
          className="absolute rounded-full border border-teal-500/40 bg-teal-500/10 animate-pulse pointer-events-none flex items-center justify-center"
          style={{ width: '120px', height: '120px', left: '26%', top: '22%' }}
        >
          <span className="text-[9px] font-mono font-bold text-teal-400 bg-slate-950/80 px-1.5 py-0.5 rounded border border-teal-500/30">
            ⛈️ GALE 9 (8.2m)
          </span>
        </div>

        {/* Vessel Radar Blips */}
        {voyages.map((v, idx) => {
          const coords = vesselCoordinates[v.vessel_imo_number] || {
            x: 20 + (idx * 25) % 60,
            y: 30 + (idx * 20) % 50,
            route: 'Global Shipping Corridor',
            seaState: `${v.max_wave_height_meters || 1.5}m swell`,
          };
          const isSelected = selectedVoyage?.voyage_id === v.voyage_id;
          const isStormExcused = v.max_wave_height_meters >= 6;

          return (
            <button
              key={v.voyage_id}
              onClick={() => onSelectVoyage(v)}
              style={{ left: `${coords.x}%`, top: `${coords.y}%` }}
              className={`absolute -translate-x-1/2 -translate-y-1/2 group cursor-pointer z-20 flex flex-col items-center transition-all ${
                isSelected ? 'scale-125 z-30' : 'hover:scale-110'
              }`}
            >
              {/* Blip Ping Ring */}
              <div
                className={`w-4 h-4 rounded-full flex items-center justify-center relative ${
                  isStormExcused
                    ? 'bg-teal-500 text-white'
                    : v.status === 1
                    ? 'bg-amber-500 text-white animate-bounce'
                    : 'bg-sky-500 text-white'
                }`}
              >
                <div
                  className={`absolute inset-0 rounded-full animate-ping opacity-75 ${
                    isStormExcused ? 'bg-teal-400' : 'bg-sky-400'
                  }`}
                ></div>
                <Ship className="w-2.5 h-2.5 relative z-10" />
              </div>

              {/* Tag Label */}
              <div
                className={`mt-1 px-2 py-0.5 rounded text-[10px] font-mono whitespace-nowrap shadow-md transition-all ${
                  isSelected
                    ? 'bg-sky-500 text-white font-bold ring-2 ring-sky-300'
                    : 'bg-slate-900/90 text-slate-200 border border-slate-700'
                }`}
              >
                {v.vessel_imo_number}
                {v.is_fast_track && <span className="ml-1 text-amber-300">⚡</span>}
              </div>
            </button>
          );
        })}

        {/* Compass Cardinal Rose */}
        <div className="absolute top-2 left-3 font-mono text-[10px] text-sky-400/80 font-bold flex items-center space-x-1">
          <Compass className="w-3.5 h-3.5" />
          <span>HDG: 042° TRUE • SPEED: 16.4 KN</span>
        </div>

        <div className="absolute bottom-2 right-3 font-mono text-[10px] text-slate-500">
          BEAUFORT SCALE: FORCE 8-9 ALERT
        </div>
      </div>

      {/* Radar Bottom Ticker: Selected Vessel Quick Telemetry */}
      {selectedVoyage && (
        <div
          className={`mt-3 p-3 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono ${
            isDarkTheme
              ? 'bg-slate-900/80 border-slate-800 text-slate-200'
              : 'bg-slate-50 border-slate-200 text-slate-800'
          }`}
        >
          <div className="flex items-center space-x-3">
            <div className="w-2 h-2 rounded-full bg-sky-400 animate-ping"></div>
            <div>
              <span className="font-bold text-sky-400">
                LOCKED TARGET: {selectedVoyage.vessel_imo_number}
              </span>
              <span className="text-slate-400 ml-2">
                (Voyage #{selectedVoyage.voyage_id})
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4 text-[11px]">
            <div>
              <span className="text-slate-400">Laytime:</span>{' '}
              <span className="font-bold text-white">
                {selectedVoyage.laytime_hours_allowed}h
              </span>
            </div>
            <div>
              <span className="text-slate-400">Delay:</span>{' '}
              <span
                className={`font-bold ${
                  selectedVoyage.measured_delay_hours > 0 ? 'text-rose-400' : 'text-emerald-400'
                }`}
              >
                +{selectedVoyage.measured_delay_hours}h
              </span>
            </div>
            <div>
              <span className="text-slate-400">Waves:</span>{' '}
              <span
                className={`font-bold ${
                  selectedVoyage.max_wave_height_meters >= 6 ? 'text-teal-400' : 'text-sky-300'
                }`}
              >
                {selectedVoyage.max_wave_height_meters}m
              </span>
            </div>
            <div>
              <span className="text-slate-400">Verdict:</span>{' '}
              <span className="font-bold text-amber-300">
                {selectedVoyage.verdict || 'PENDING'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
