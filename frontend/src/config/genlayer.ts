export const STUDIONET_CHAIN_ID_DEC = 61999;
export const STUDIONET_CHAIN_ID_HEX = "0xF22F";
export const STUDIONET_RPC_URL = "https://studio.genlayer.com/api";
export const STUDIONET_EXPLORER_URL = "https://studio.genlayer.com";

export const DEFAULT_CONTRACT_ADDRESS = "0x133f95019925c8fAC02BE0bD1b86F947AA50F13F";

export const STUDIONET_CHAIN_CONFIG = {
  chainId: STUDIONET_CHAIN_ID_HEX,
  chainName: "GenLayer StudioNet",
  nativeCurrency: {
    name: "GEN",
    symbol: "GEN",
    decimals: 18,
  },
  rpcUrls: [STUDIONET_RPC_URL],
  blockExplorerUrls: [STUDIONET_EXPLORER_URL],
};

export const CONTRACT_ABI = [
  {
    name: "create_voyage_escrow",
    type: "function",
    inputs: [
      { name: "vessel_imo", type: "string" },
      { name: "laytime_hours", type: "int" },
      { name: "demurrage_buffer_wei", type: "bigint" },
      { name: "duration_blocks", type: "int" },
    ],
    outputs: [{ name: "voyage_id", type: "u64" }],
  },
  {
    name: "pledge_voyage_escrow",
    type: "function",
    inputs: [{ name: "voyage_id", type: "u64" }],
    outputs: [],
  },
  {
    name: "submit_voyage_logs",
    type: "function",
    inputs: [
      { name: "voyage_id", type: "u64" },
      { name: "ais_tracking_url", type: "string" },
      { name: "marine_weather_url", type: "string" },
    ],
    outputs: [],
  },
  {
    name: "adjudicate_demurrage",
    type: "function",
    inputs: [{ name: "voyage_id", type: "u64" }],
    outputs: [],
  },
  {
    name: "appeal_verdict",
    type: "function",
    inputs: [
      { name: "voyage_id", type: "u64" },
      { name: "dispute_reason", type: "string" },
    ],
    outputs: [],
  },
  {
    name: "adjudicate_appeal",
    type: "function",
    inputs: [
      { name: "voyage_id", type: "u64" },
      { name: "supplemental_log_url", type: "string" },
    ],
    outputs: [],
  },
  {
    name: "finalize_settlement",
    type: "function",
    inputs: [{ name: "voyage_id", type: "u64" }],
    outputs: [],
  },
  {
    name: "cancel_or_reclaim",
    type: "function",
    inputs: [{ name: "voyage_id", type: "u64" }],
    outputs: [],
  },
  {
    name: "get_voyage",
    type: "function",
    inputs: [{ name: "voyage_id", type: "u64" }],
    outputs: [{ name: "data", type: "string" }],
  },
  {
    name: "get_voyage_count",
    type: "function",
    inputs: [],
    outputs: [{ name: "count", type: "int" }],
  },
  {
    name: "get_all_voyages",
    type: "function",
    inputs: [],
    outputs: [{ name: "voyages", type: "string" }],
  },
  {
    name: "get_stats",
    type: "function",
    inputs: [],
    outputs: [{ name: "stats", type: "string" }],
  },
  {
    name: "get_reputation_profile",
    type: "function",
    inputs: [{ name: "user_address", type: "Address" }],
    outputs: [{ name: "profile", type: "string" }],
  },
  {
    name: "get_maritime_leaderboard",
    type: "function",
    inputs: [],
    outputs: [{ name: "leaderboard", type: "string" }],
  },
  {
    name: "get_voyage_pledges",
    type: "function",
    inputs: [{ name: "voyage_id", type: "u64" }],
    outputs: [{ name: "pledges", type: "string" }],
  },
];
