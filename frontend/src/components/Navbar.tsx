import React from 'react';
import { Anchor, ShieldCheck, Wallet, Trophy, PlusCircle, RefreshCw } from 'lucide-react';
import { formatAddress, formatWei } from '../utils/formatters';

interface NavbarProps {
  account: string | null;
  balance: string;
  chainId: number | null;
  onConnect: () => void;
  onSwitchNetwork: () => void;
  onOpenCreate: () => void;
  onOpenLeaderboard: () => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  account,
  balance,
  chainId,
  onConnect,
  onSwitchNetwork,
  onOpenCreate,
  onOpenLeaderboard,
  onRefresh,
  isRefreshing,
}) => {
  const isCorrectChain = chainId === 61999;

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-navy-900 to-ocean-700 flex items-center justify-center text-white shadow-md shadow-ocean-500/20">
            <Anchor className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl font-bold font-space tracking-tight text-navy-900">
                AgentShip
              </span>
              <span className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-md bg-ocean-100 text-ocean-700 border border-ocean-200">
                v3.0 Admiralty
              </span>
            </div>
            <p className="text-xs text-slate-500 font-sans hidden sm:block">
              Global Maritime Demurrage & Weather Risk Court • GenLayer StudioNet
            </p>
          </div>
        </div>

        {/* Actions & Wallet */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onOpenLeaderboard}
            className="hidden md:flex items-center space-x-1.5 px-3.5 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors border border-slate-200"
          >
            <Trophy className="w-4 h-4 text-amber-500" />
            <span>Leaderboard</span>
          </button>

          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 text-slate-600 hover:text-navy-900 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-ocean-500' : ''}`} />
          </button>

          <button
            onClick={onOpenCreate}
            className="flex items-center space-x-1.5 px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-ocean-700 to-navy-900 hover:from-ocean-800 hover:to-navy-950 rounded-lg shadow-sm hover:shadow transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span className="hidden sm:inline">Book Voyage Escrow</span>
            <span className="sm:hidden">Book</span>
          </button>

          {/* Network & Account */}
          {account ? (
            <div className="flex items-center space-x-2">
              {!isCorrectChain ? (
                <button
                  onClick={onSwitchNetwork}
                  className="px-3 py-1.5 text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-300 rounded-lg hover:bg-rose-100 transition-colors"
                >
                  Switch to StudioNet
                </button>
              ) : (
                <div className="hidden lg:flex items-center space-x-1 px-2.5 py-1 text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping mr-1"></span>
                  <span>StudioNet (61999)</span>
                </div>
              )}

              <div className="flex items-center space-x-2 pl-3 pr-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg">
                <div className="text-right">
                  <div className="text-xs font-mono font-semibold text-navy-900">
                    {formatWei(balance, 3)} GEN
                  </div>
                  <div className="text-[10px] font-mono text-slate-500">
                    {formatAddress(account)}
                  </div>
                </div>
                <div className="w-8 h-8 rounded-full bg-navy-900 text-white flex items-center justify-center font-bold text-xs">
                  {account.substring(2, 4).toUpperCase()}
                </div>
              </div>
            </div>
          ) : (
            <button
              onClick={onConnect}
              className="flex items-center space-x-2 px-4 py-2 text-sm font-semibold text-navy-900 bg-white border border-slate-300 hover:border-slate-400 rounded-lg shadow-sm hover:bg-slate-50 transition-colors"
            >
              <Wallet className="w-4 h-4 text-ocean-700" />
              <span>Connect Wallet</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
