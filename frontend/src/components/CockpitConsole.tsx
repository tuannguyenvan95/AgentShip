import React from 'react';
import {
  Ship,
  Compass,
  Scale,
  Clock,
  Waves,
  AlertTriangle,
  Zap,
  Users,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  Hash,
} from 'lucide-react';
import { MaritimeRadarHUD } from './MaritimeRadarHUD';
import {
  MaritimeVoyage,
  LeaderboardEntry,
  ReputationDossier,
} from '../types/voyage';
import {
  formatAddress,
  formatWei,
  getStatusBadge,
  getVerdictBadge,
  getTierBadge,
} from '../utils/formatters';

interface CockpitConsoleProps {
  voyages: MaritimeVoyage[];
  selectedVoyage: MaritimeVoyage | null;
  onSelectVoyage: (v: MaritimeVoyage) => void;
  currentAccount: string | null;
  leaderboard: LeaderboardEntry[];
  userProfile: ReputationDossier | null;
  onOpenTelemetry: (voyage: MaritimeVoyage) => void;
  onOpenInspector: (voyage: MaritimeVoyage) => void;
  onOpenAppeal: (voyage: MaritimeVoyage) => void;
  onOpenSyndicate: (voyage: MaritimeVoyage) => void;
  onAdjudicate: (voyageId: number) => void;
  onFinalize: (voyageId: number) => void;
  isLoadingAction: boolean;
  isDarkTheme?: boolean;
}

