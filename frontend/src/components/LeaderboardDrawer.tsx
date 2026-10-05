import React from 'react';
import { X, Trophy, Zap, ShieldCheck, Award, Ship } from 'lucide-react';
import { LeaderboardEntry, ReputationDossier } from '../types/voyage';
import { formatAddress, getTierBadge } from '../utils/formatters';

interface LeaderboardDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  leaderboard: LeaderboardEntry[];
  userProfile: ReputationDossier | null;
}

export const LeaderboardDrawer: React.FC<LeaderboardDrawerProps> = ({
  isOpen,
  onClose,
  leaderboard,
  userProfile,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-navy-950/60 backdrop-blur-xs">
      <div className="bg-white w-full max-w-md h-full shadow-2xl flex flex-col border-l border-slate-200 animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="px-6 py-5 bg-navy-900 text-white flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-amber-500/20 text-amber-300 flex items-center justify-center">
              <Trophy className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h3 className="font-space font-bold text-lg text-white">
                Admiralty Trust Registry
              </h3>
              <p className="text-xs text-slate-300">
                Milestone v3 Fast-Track Tier Leaderboard
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

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* User's own trust dossier */}
          {userProfile && (
            <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-900 to-navy-900 text-white shadow-md space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Your Admiralty Dossier
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-white font-mono">
                  {formatAddress(userProfile.address)}
                </span>
              </div>

              <div className="flex items-baseline justify-between">
                <div>
                  <div className="text-3xl font-extrabold font-space text-amber-400">
                    {userProfile.reputation_score}{' '}
                    <span className="text-xs font-normal text-slate-300">points</span>
                  </div>
                  <div className="text-xs text-slate-300 mt-0.5">
                    Tier: {getTierBadge(userProfile.tier).label}
                  </div>
                </div>

                {userProfile.is_fast_track_eligible ? (
                  <div className="text-right">
                    <span className="inline-flex items-center space-x-1 text-xs font-bold px-2 py-1 rounded bg-amber-400/20 text-amber-300 border border-amber-400/40">
                      <Zap className="w-3.5 h-3.5 fill-amber-300" />
                      <span>12H Fast-Track</span>
                    </span>
                    <div className="text-[10px] text-slate-400 mt-1 font-mono">
                      Window: 12 Blocks
                    </div>
                  </div>
                ) : (
                  <div className="text-right">
                    <span className="text-xs font-semibold px-2 py-1 rounded bg-slate-800 text-slate-300">
                      Standard (24H)
                    </span>
                    <div className="text-[10px] text-slate-400 mt-1 font-mono">
                      Need 50 pts for Gold
                    </div>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/10 text-center text-xs">
                <div>
                  <span className="text-[10px] text-slate-400 block">Settled</span>
                  <span className="font-bold font-mono">{userProfile.completed_voyages}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block">Appeals Won</span>
                  <span className="font-bold font-mono text-emerald-400">
                    {userProfile.appeals_won}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block">Faults</span>
                  <span className="font-bold font-mono text-rose-400">
                    {userProfile.demurrage_faults}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Leaderboard Table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Global Ranked Maritime Operators
              </h4>
              <span className="text-xs text-slate-400 font-mono">
                Top {leaderboard.length}
              </span>
            </div>

            <div className="space-y-2">
              {leaderboard.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-xs italic bg-slate-50 rounded-xl border border-slate-200">
                  No verified voyages settled yet. Complete voyages to establish ranking!
                </div>
              ) : (
                leaderboard.map((item, index) => {
                  const tierInfo = getTierBadge(item.tier);
                  return (
                    <div
                      key={item.address}
                      className="flex items-center justify-between p-3 bg-white hover:bg-slate-50 rounded-xl border border-slate-200 transition-colors shadow-2xs"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-6 text-center font-bold font-space text-slate-400 text-sm">
                          {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}
                        </div>
                        <div>
                          <div className="font-mono font-semibold text-xs text-navy-900">
                            {formatAddress(item.address)}
                          </div>
                          <div className="text-[10px] text-slate-500 flex items-center space-x-1 mt-0.5">
                            <span>{tierInfo.icon}</span>
                            <span>{tierInfo.label}</span>
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="font-space font-extrabold text-sm text-navy-900">
                          {item.score}{' '}
                          <span className="text-[10px] font-normal text-slate-500">pts</span>
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {item.completed} voyages
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
