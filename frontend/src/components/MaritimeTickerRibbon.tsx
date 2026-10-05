import React from 'react';
import { Waves, Wind, Compass, Radio, ShieldCheck, Zap } from 'lucide-react';

export const MaritimeTickerRibbon: React.FC = () => {
  const tickerItems = [
    { label: "GENLAYER STUDIONET", value: "CHAIN 61999 (0xF22F) • ACTIVE", icon: Radio, color: "text-emerald-400" },
    { label: "NORTH SEA GALE", value: "BEAUFORT 9 • SWELL 8.2M • FORCE MAJEURE ACTIVE", icon: Wind, color: "text-teal-400" },
    { label: "STRAIT OF MALACCA", value: "CALM SEA • SWELL 1.2M • NORMAL LAYTIME", icon: Waves, color: "text-sky-400" },
    { label: "PACIFIC FEEDER", value: "TYPHOON WARNING ALERT • WAVES 7.5M", icon: Compass, color: "text-amber-400" },
    { label: "AI ADMIRALTY TRIBUNAL", value: "GENVM SUBJECTIVE CONSENSUS • ZERO ADMIN", icon: ShieldCheck, color: "text-purple-400" },
    { label: "MILESTONE V3", value: "DYNAMIC FAST-TRACK 12H • SYNDICATE ESCROWS", icon: Zap, color: "text-amber-400" },
  ];

  return (
    <div className="bg-slate-950 text-slate-300 border-b border-slate-800 text-xs py-2 overflow-hidden select-none">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between">
        <div className="flex items-center space-x-2 shrink-0 pr-4 border-r border-slate-800">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          <span className="font-mono font-bold text-slate-100 text-[11px] tracking-wider uppercase">
            LIVE TELEMETRY
          </span>
        </div>

        <div className="overflow-x-auto no-scrollbar flex items-center space-x-6 pl-4 text-[11px] font-mono whitespace-nowrap">
          {tickerItems.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="flex items-center space-x-2">
                <Icon className={`w-3.5 h-3.5 ${item.color}`} />
                <span className="text-slate-400 font-medium">{item.label}:</span>
                <span className={`font-semibold ${item.color}`}>{item.value}</span>
                {idx < tickerItems.length - 1 && (
                  <span className="text-slate-700 ml-4">•</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
