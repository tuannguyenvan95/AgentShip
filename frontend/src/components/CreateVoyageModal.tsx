import React, { useState } from 'react';
import { X, Ship, Clock, Lock, Sparkles, AlertCircle } from 'lucide-react';

interface CreateVoyageModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    vesselImo: string;
    laytimeHours: number;
    freightGen: string;
    demurrageGen: string;
    durationBlocks: number;
  }) => void;
  isSubmitting: boolean;
}

export const CreateVoyageModal: React.FC<CreateVoyageModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
}) => {
  const [vesselImo, setVesselImo] = useState('IMO9811000');
  const [laytimeHours, setLaytimeHours] = useState(48);
  const [freightGen, setFreightGen] = useState('0.04');
  const [demurrageGen, setDemurrageGen] = useState('0.01');
  const [durationBlocks, setDurationBlocks] = useState(6000);

  if (!isOpen) return null;

  const totalGen = (parseFloat(freightGen || '0') + parseFloat(demurrageGen || '0')).toFixed(4);

  const applyTemplate = (imo: string, laytime: number, freight: string, demurrage: string) => {
    setVesselImo(imo);
    setLaytimeHours(laytime);
    setFreightGen(freight);
    setDemurrageGen(demurrage);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!vesselImo.trim()) return;
    onSubmit({
      vesselImo: vesselImo.trim(),
      laytimeHours,
      freightGen,
      demurrageGen,
      durationBlocks,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-xs">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-5 bg-navy-900 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-ocean-500/20 text-ocean-300 flex items-center justify-center">
              <Ship className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <h3 className="font-space font-bold text-lg text-white">
                Book Maritime Voyage Escrow
              </h3>
              <p className="text-xs text-slate-300">
                Lock Freight & Demurrage Buffer under Admiralty Law
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

        {/* Templates quick-pick */}
        <div className="px-6 pt-4 pb-2 bg-slate-50 border-b border-slate-100">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 flex items-center space-x-1 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            <span>Charter Templates</span>
          </span>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => applyTemplate('IMO9811000', 48, '0.04', '0.01')}
              className="px-2.5 py-1 text-xs font-medium rounded-lg bg-white border border-slate-200 hover:border-ocean-400 text-slate-700 hover:text-navy-900 transition-colors shadow-2xs"
            >
              Rotterdam - Singapore (Bulk 48h)
            </button>
            <button
              type="button"
              onClick={() => applyTemplate('IMO9732100', 36, '0.03', '0.01')}
              className="px-2.5 py-1 text-xs font-medium rounded-lg bg-white border border-slate-200 hover:border-ocean-400 text-slate-700 hover:text-navy-900 transition-colors shadow-2xs"
            >
              LA Long Beach (Container 36h)
            </button>
            <button
              type="button"
              onClick={() => applyTemplate('IMO9954321', 24, '0.05', '0.02')}
              className="px-2.5 py-1 text-xs font-medium rounded-lg bg-white border border-slate-200 hover:border-ocean-400 text-slate-700 hover:text-navy-900 transition-colors shadow-2xs"
            >
              Tokyo Bay Express (LNG 24h)
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
              Vessel IMO Number
            </label>
            <input
              type="text"
              required
              value={vesselImo}
              onChange={(e) => setVesselImo(e.target.value)}
              placeholder="e.g. IMO9811000"
              className="w-full px-3.5 py-2.5 text-sm font-mono font-medium text-slate-900 placeholder:text-slate-400 border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-ocean-500 bg-white shadow-2xs"
            />
            <span className="text-[11px] text-slate-500 mt-1 block">
              7-character unique International Maritime Organization registry.
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                Agreed Laytime (Hours)
              </label>
              <div className="relative">
                <input
                  type="number"
                  min={12}
                  max={720}
                  required
                  value={laytimeHours}
                  onChange={(e) => setLaytimeHours(parseInt(e.target.value) || 24)}
                  className="w-full px-3.5 py-2.5 text-sm font-mono font-medium text-slate-900 placeholder:text-slate-400 border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-ocean-500 bg-white shadow-2xs"
                />
                <Clock className="w-4 h-4 text-slate-500 absolute right-3 top-3" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                Duration (Blocks)
              </label>
              <input
                type="number"
                min={100}
                required
                value={durationBlocks}
                onChange={(e) => setDurationBlocks(parseInt(e.target.value) || 6000)}
                className="w-full px-3.5 py-2.5 text-sm font-mono font-medium text-slate-900 placeholder:text-slate-400 border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-ocean-500 bg-white shadow-2xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                Base Freight (GEN)
              </label>
              <input
                type="text"
                required
                value={freightGen}
                onChange={(e) => setFreightGen(e.target.value)}
                placeholder="0.04"
                className="w-full px-3.5 py-2.5 text-sm font-mono font-medium text-slate-900 placeholder:text-slate-400 border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-ocean-500 bg-white shadow-2xs"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                Demurrage Buffer (GEN)
              </label>
              <input
                type="text"
                required
                value={demurrageGen}
                onChange={(e) => setDemurrageGen(e.target.value)}
                placeholder="0.01"
                className="w-full px-3.5 py-2.5 text-sm font-mono font-medium text-slate-900 placeholder:text-slate-400 border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-ocean-500 bg-white shadow-2xs"
              />
            </div>
          </div>

          {/* Escrow summary */}
          <div className="p-3.5 bg-ocean-50/80 rounded-xl border border-ocean-100 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Lock className="w-4 h-4 text-ocean-600" />
              <span className="text-xs font-medium text-ocean-900">
                Total Native Escrow to Lock:
              </span>
            </div>
            <div className="text-right">
              <span className="font-space font-bold text-base text-ocean-900">
                {totalGen} GEN
              </span>
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
              {isSubmitting ? 'Locking Escrow on GenVM...' : 'Confirm & Lock Escrow'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
