import React, { useState } from 'react';
import { X, Users, DollarSign, ShieldCheck } from 'lucide-react';
import { MaritimeVoyage, SyndicatePledge } from '../types/voyage';
import { formatAddress, formatWei } from '../utils/formatters';

interface SyndicateModalProps {
  voyage: MaritimeVoyage | null;
  pledges: SyndicatePledge[];
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (voyageId: number, pledgeGen: string) => void;
  isSubmitting: boolean;
}

export const SyndicateModal: React.FC<SyndicateModalProps> = ({
  voyage,
  pledges,
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
}) => {
  const [pledgeGen, setPledgeGen] = useState('0.01');

  if (!isOpen || !voyage) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (parseFloat(pledgeGen || '0') <= 0) return;
    onSubmit(voyage.voyage_id, pledgeGen);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/70 backdrop-blur-xs">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-5 bg-navy-900 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-ocean-500/20 text-ocean-300 flex items-center justify-center">
              <Users className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <h3 className="font-space font-bold text-lg text-white">
                Cargo Syndicate Co-Funding Pool
              </h3>
              <p className="text-xs text-slate-300 font-mono">
                Voyage #{voyage.voyage_id} • Vessel {voyage.vessel_imo_number}
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
          <div className="p-3 bg-ocean-50 border border-ocean-200 rounded-xl text-xs text-ocean-900">
            <div className="font-semibold mb-0.5">Milestone v3 Proportional Solvency</div>
            Co-shippers pool freight into container escrows. In case of cancellation or demurrage waiver, refunds are distributed proportionally across all contributors without rounding loss.
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Co-Funding Contribution (GEN)
            </label>
            <div className="relative">
              <input
                type="text"
                required
                value={pledgeGen}
                onChange={(e) => setPledgeGen(e.target.value)}
                placeholder="0.01"
                className="w-full px-3.5 py-2.5 text-sm font-mono border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-ocean-500 bg-slate-50/50"
              />
              <span className="text-xs font-bold text-slate-400 absolute right-3 top-3">
                GEN
              </span>
            </div>
          </div>

          {/* Current Pledges List */}
          <div className="space-y-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
              Active Syndicate Co-Funders ({pledges.length})
            </span>
            <div className="max-h-36 overflow-y-auto space-y-1.5 p-2 bg-slate-50 rounded-xl border border-slate-200">
              {pledges.length === 0 ? (
                <div className="text-xs text-slate-400 text-center py-2 italic">
                  Primary charterer is sole funder.
                </div>
              ) : (
                pledges.map((p, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 bg-white rounded-lg border border-slate-200/60 text-xs"
                  >
                    <div className="font-mono text-slate-700">
                      {formatAddress(p.funder)}
                      <span className="text-[10px] ml-1.5 px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
                        {p.role}
                      </span>
                    </div>
                    <div className="font-mono font-bold text-navy-900">
                      {formatWei(p.amount, 3)} GEN
                    </div>
                  </div>
                ))
              )}
            </div>
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
              className="px-5 py-2.5 text-sm font-semibold text-white bg-navy-900 hover:bg-navy-950 rounded-xl shadow-sm transition-all disabled:opacity-50"
            >
              {isSubmitting ? 'Pooling GEN into Escrow...' : 'Pool Escrow Share'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
