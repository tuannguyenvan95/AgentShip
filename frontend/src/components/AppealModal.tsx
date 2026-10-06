import React, { useState } from 'react';
import { X, Scale, AlertTriangle, ShieldAlert } from 'lucide-react';
import { MaritimeVoyage } from '../types/voyage';
import { formatWei } from '../utils/formatters';

interface AppealModalProps {
  voyage: MaritimeVoyage | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (voyageId: number, disputeReason: string, bondWei: bigint) => void;
  isSubmitting: boolean;
}

export const AppealModal: React.FC<AppealModalProps> = ({
  voyage,
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
}) => {
  const [reason, setReason] = useState(
    'Harbor master officially closed port due to severe cyclonic swell.'
  );

  if (!isOpen || !voyage) return null;

  const totalEscrow =
    BigInt(voyage.freight_amount || '0') + BigInt(voyage.demurrage_deposit || '0');
  const bondWei = (totalEscrow * BigInt(10)) / BigInt(100);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (reason.trim().length < 10) return;
    onSubmit(voyage.voyage_id, reason.trim(), bondWei);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/70 backdrop-blur-xs">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-5 bg-rose-950 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-rose-500/20 text-rose-300 flex items-center justify-center">
              <Scale className="w-5 h-5 text-rose-400" />
            </div>
            <div>
              <h3 className="font-space font-bold text-lg text-white">
                File Admiralty Judicial Appeal
              </h3>
              <p className="text-xs text-rose-200 font-mono">
                Voyage #{voyage.voyage_id} • Vessel {voyage.vessel_imo_number}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-rose-300 hover:text-white p-1 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 space-y-1">
            <div className="flex items-center space-x-1.5 font-bold text-rose-900">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              <span>10% Anti-Griefing Dispute Bond Required</span>
            </div>
            <p>
              Under GenLayer Admiralty jurisprudence, filing an appeal requires locking a 10% staked bond ({formatWei(bondWei.toString(), 3)} GEN). If upheld, your bond is refunded 100%. If dismissed, your bond is slashed to the counterparty.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
              Appeal Justification & Legal Basis
            </label>
            <textarea
              required
              minLength={10}
              rows={4}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="State the verifiable maritime facts (e.g. harbor closure notices, cyclone reports, or incorrect laytime calculation)..."
              className="w-full px-3.5 py-2.5 text-xs font-sans font-medium text-slate-900 placeholder:text-slate-400 border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-rose-500 bg-white shadow-2xs"
            />
            <span className="text-[11px] text-slate-500 mt-1 block">
              Minimum 10 characters required. Will be evaluated by Supreme Appellate AI Jury.
            </span>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600">
              Required Staked Bond:
            </span>
            <span className="text-sm font-bold font-mono text-rose-600">
              {formatWei(bondWei.toString(), 4)} GEN
            </span>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-2">
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
              className="px-5 py-2.5 text-sm font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-xl shadow-sm transition-all disabled:opacity-50"
            >
              {isSubmitting ? 'Staking Bond & Escalating...' : 'Stake 10% & File Appeal'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
