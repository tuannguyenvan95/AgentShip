import React from 'react';
import {
  X,
  Scale,
  Waves,
  Clock,
  ShieldCheck,
  ExternalLink,
  Hash,
  AlertTriangle,
  Zap,
} from 'lucide-react';
import { MaritimeVoyage } from '../types/voyage';
import {
  formatAddress,
  formatWei,
  getStatusBadge,
  getVerdictBadge,
} from '../utils/formatters';

interface AdmiraltyInspectorModalProps {
  voyage: MaritimeVoyage | null;
  isOpen: boolean;
  onClose: () => void;
}

export const AdmiraltyInspectorModal: React.FC<AdmiraltyInspectorModalProps> = ({
  voyage,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !voyage) return null;

  const statusInfo = getStatusBadge(voyage.status);
  const isForceMajeure = voyage.max_wave_height_meters >= 6;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/70 backdrop-blur-xs">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-5 bg-navy-900 text-white flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-ocean-500/20 text-ocean-300 flex items-center justify-center">
              <Scale className="w-6 h-6 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-space font-bold text-lg text-white">
                  High Admiralty Court Dossier
                </h3>
                <span className="text-xs px-2 py-0.5 rounded bg-navy-800 text-ocean-300 font-mono">
                  Voyage #{voyage.voyage_id}
                </span>
              </div>
              <p className="text-xs text-slate-300 font-mono">
                Vessel IMO: {voyage.vessel_imo_number}
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

        {/* Modal Scrollable Content */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {/* Status & Verdict Highlight */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                Tribunal Adjudication Status
              </span>
              <div className="flex items-center space-x-2">
                <span
                  className={`text-xs font-bold px-3 py-1 rounded-full border ${statusInfo.color}`}
                >
                  {statusInfo.label}
                </span>
                {voyage.is_fast_track && (
                  <span className="flex items-center space-x-1 text-xs font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">
                    <Zap className="w-3.5 h-3.5 text-amber-600 fill-amber-500" />
                    <span>Fast-Track 12H</span>
                  </span>
                )}
              </div>
            </div>

            <div className="text-right">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                Final Consensus Verdict
              </span>
              <span
                className={`text-xs font-extrabold px-3 py-1 rounded-lg border font-mono ${getVerdictBadge(
                  voyage.verdict
                )}`}
              >
                {voyage.verdict || 'PENDING'}
              </span>
            </div>
          </div>

          {/* AI Tribunal Rationale */}
          <div className="p-4 rounded-xl bg-ocean-50/50 border border-ocean-100 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-ocean-900 flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4 text-ocean-600" />
                <span>GenVM Subjective Jury Rationale</span>
              </span>
              {voyage.confidence > 0 && (
                <span className="text-xs font-mono font-bold text-ocean-700 bg-white px-2 py-0.5 rounded border border-ocean-200">
                  Consensus: {voyage.confidence}%
                </span>
              )}
            </div>
            <p className="text-sm text-slate-700 leading-relaxed font-sans italic bg-white p-3 rounded-lg border border-ocean-100/60">
              "{voyage.reason || 'Telemetry active. Awaiting maritime tribunal consensus.'}"
            </p>
          </div>

          {/* Weather & Delay Gauge Comparison */}
          <div className="grid grid-cols-2 gap-4">
            {/* Wave Height vs Force Majeure */}
            <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 flex items-center space-x-1.5">
                  <Waves className="w-4 h-4 text-blue-500" />
                  <span>Peak Oceanic Waves</span>
                </span>
                <span
                  className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                    isForceMajeure
                      ? 'bg-teal-100 text-teal-800'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {isForceMajeure ? 'FORCE MAJEURE (>= 6m)' : 'NORMAL STATE (< 6m)'}
                </span>
              </div>
              <div className="text-2xl font-extrabold font-space text-navy-900">
                {voyage.max_wave_height_meters}{' '}
                <span className="text-sm font-normal text-slate-500">meters</span>
              </div>
              {/* Progress bar visual */}
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div
                  className={`h-full ${
                    isForceMajeure ? 'bg-teal-500' : 'bg-blue-500'
                  }`}
                  style={{
                    width: `${Math.min(100, (voyage.max_wave_height_meters / 12) * 100)}%`,
                  }}
                ></div>
              </div>
            </div>

            {/* Delay beyond Laytime */}
            <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 flex items-center space-x-1.5">
                  <Clock className="w-4 h-4 text-amber-500" />
                  <span>Laytime vs Delay</span>
                </span>
                <span className="text-[11px] font-mono text-slate-400">
                  Allowed: {voyage.laytime_hours_allowed}h
                </span>
              </div>
              <div
                className={`text-2xl font-extrabold font-space ${
                  voyage.measured_delay_hours > 0 ? 'text-rose-600' : 'text-emerald-600'
                }`}
              >
                +{voyage.measured_delay_hours}{' '}
                <span className="text-sm font-normal text-slate-500">hours delay</span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div
                  className={`h-full ${
                    voyage.measured_delay_hours > 0 ? 'bg-rose-500' : 'bg-emerald-500'
                  }`}
                  style={{
                    width: `${Math.min(100, (voyage.measured_delay_hours / 72) * 100)}%`,
                  }}
                ></div>
              </div>
            </div>
          </div>

          {/* Cryptographic SHA-256 Digest */}
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1 mb-1">
              <Hash className="w-3.5 h-3.5" />
              <span>Immutable SHA-256 Telemetry Snapshot</span>
            </span>
            <div className="font-mono text-xs text-slate-800 break-all select-all bg-white p-2 rounded-lg border border-slate-200">
              {voyage.evidence_hash || 'Pending validation upon consensus trigger...'}
            </div>
          </div>

          {/* Telemetry Links */}
          <div className="space-y-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Multi-Source Telemetry Endpoints
            </span>
            <div className="space-y-1.5">
              {voyage.ais_tracking_url ? (
                <a
                  href={voyage.ais_tracking_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between p-2.5 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 text-xs font-mono text-ocean-700 transition-colors"
                >
                  <span className="truncate max-w-[450px]">
                    AIS Satellite: {voyage.ais_tracking_url}
                  </span>
                  <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                </a>
              ) : (
                <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-400 italic">
                  AIS endpoint not yet linked by Carrier.
                </div>
              )}

              {voyage.marine_weather_url ? (
                <a
                  href={voyage.marine_weather_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between p-2.5 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 text-xs font-mono text-ocean-700 transition-colors"
                >
                  <span className="truncate max-w-[450px]">
                    Marine Weather: {voyage.marine_weather_url}
                  </span>
                  <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                </a>
              ) : (
                <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-400 italic">
                  Marine weather endpoint not yet linked by Carrier.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end shrink-0">
          <button
            onClick={onClose}
            className="px-5 py-2 text-sm font-semibold text-slate-700 hover:text-navy-900 bg-white hover:bg-slate-100 border border-slate-300 rounded-xl transition-colors"
          >
            Close Dossier
          </button>
        </div>
      </div>
    </div>
  );
};
