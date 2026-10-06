import React from 'react';
import {
  Ship,
  Clock,
  Waves,
  ShieldCheck,
  Scale,
  ExternalLink,
  ChevronRight,
  AlertTriangle,
  Zap,
  Users,
  CheckCircle2,
  Lock,
} from 'lucide-react';
import { MaritimeVoyage } from '../types/voyage';
import {
  formatAddress,
  formatWei,
  getStatusBadge,
  getVerdictBadge,
} from '../utils/formatters';

interface VoyageCardProps {
  voyage: MaritimeVoyage;
  currentAccount: string | null;
  onOpenTelemetry: (voyage: MaritimeVoyage) => void;
  onOpenInspector: (voyage: MaritimeVoyage) => void;
  onOpenAppeal: (voyage: MaritimeVoyage) => void;
  onOpenSyndicate: (voyage: MaritimeVoyage) => void;
  onAdjudicate: (voyageId: number) => void;
  onFinalize: (voyageId: number) => void;
  onCancel: (voyageId: number) => void;
  isLoadingAction: boolean;
}

export const VoyageCard: React.FC<VoyageCardProps> = ({
  voyage,
  currentAccount,
  onOpenTelemetry,
  onOpenInspector,
  onOpenAppeal,
  onOpenSyndicate,
  onAdjudicate,
  onFinalize,
  onCancel,
  isLoadingAction,
}) => {
  const statusInfo = getStatusBadge(voyage.status);
  const totalLocked = (
    BigInt(voyage.freight_amount || "0") + BigInt(voyage.demurrage_deposit || "0")
  ).toString();

  const isCharterer =
    currentAccount && currentAccount.toLowerCase() === voyage.charterer.toLowerCase();
  const isCarrier =
    currentAccount && currentAccount.toLowerCase() === voyage.carrier.toLowerCase();

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm hover:shadow-md transition-all overflow-hidden flex flex-col">
      {/* Top Banner / Card Header */}
      <div className="p-5 border-b border-slate-100 bg-slate-50/50">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-11 h-11 rounded-xl bg-navy-900 text-white flex items-center justify-center font-bold text-lg shadow-sm">
              <Ship className="w-6 h-6 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-space font-bold text-lg text-navy-900 tracking-tight">
                  {voyage.vessel_imo_number}
                </span>
                <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                  #{voyage.voyage_id}
                </span>
                {voyage.is_fast_track && (
                  <span className="flex items-center space-x-1 text-[11px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">
                    <Zap className="w-3 h-3 text-amber-600 fill-amber-500" />
                    <span>Fast-Track 12H</span>
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-0.5 font-mono">
                Charterer: {formatAddress(voyage.charterer)}{' '}
                {voyage.carrier !== '0x0000000000000000000000000000000000000000' && (
                  <span>• Carrier: {formatAddress(voyage.carrier)}</span>
                )}
              </p>
              {currentAccount && (
                <div className="mt-1 flex items-center space-x-1.5">
                  {isCharterer && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-blue-100 text-blue-800 border border-blue-200">
                      YOUR ROLE: CHARTERER (Cargo Owner)
                    </span>
                  )}
                  {isCarrier && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 border border-emerald-200">
                      YOUR ROLE: CARRIER (Vessel Owner)
                    </span>
                  )}
                  {!isCharterer && !isCarrier && (
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200">
                      OBSERVER / SYNDICATE
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="text-right">
            <span
              className={`inline-block text-xs font-bold px-2.5 py-1 rounded-full border ${statusInfo.color}`}
            >
              {statusInfo.label}
            </span>
            <div className="text-[11px] text-slate-400 mt-1 font-mono">
              {statusInfo.desc}
            </div>
          </div>
        </div>
      </div>

      {/* Body: Financial Escrow & Maritime Gauges */}
      <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
        {/* Financial Escrow Breakdown */}
        <div className="grid grid-cols-3 gap-2 p-3 bg-slate-50/70 rounded-xl border border-slate-200/60 text-center">
          <div>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
              Base Freight
            </span>
            <span className="text-sm font-bold font-mono text-navy-900">
              {formatWei(voyage.freight_amount, 2)}
            </span>
            <span className="text-[10px] text-slate-500 ml-0.5">GEN</span>
          </div>
          <div className="border-x border-slate-200">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
              Demurrage Buffer
            </span>
            <span className="text-sm font-bold font-mono text-amber-700">
              {formatWei(voyage.demurrage_deposit, 2)}
            </span>
            <span className="text-[10px] text-slate-500 ml-0.5">GEN</span>
          </div>
          <div>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
              Total Escrow
            </span>
            <span className="text-sm font-bold font-mono text-ocean-700">
              {formatWei(totalLocked, 2)}
            </span>
            <span className="text-[10px] text-slate-500 ml-0.5">GEN</span>
          </div>
        </div>

        {/* Telemetry Metrics Bar */}
        <div className="grid grid-cols-3 gap-2">
          {/* Laytime Allowed */}
          <div className="p-2.5 rounded-xl border border-slate-200 bg-white">
            <div className="flex items-center space-x-1.5 text-slate-400 text-xs mb-1">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <span className="font-medium text-[11px]">Laytime Cap</span>
            </div>
            <div className="text-base font-bold font-space text-navy-900">
              {voyage.laytime_hours_allowed}{' '}
              <span className="text-xs font-normal text-slate-500">hours</span>
            </div>
          </div>

          {/* Measured Delay */}
          <div className="p-2.5 rounded-xl border border-slate-200 bg-white">
            <div className="flex items-center space-x-1.5 text-slate-400 text-xs mb-1">
              <AlertTriangle
                className={`w-3.5 h-3.5 ${
                  voyage.measured_delay_hours > 0 ? 'text-rose-500' : 'text-slate-400'
                }`}
              />
              <span className="font-medium text-[11px]">Delay Log</span>
            </div>
            <div
              className={`text-base font-bold font-space ${
                voyage.measured_delay_hours > 0 ? 'text-rose-600' : 'text-emerald-600'
              }`}
            >
              {voyage.measured_delay_hours}{' '}
              <span className="text-xs font-normal text-slate-500">hrs</span>
            </div>
          </div>

          {/* Ocean Wave Height */}
          <div className="p-2.5 rounded-xl border border-slate-200 bg-white">
            <div className="flex items-center space-x-1.5 text-slate-400 text-xs mb-1">
              <Waves
                className={`w-3.5 h-3.5 ${
                  voyage.max_wave_height_meters >= 6 ? 'text-teal-600' : 'text-blue-500'
                }`}
              />
              <span className="font-medium text-[11px]">Peak Wave</span>
            </div>
            <div
              className={`text-base font-bold font-space ${
                voyage.max_wave_height_meters >= 6 ? 'text-teal-600 font-extrabold' : 'text-navy-900'
              }`}
            >
              {voyage.max_wave_height_meters}{' '}
              <span className="text-xs font-normal text-slate-500">meters</span>
            </div>
          </div>
        </div>

        {/* AI Verdict / Reason snippet if adjudicated */}
        {voyage.verdict && voyage.verdict !== 'PENDING' && (
          <div
            className={`p-3 rounded-xl border text-xs ${getVerdictBadge(
              voyage.verdict
            )}`}
          >
            <div className="flex items-center justify-between font-bold mb-1">
              <span>Verdict: {voyage.verdict}</span>
              {voyage.confidence > 0 && (
                <span className="font-mono text-[10px]">
                  AI Confidence: {voyage.confidence}%
                </span>
              )}
            </div>
            <p className="line-clamp-2 text-slate-600 font-sans italic">
              "{voyage.reason}"
            </p>
          </div>
        )}

        {/* Evidence Hash Pill */}
        {voyage.evidence_hash && (
          <div className="flex items-center justify-between px-3 py-1.5 bg-slate-100/80 rounded-lg text-[11px] font-mono text-slate-600">
            <span className="text-slate-400">SHA-256 Digest:</span>
            <span className="text-slate-800 font-semibold truncate max-w-[200px]">
              {voyage.evidence_hash.substring(0, 16)}...
              {voyage.evidence_hash.substring(voyage.evidence_hash.length - 8)}
            </span>
          </div>
        )}
      </div>

      {/* Card Action Footer */}
      <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between gap-2">
        {/* Left: Inspector / Details Trigger */}
        <button
          onClick={() => onOpenInspector(voyage)}
          className="text-xs font-semibold text-ocean-700 hover:text-ocean-900 flex items-center space-x-1 py-1.5 px-2 hover:bg-ocean-50 rounded-lg transition-colors"
        >
          <span>Forensic Dossier</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>

        {/* Right: State-Specific Action Buttons */}
        <div className="flex items-center space-x-2">
          {voyage.status === 0 && (
            <>
              <button
                onClick={() => onOpenSyndicate(voyage)}
                className="px-2.5 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded-lg shadow-xs transition-colors flex items-center space-x-1"
                title="Co-Fund Cargo Escrow"
              >
                <Users className="w-3.5 h-3.5 text-ocean-600" />
                <span className="hidden sm:inline">Co-Fund ({voyage.co_funder_count})</span>
              </button>

              <button
                onClick={() => onOpenTelemetry(voyage)}
                disabled={Boolean(isCharterer)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center space-x-1 ${
                  isCharterer
                    ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    : 'text-white bg-navy-900 hover:bg-navy-950'
                }`}
                title={
                  isCharterer
                    ? 'Charterers cannot act as Carrier for their own booking'
                    : 'Carrier: Accept voyage & submit AIS telemetry'
                }
              >
                <Ship className="w-3.5 h-3.5" />
                <span>{isCharterer ? 'Carrier Only' : 'Claim & Link AIS'}</span>
              </button>
            </>
          )}

          {voyage.status === 1 && (
            <button
              onClick={() => onAdjudicate(voyage.voyage_id)}
              disabled={isLoadingAction}
              className="px-3.5 py-1.5 text-xs font-semibold text-white bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 rounded-lg shadow-sm transition-all flex items-center space-x-1"
              title="Stakeholders trigger AI subjective consensus"
            >
              <Scale className="w-3.5 h-3.5" />
              <span>Adjudicate (AI Jury)</span>
            </button>
          )}

          {voyage.status === 2 && (
            <>
              <button
                onClick={() => onOpenAppeal(voyage)}
                disabled={Boolean(!isCharterer && !isCarrier)}
                className={`px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  !isCharterer && !isCarrier
                    ? 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
                    : 'text-rose-700 bg-rose-50 border border-rose-200 hover:bg-rose-100'
                }`}
                title={
                  !isCharterer && !isCarrier
                    ? 'Only Charterer or Carrier can file an appeal'
                    : 'File appeal with 10% bond'
                }
              >
                Appeal (10% Bond)
              </button>

              <button
                onClick={() => onFinalize(voyage.voyage_id)}
                disabled={isLoadingAction || Boolean(!isCharterer && !isCarrier)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center space-x-1 ${
                  !isCharterer && !isCarrier
                    ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    : 'text-white bg-emerald-600 hover:bg-emerald-700'
                }`}
                title={
                  !isCharterer && !isCarrier
                    ? 'Only Charterer or Carrier can finalize settlement'
                    : 'Finalize payout after cooling-off period'
                }
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Finalize Payout</span>
              </button>
            </>
          )}

          {voyage.status === 6 && (
            <button
              onClick={() => onOpenInspector(voyage)}
              className="px-3 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-lg shadow-sm transition-colors animate-pulse"
            >
              Review Appellate Jury
            </button>
          )}

          {(voyage.status === 3 || voyage.status === 4 || voyage.status === 5) && (
            <div className="flex items-center space-x-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Settled</span>
            </div>
          )}

          {voyage.status === 7 && (
            <div className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md">
              Refunded
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
