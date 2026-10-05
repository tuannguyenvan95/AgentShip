export function formatWei(weiStr: string, decimals: number = 3): string {
  try {
    const wei = BigInt(weiStr || "0");
    const gen = Number(wei) / 1e18;
    return gen.toLocaleString(undefined, {
      minimumFractionDigits: 0,
      maximumFractionDigits: decimals,
    });
  } catch {
    return "0";
  }
}

export function formatAddress(addr: string): string {
  if (!addr || addr.length < 10) return addr || "0x000...000";
  return `${addr.substring(0, 6)}...${addr.substring(addr.length - 4)}`;
}

export function getStatusBadge(status: number) {
  switch (status) {
    case 0:
      return {
        label: "VOYAGE OPEN",
        color: "bg-blue-100 text-blue-800 border-blue-300",
        desc: "Awaiting Carrier Claim & Telemetry",
      };
    case 1:
      return {
        label: "IN TRANSIT",
        color: "bg-amber-100 text-amber-800 border-amber-300 animate-pulse",
        desc: "Vessel Navigating & Tracking Linked",
      };
    case 2:
      return {
        label: "AWAITING PAYOUT",
        color: "bg-purple-100 text-purple-800 border-purple-300",
        desc: "Consensus Rendered (Cooling-off Open)",
      };
    case 3:
      return {
        label: "CLEAN ON-TIME",
        color: "bg-emerald-100 text-emerald-800 border-emerald-300",
        desc: "Settled 100% to Carrier",
      };
    case 4:
      return {
        label: "DEMURRAGE ENFORCED",
        color: "bg-rose-100 text-rose-800 border-rose-300",
        desc: "Delay Penalty Slashed to Carrier",
      };
    case 5:
      return {
        label: "FORCE MAJEURE",
        color: "bg-teal-100 text-teal-800 border-teal-300",
        desc: "Storm Excused, Buffer Refunded",
      };
    case 6:
      return {
        label: "DISPUTED",
        color: "bg-red-100 text-red-800 border-red-300 animate-bounce",
        desc: "Appellate Admiralty Court Active",
      };
    case 7:
      return {
        label: "CANCELLED",
        color: "bg-slate-100 text-slate-800 border-slate-300",
        desc: "Escrow Reclaimed by Charterer",
      };
    default:
      return {
        label: "UNKNOWN",
        color: "bg-gray-100 text-gray-800 border-gray-300",
        desc: "Undefined state",
      };
  }
}

export function getVerdictBadge(verdict: string) {
  switch (verdict) {
    case "CLEAN_ON_TIME":
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    case "FORCE_MAJEURE_EXCUSED":
      return "bg-teal-50 text-teal-700 border-teal-200";
    case "DEMURRAGE_ENFORCED":
      return "bg-rose-50 text-rose-700 border-rose-200";
    case "DISPUTED":
      return "bg-amber-50 text-amber-700 border-amber-200";
    default:
      return "bg-slate-50 text-slate-700 border-slate-200";
  }
}

export function getTierBadge(tier: string) {
  switch (tier) {
    case "PLATINUM_ADMIRALTY_MASTER":
      return {
        label: "Platinum Master",
        badgeClass: "bg-purple-100 text-purple-900 border-purple-400 font-bold",
        icon: "👑",
      };
    case "GOLD_ESTABLISHED":
      return {
        label: "Gold Established",
        badgeClass: "bg-amber-100 text-amber-900 border-amber-400 font-semibold",
        icon: "⭐",
      };
    case "SILVER_VERIFIED":
      return {
        label: "Silver Verified",
        badgeClass: "bg-slate-200 text-slate-800 border-slate-400",
        icon: "🛡️",
      };
    default:
      return {
        label: "Bronze Newcomer",
        badgeClass: "bg-amber-50 text-amber-800 border-amber-200",
        icon: "⚓",
      };
  }
}
