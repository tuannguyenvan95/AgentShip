import React from 'react';
import {
  Anchor,
  ShieldCheck,
  Wallet,
  Trophy,
  PlusCircle,
  RefreshCw,
  LayoutGrid,
  Columns3,
  Moon,
  Sun,
  LogOut,
} from 'lucide-react';
import { formatAddress, formatWei } from '../utils/formatters';

interface NavbarProps {
  account: string | null;
  balance: string;
  chainId: number | null;
  layoutMode: 'cockpit' | 'grid';
  isDarkTheme: boolean;
  onToggleLayout: () => void;
  onToggleTheme: () => void;
  onConnect: () => void;
  onDisconnect: () => void;
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
  layoutMode,
  isDarkTheme,
  onToggleLayout,
  onToggleTheme,
  onConnect,
  onDisconnect,
  onSwitchNetwork,
  onOpenCreate,
  onOpenLeaderboard,
  onRefresh,
  isRefreshing,
}) => {
  const isCorrectChain = chainId === 61999;

  return (
    <header
      className={`sticky top-0 z-40 border-b backdrop-blur-md transition-colors ${
        isDarkTheme
          ? 'bg-slate-950/95 border-slate-800 text-slate-100 shadow-lg'
          : 'bg-white/95 border-slate-200 text-navy-900 shadow-sm'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-navy-900 to-ocean-700 flex items-center justify-center text-white shadow-md shadow-ocean-500/20">
            <Anchor className="w-6 h-6 text-sky-400 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl font-bold font-space tracking-tight">
                AgentShip
              </span>
              <span className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-md bg-ocean-500/20 text-ocean-400 border border-ocean-500/30">
                v3.0 Admiralty
              </span>
            </div>
            <p className="text-xs text-slate-400 font-sans hidden sm:block">
              Global Maritime Demurrage & Weather Risk Court • GenLayer StudioNet
            </p>
          </div>
        </div>

        {/* Layout & Theme & Actions & Wallet */}
        <div className="flex items-center space-x-2.5">
          {/* Mode Switcher: Cockpit vs Grid */}
          <div
            className={`flex items-center rounded-xl p-1 border ${
              isDarkTheme
                ? 'bg-slate-900 border-slate-800'
                : 'bg-slate-100 border-slate-200'
            }`}
          >
            <button
              onClick={onToggleLayout}
              className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-mono font-semibold rounded-lg transition-all ${
                layoutMode === 'cockpit'
                  ? 'bg-sky-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="3-Panel Oceanic Command Bridge"
            >
              <Columns3 className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Cockpit HUD</span>
            </button>
            <button
              onClick={onToggleLayout}
              className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-mono font-semibold rounded-lg transition-all ${
                layoutMode === 'grid'
                  ? 'bg-sky-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Fleet Grid Cards"
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Fleet Grid</span>
            </button>
          </div>

          {/* Theme Switcher: Dark vs Light */}
          <button
            onClick={onToggleTheme}
            className={`p-2 rounded-xl border transition-colors ${
              isDarkTheme
                ? 'bg-slate-900 border-slate-800 text-amber-400 hover:bg-slate-800'
                : 'bg-slate-100 border-slate-200 text-slate-700 hover:bg-slate-200'
            }`}
            title={isDarkTheme ? 'Switch to Light Cleanroom' : 'Switch to Dark Bridge'}
          >
            {isDarkTheme ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          {/* Leaderboard button */}
          <button
            onClick={onOpenLeaderboard}
            className={`hidden md:flex items-center space-x-1.5 px-3 py-2 text-xs font-medium rounded-xl border transition-colors ${
              isDarkTheme
                ? 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800'
                : 'bg-slate-100 border-slate-200 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <Trophy className="w-3.5 h-3.5 text-amber-400" />
            <span>Tiers</span>
          </button>

          {/* Refresh button */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className={`p-2 rounded-xl border transition-colors ${
              isDarkTheme
                ? 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                : 'bg-slate-100 border-slate-200 text-slate-600 hover:text-navy-900'
            }`}
            title="Refresh State"
          >
            <RefreshCw
              className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-sky-400' : ''}`}
            />
          </button>

          {/* Book Voyage Button */}
          <button
            onClick={onOpenCreate}
            className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-gradient-to-r from-sky-600 to-navy-900 hover:from-sky-500 hover:to-navy-800 rounded-xl shadow-sm transition-all"
          >
            <PlusCircle className="w-4 h-4 text-sky-300" />
            <span className="hidden sm:inline">Book Escrow</span>
            <span className="sm:hidden">Book</span>
          </button>

          {/* Wallet Connection */}
          {account ? (
            <div className="flex items-center space-x-2">
              {!isCorrectChain ? (
                <button
                  onClick={onSwitchNetwork}
                  className="px-2.5 py-1.5 text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30 rounded-xl hover:bg-rose-500/30 transition-colors"
                >
                  Switch Chain
                </button>
              ) : (
                <div className="hidden xl:flex items-center space-x-1 px-2.5 py-1 text-[11px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-xl">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping mr-1"></span>
                  <span>StudioNet</span>
                </div>
              )}

              <div
                className={`flex items-center space-x-2 pl-3 pr-2 py-1.5 rounded-xl border font-mono ${
                  isDarkTheme
                    ? 'bg-slate-900 border-slate-800'
                    : 'bg-slate-50 border-slate-200'
                }`}
              >
                <div className="text-right">
                  <div className="text-xs font-bold text-sky-400">
                    {formatWei(balance, 3)} GEN
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {formatAddress(account)}
                  </div>
                </div>
                <div className="w-7 h-7 rounded-full bg-navy-900 text-sky-300 flex items-center justify-center font-bold text-xs border border-sky-500/30">
                  {account.substring(2, 4).toUpperCase()}
                </div>
              </div>

              {/* Disconnect Button */}
              <button
                onClick={onDisconnect}
                title="Disconnect Wallet"
                className={`p-2 rounded-xl border transition-colors flex items-center justify-center ${
                  isDarkTheme
                    ? 'bg-slate-900/80 border-slate-800 text-slate-400 hover:text-rose-400 hover:border-rose-900/50'
                    : 'bg-white border-slate-200 text-slate-500 hover:text-rose-600 hover:border-rose-200'
                }`}
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={onConnect}
              className={`flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl border transition-colors ${
                isDarkTheme
                  ? 'bg-slate-900 border-slate-800 text-white hover:bg-slate-800'
                  : 'bg-white border-slate-300 text-navy-900 hover:bg-slate-50'
              }`}
            >
              <Wallet className="w-3.5 h-3.5 text-sky-400" />
              <span>Connect</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
