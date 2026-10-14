import React, { useState } from 'react';
import { X, Gavel, Scale, FileText, AlertCircle, ShieldCheck } from 'lucide-react';
import { MaritimeVoyage } from '../types/voyage';
import { formatWei } from '../utils/formatters';

interface AdjudicateAppealModalProps {
  voyage: MaritimeVoyage | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (voyageId: string | number, supplementalLogUrl: string) => void;
  isSubmitting: boolean;
}

export const AdjudicateAppealModal: React.FC<AdjudicateAppealModalProps> = ({
  voyage,
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
}) => {
  const [supplementalUrl, setSupplementalUrl] = useState(
    'https://raw.githubusercontent.com/tuannguyenvan95/AgentShip/main/telemetry/sample_supplemental_evidence.txt'
  );

  if (!isOpen || !voyage) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!supplementalUrl.trim().startsWith('http')) return;
    onSubmit(voyage.voyage_id, supplementalUrl.trim());
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/70 backdrop-blur-xs">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-5 bg-purple-950 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-purple-500/20 text-purple-300 flex items-center justify-center">
              <Gavel className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h3 className="font-space font-bold text-lg text-white">
                Adjudicate Admiralty Appeal
              </h3>
              <p className="text-xs text-purple-200 font-mono">
                Voyage #{voyage.voyage_id} • Vessel IMO {voyage.vessel_imo_number}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-purple-300 hover:text-white p-1 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-3.5 bg-purple-50 border border-purple-200 rounded-xl text-xs text-purple-900 space-y-1.5">
            <div className="flex items-center space-x-1.5 font-bold text-purple-950">
              <Scale className="w-4 h-4 text-purple-600" />
              <span>Appellate Court Jurisdiction & Payout Safeguards</span>
            </div>
            <p className="text-slate-600 leading-relaxed">
              The GenVM consensus validator jury evaluates supplemental harbor telemetry against vessel IMO <strong>{voyage.vessel_imo_number}</strong>.
            </p>
            <ul className="list-disc pl-4 space-y-0.5 text-slate-600">
              <li><strong>If Upheld:</strong> Appeal bond is refunded 100% to appellant, verdict updated.</li>
              <li><strong>If Dismissed:</strong> Original verdict ({voyage.original_verdict || voyage.verdict}) is preserved and executed; the 10% dispute bond ({formatWei(voyage.dispute_bond, 3)} GEN) is forfeited to counterparty.</li>
            </ul>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700">
              Supplemental Maritime Telemetry URL (Must be bound to IMO {voyage.vessel_imo_number})
            </label>
            <div className="relative">
              <FileText className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
              <input
                type="url"
                required
                value={supplementalUrl}
                onChange={(e) => setSupplementalUrl(e.target.value)}
                placeholder="https://port-authority.org/certified_logs.txt"
                className="w-full pl-9 pr-3 py-2 text-xs font-mono bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/30 focus:border-purple-600 transition-all text-slate-900"
              />
            </div>
            <p className="text-[11px] text-slate-500 flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5 text-purple-600 inline" />
              <span>Evidence without matching vessel IMO {voyage.vessel_imo_number} will be dismissed.</span>
            </p>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
            <div className="flex justify-between text-slate-600">
              <span>Appellate Dispute Bond:</span>
              <span className="font-mono font-bold text-purple-700">{formatWei(voyage.dispute_bond, 3)} GEN</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Original Disputed Verdict:</span>
              <span className="font-mono font-bold text-slate-900">{voyage.original_verdict || voyage.verdict}</span>
            </div>
          </div>

          <div className="flex items-center space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 py-2.5 px-4 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 py-2.5 px-4 text-xs font-bold text-white bg-purple-700 hover:bg-purple-800 disabled:bg-purple-400 rounded-xl transition-colors shadow-sm flex items-center justify-center space-x-1.5"
            >
              {isSubmitting ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Jury Adjudicating...</span>
                </>
              ) : (
                <>
                  <Gavel className="w-3.5 h-3.5" />
                  <span>Adjudicate Appeal</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
