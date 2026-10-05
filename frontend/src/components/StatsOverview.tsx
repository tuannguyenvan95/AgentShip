import React from 'react';
import { Lock, Ship, Scale, CloudRain, Users } from 'lucide-react';
import { ContractStats } from '../types/voyage';
import { formatWei } from '../utils/formatters';

interface StatsOverviewProps {
  stats: ContractStats | null;
  activeCount: number;
}

export const StatsOverview: React.FC<StatsOverviewProps> = ({ stats, activeCount }) => {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {/* Total Locked */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Maritime Escrow Locked
          </span>
          <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Lock className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline space-x-1.5">
          <span className="text-2xl sm:text-3xl font-extrabold font-space text-navy-900">
            {formatWei(stats?.total_maritime_locked || '0', 2)}
          </span>
          <span className="text-sm font-semibold text-ocean-700">GEN</span>
        </div>
        <p className="text-xs text-slate-500 mt-1 font-mono">
          Freight & Demurrage Buffer
        </p>
      </div>

      {/* Voyages Tracked */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Voyages Logged
          </span>
          <div className="w-9 h-9 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
            <Ship className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl sm:text-3xl font-extrabold font-space text-navy-900">
            {stats?.total_voyages ?? 0}
          </span>
          <span className="text-xs font-medium text-emerald-600">
            ({stats?.total_voyages_settled ?? 0} Settled)
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Global AIS Fleet Telemetry
        </p>
      </div>

      {/* Active Tribunals */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Active Sea Tribunals
          </span>
          <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Scale className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline space-x-1.5">
          <span className="text-2xl sm:text-3xl font-extrabold font-space text-navy-900">
            {activeCount}
          </span>
          <span className="text-xs font-medium text-amber-600">In Transit</span>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Laytime & Weather Monitoring
        </p>
      </div>

      {/* Trust Registry */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Admiralty Trust Network
          </span>
          <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
            <Users className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline space-x-1.5">
          <span className="text-2xl sm:text-3xl font-extrabold font-space text-navy-900">
            {stats?.registered_participants ?? 0}
          </span>
          <span className="text-xs font-medium text-purple-600">Verified</span>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Fast-Track 12-Block Qualifying
        </p>
      </div>
    </div>
  );
};
