import React, { useState } from 'react';
import { X, Navigation, CloudRain, ShieldCheck, Link2 } from 'lucide-react';
import { MaritimeVoyage } from '../types/voyage';

interface SubmitTelemetryModalProps {
  voyage: MaritimeVoyage | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (voyageId: number, aisUrl: string, weatherUrl: string) => void;
  isSubmitting: boolean;
}

export const SubmitTelemetryModal: React.FC<SubmitTelemetryModalProps> = ({
  voyage,
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
}) => {
  const [aisUrl, setAisUrl] = useState(
    'https://marinetraffic.org/ais/voyage_rotterdam_singapore.json'
  );
  const [weatherUrl, setWeatherUrl] = useState(
    'https://noaa-marine.org/data/typhoon_north_sea.txt'
  );

  if (!isOpen || !voyage) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!aisUrl.trim() || !weatherUrl.trim()) return;
    onSubmit(voyage.voyage_id, aisUrl.trim(), weatherUrl.trim());
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-5 bg-navy-900 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-teal-500/20 text-teal-300 flex items-center justify-center">
              <Navigation className="w-5 h-5 text-teal-400" />
            </div>
            <div>
              <h3 className="font-space font-bold text-lg text-white">
                Carrier Portal: Link Telemetry
              </h3>
              <p className="text-xs text-slate-300 font-mono">
                Vessel {voyage.vessel_imo_number} • Voyage #{voyage.voyage_id}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-start space-x-2">
            <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <span>
              By claiming this voyage, your address becomes the legal Carrier. Both AIS satellite position and NOAA oceanic telemetry will be validated on-chain via GenVM subjective consensus.
            </span>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
              Live AIS Tracking Endpoint
            </label>
            <div className="relative">
              <input
                type="url"
                required
                value={aisUrl}
                onChange={(e) => setAisUrl(e.target.value)}
                placeholder="https://marinetraffic.org/ais/vessel_live.json"
                className="w-full px-3.5 py-2.5 text-xs font-mono font-medium text-slate-900 placeholder:text-slate-400 border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-ocean-500 bg-white shadow-2xs"
              />
              <Link2 className="w-4 h-4 text-slate-500 absolute right-3 top-3" />
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">
              Public AIS stream reporting coordinates, knots, and port arrival timestamp.
            </span>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
              Marine Oceanic Weather Telemetry Endpoint
            </label>
            <div className="relative">
              <input
                type="url"
                required
                value={weatherUrl}
                onChange={(e) => setWeatherUrl(e.target.value)}
                placeholder="https://noaa-marine.org/data/ocean_sea_state.txt"
                className="w-full px-3.5 py-2.5 text-xs font-mono font-medium text-slate-900 placeholder:text-slate-400 border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-ocean-500 bg-white shadow-2xs"
              />
              <CloudRain className="w-4 h-4 text-slate-500 absolute right-3 top-3" />
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">
              NOAA / ECMWF oceanic sea state, wave height, and Beaufort gale scale.
            </span>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2.5 text-sm font-semibold text-white bg-navy-900 hover:bg-navy-950 rounded-xl shadow-sm transition-all disabled:opacity-50"
            >
              {isSubmitting ? 'Linking Telemetry on-chain...' : 'Claim & Link Telemetry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
