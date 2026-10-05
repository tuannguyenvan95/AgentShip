export interface MaritimeVoyage {
  voyage_id: number;
  charterer: string;
  carrier: string;
  dispute_initiator: string;
  freight_amount: string;
  demurrage_deposit: string;
  dispute_bond: string;
  vessel_imo_number: string;
  laytime_hours_allowed: number;
  ais_tracking_url: string;
  marine_weather_url: string;
  evidence_hash: string;
  status: number; // 0..7
  verdict: string;
  reason: string;
  confidence: number;
  measured_delay_hours: number;
  max_wave_height_meters: number;
  created_at_block: string;
  expires_at_block: string;
  audit_completed_block: string;
  is_fast_track: boolean;
  co_funder_count: number;
}

export interface ReputationDossier {
  address: string;
  reputation_score: number;
  tier: string;
  is_fast_track_eligible: boolean;
  cooling_off_blocks: number;
  completed_voyages: number;
  force_majeure_weather_verified: number;
  demurrage_faults: number;
  appeals_won: number;
  appeals_lost: number;
}

export interface LeaderboardEntry {
  address: string;
  score: number;
  tier: string;
  completed: number;
}

export interface SyndicatePledge {
  funder: string;
  amount: string;
  role: string;
}

export interface ContractStats {
  total_voyages: number;
  total_maritime_locked: string;
  total_voyages_settled: number;
  registered_participants: number;
  owner: string;
}