export const CockpitConsole: React.FC<CockpitConsoleProps> = ({
  voyages,
  selectedVoyage,
  onSelectVoyage,
  currentAccount,
  leaderboard,
  userProfile,
  onOpenTelemetry,
  onOpenInspector,
  onOpenAppeal,
  onOpenSyndicate,
  onAdjudicate,
  onFinalize,
  isLoadingAction,
  isDarkTheme = true,
}) => {
  const activeVoyage = selectedVoyage || voyages[0] || null;
  const statusInfo = activeVoyage ? getStatusBadge(activeVoyage.status) : null;
  const isForceMajeure = activeVoyage && activeVoyage.max_wave_height_meters >= 6;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* ── PANEL 1 (LEFT, 3 cols): FLEET ROSTER & AIS PIPELINE ── */}
      <div className="lg:col-span-3 space-y-3">
        <div className="flex items-center justify-between px-1">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center space-x-1.5">
            <Ship className="w-3.5 h-3.5 text-sky-400" />
            <span>FLEET PIPELINE ({voyages.length})</span>
          </span>
          <span className="text-[10px] font-mono text-emerald-400">● LIVE</span>
        </div>

        <div className="space-y-2 max-h-[750px] overflow-y-auto pr-1">
          {voyages.map((v) => {
            const isSelected = activeVoyage?.voyage_id === v.voyage_id;
            const badge = getStatusBadge(v.status);
            return (
              <button
                key={v.voyage_id}
                onClick={() => onSelectVoyage(v)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                  isSelected
                    ? isDarkTheme
                      ? 'bg-slate-900 border-sky-500 shadow-md ring-1 ring-sky-500/50'
                      : 'bg-white border-sky-500 shadow-md ring-1 ring-sky-500/50'
                    : isDarkTheme
                    ? 'bg-slate-950/70 hover:bg-slate-900 border-slate-800 text-slate-300'
                    : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="font-space font-bold text-sm tracking-tight text-white flex items-center space-x-1.5">
                    <span className={isDarkTheme ? 'text-white' : 'text-navy-900'}>
                      {v.vessel_imo_number}
                    </span>
                    {v.is_fast_track && (
                      <span className="text-[10px] text-amber-400 font-bold">⚡12H</span>
                    )}
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badge.color}`}
                  >
                    {badge.label}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mt-2">
                  <span>Voyage #{v.voyage_id}</span>
                  <span className={isDarkTheme ? 'text-slate-200' : 'text-navy-900'}>
                    {formatWei(v.freight_amount, 2)} GEN
                  </span>
                </div>

                {v.measured_delay_hours > 0 && (
                  <div className="mt-2 text-[10px] font-mono text-rose-400 flex items-center space-x-1">
                    <AlertTriangle className="w-3 h-3" />
                    <span>Delay: +{v.measured_delay_hours}h beyond laytime</span>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── PANEL 2 (CENTER, 6 cols): RADAR HUD + ACTIVE COMMAND CONSOLE ── */}
      <div className="lg:col-span-6 space-y-5">
        {/* Radar Map */}
        <MaritimeRadarHUD
          voyages={voyages}
          selectedVoyage={activeVoyage}
          onSelectVoyage={onSelectVoyage}
          isDarkTheme={isDarkTheme}
        />

        {/* Selected Vessel Operational Bridge */}
        {activeVoyage ? (
          <div
            className={`rounded-2xl border p-5 space-y-4 ${
              isDarkTheme
                ? 'bg-slate-950/80 border-slate-800 text-slate-100'
                : 'bg-white border-slate-200 text-navy-900'
            }`}
          >
            {/* Bridge Header */}
            <div className="flex items-start justify-between pb-3 border-b border-slate-800/80">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-space font-extrabold text-xl text-sky-400">
                    {activeVoyage.vessel_imo_number}
                  </span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    VOYAGE #{activeVoyage.voyage_id}
                  </span>
                  {activeVoyage.is_fast_track && (
                    <span className="flex items-center space-x-1 text-xs font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      <Zap className="w-3 h-3 fill-amber-300" />
                      <span>FAST-TRACK 12H ACTIVE</span>
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 font-mono mt-1">
                  Charterer: {formatAddress(activeVoyage.charterer)} • Carrier:{' '}
                  {formatAddress(activeVoyage.carrier)}
                </p>
              </div>

              <div className="text-right">
                <span
                  className={`text-xs font-bold px-3 py-1 rounded-full border ${statusInfo?.color}`}
                >
                  {statusInfo?.label}
                </span>
              </div>
            </div>

            {/* Escrow Financial HUD */}
            <div className="grid grid-cols-3 gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-center font-mono text-xs">
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Base Freight
                </span>
                <span className="text-sm font-bold text-sky-400">
                  {formatWei(activeVoyage.freight_amount, 2)}
                </span>{' '}
                GEN
              </div>
              <div className="border-x border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Demurrage Buffer
                </span>
                <span className="text-sm font-bold text-amber-400">
                  {formatWei(activeVoyage.demurrage_deposit, 2)}
                </span>{' '}
                GEN
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Total Locked
                </span>
                <span className="text-sm font-bold text-emerald-400">
                  {formatWei(
                    (
                      BigInt(activeVoyage.freight_amount || '0') +
                      BigInt(activeVoyage.demurrage_deposit || '0')
                    ).toString(),
                    2
                  )}
                </span>{' '}
                GEN
              </div>
            </div>

            {/* Wave & Sea State Gauges */}
            <div className="grid grid-cols-2 gap-3 font-mono">
              <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span className="flex items-center space-x-1">
                    <Waves className="w-3.5 h-3.5 text-blue-400" />
                    <span>Peak Waves</span>
                  </span>
                  <span
                    className={`font-bold ${
                      isForceMajeure ? 'text-teal-400' : 'text-slate-300'
                    }`}
                  >
                    {isForceMajeure ? 'FORCE MAJEURE (>=6m)' : 'NORMAL'}
                  </span>
                </div>
                <div className="text-xl font-bold font-space text-white">
                  {activeVoyage.max_wave_height_meters} meters
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span className="flex items-center space-x-1">
                    <Clock className="w-3.5 h-3.5 text-amber-400" />
                    <span>Laytime Breach</span>
                  </span>
                  <span className="text-slate-400">Cap: {activeVoyage.laytime_hours_allowed}h</span>
                </div>
                <div
                  className={`text-xl font-bold font-space ${
                    activeVoyage.measured_delay_hours > 0 ? 'text-rose-400' : 'text-emerald-400'
                  }`}
                >
                  +{activeVoyage.measured_delay_hours} hrs delay
                </div>
              </div>
            </div>

            {/* Command Trigger Actions */}
            <div className="pt-2 flex flex-wrap items-center justify-end gap-2.5">
              <button
                onClick={() => onOpenInspector(activeVoyage)}
                className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
              >
                Forensic Dossier
              </button>

              {activeVoyage.status === 0 && (
                <>
                  <button
                    onClick={() => onOpenSyndicate(activeVoyage)}
                    className="px-3 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors flex items-center space-x-1.5"
                  >
                    <Users className="w-3.5 h-3.5 text-sky-400" />
                    <span>Co-Fund Syndicate</span>
                  </button>

                  <button
                    onClick={() => onOpenTelemetry(activeVoyage)}
                    className="px-4 py-2 text-xs font-semibold rounded-xl bg-sky-600 hover:bg-sky-500 text-white shadow-sm transition-colors flex items-center space-x-1.5"
                  >
                    <Ship className="w-3.5 h-3.5" />
                    <span>Carrier: Link AIS Telemetry</span>
                  </button>
                </>
              )}

              {activeVoyage.status === 1 && (
                <button
                  onClick={() => onAdjudicate(activeVoyage.voyage_id)}
                  disabled={isLoadingAction}
                  className="px-4 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white shadow-md transition-all flex items-center space-x-1.5"
                >
                  <Scale className="w-4 h-4" />
                  <span>Adjudicate Demurrage (AI Jury)</span>
                </button>
              )}

              {activeVoyage.status === 2 && (
                <>
                  <button
                    onClick={() => onOpenAppeal(activeVoyage)}
                    className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-800 transition-colors"
                  >
                    File Appeal (10% Bond)
                  </button>

                  <button
                    onClick={() => onFinalize(activeVoyage.voyage_id)}
                    disabled={isLoadingAction}
                    className="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white shadow-md transition-colors flex items-center space-x-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Finalize Settlement Payout</span>
                  </button>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-slate-400 font-mono text-xs">
            No vessel selected. Select a vessel from the fleet roster.
          </div>
        )}
      </div>

      {/* ── PANEL 3 (RIGHT, 3 cols): JURY VERDICT & TRUST LEADERBOARD ── */}
      <div className="lg:col-span-3 space-y-4">
        {/* AI Maritime Court Card */}
        <div
          className={`rounded-2xl border p-4 space-y-3 ${
            isDarkTheme
              ? 'bg-slate-950/80 border-slate-800 text-slate-200'
              : 'bg-white border-slate-200 text-navy-900'
          }`}
        >
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center space-x-1.5">
              <Scale className="w-3.5 h-3.5 text-purple-400" />
              <span>AI ADMIRALTY JURY</span>
            </span>
            {activeVoyage?.confidence ? (
              <span className="text-[10px] font-mono text-sky-400 font-bold">
                {activeVoyage.confidence}% Conf.
              </span>
            ) : null}
          </div>

          <div
            className={`p-3 rounded-xl border text-xs font-mono ${getVerdictBadge(
              activeVoyage?.verdict || 'PENDING'
            )}`}
          >
            <div className="font-bold text-sm mb-1">
              {activeVoyage?.verdict || 'PENDING CONFLICT'}
            </div>
            <p className="line-clamp-3 text-[11px] opacity-90 italic">
              "{activeVoyage?.reason || 'Awaiting AIS & Weather Telemetry Analysis'}"
            </p>
          </div>

          {activeVoyage?.evidence_hash && (
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-[10px] font-mono text-slate-400 break-all select-all">
              <span className="text-slate-500 block">SHA-256 Digest:</span>
              {activeVoyage.evidence_hash}
            </div>
          )}
        </div>

        {/* Milestone v3 Trust Leaderboard Preview */}
        <div
          className={`rounded-2xl border p-4 space-y-3 ${
            isDarkTheme
              ? 'bg-slate-950/80 border-slate-800 text-slate-200'
              : 'bg-white border-slate-200 text-navy-900'
          }`}
        >
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center space-x-1.5">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>TRUST TIERS (12H FAST-TRACK)</span>
            </span>
          </div>

          {/* User's own status */}
          {userProfile && (
            <div className="p-2.5 rounded-xl bg-slate-900/80 border border-amber-500/30 text-xs font-mono">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Your Tier:</span>
                <span className="font-bold text-amber-300">
                  {getTierBadge(userProfile.tier).label} ({userProfile.reputation_score} pts)
                </span>
              </div>
              <div className="text-[10px] text-slate-400 mt-1">
                Cooling-off:{' '}
                <span className="text-emerald-400 font-bold">
                  {userProfile.cooling_off_blocks} Blocks{' '}
                  {userProfile.is_fast_track_eligible ? '(Fast-Track)' : '(Standard)'}
                </span>
              </div>
            </div>
          )}

          {/* Top 3 Leaderboard list */}
          <div className="space-y-1.5 max-h-48 overflow-y-auto font-mono text-xs">
            {leaderboard.slice(0, 4).map((entry, idx) => (
              <div
                key={entry.address}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-900/40 border border-slate-800/80 text-[11px]"
              >
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-slate-500">#{idx + 1}</span>
                  <span className="text-slate-300">{formatAddress(entry.address)}</span>
                </div>
                <div className="font-bold text-amber-400">{entry.score} pts</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
