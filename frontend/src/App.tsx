import React, { useState, useEffect, useCallback } from 'react';
import {
  Anchor,
  Filter,
  Search,
  AlertCircle,
  CheckCircle2,
  Ship,
  Sparkles,
  Layers,
  ChevronDown,
  Info,
} from 'lucide-react';
import { Navbar } from './components/Navbar';
import { StatsOverview } from './components/StatsOverview';
import { VoyageCard } from './components/VoyageCard';
import { CreateVoyageModal } from './components/CreateVoyageModal';
import { SubmitTelemetryModal } from './components/SubmitTelemetryModal';
import { AdmiraltyInspectorModal } from './components/AdmiraltyInspectorModal';
import { AppealModal } from './components/AppealModal';
import { SyndicateModal } from './components/SyndicateModal';
import { LeaderboardDrawer } from './components/LeaderboardDrawer';
import { CockpitConsole } from './components/CockpitConsole';
import { MaritimeTickerRibbon } from './components/MaritimeTickerRibbon';
import {
  MaritimeVoyage,
  ContractStats,
  ReputationDossier,
  LeaderboardEntry,
  SyndicatePledge,
} from './types/voyage';
import {
  DEFAULT_CONTRACT_ADDRESS,
  STUDIONET_CHAIN_ID_DEC,
  STUDIONET_CHAIN_ID_HEX,
  STUDIONET_CHAIN_CONFIG,
  STUDIONET_RPC_URL,
} from './config/genlayer';

export const App: React.FC = () => {
  // Web3 state
  const [account, setAccount] = useState<string | null>(null);
  const [balance, setBalance] = useState<string>('0');
  const [chainId, setChainId] = useState<number | null>(null);

  // Layout & Theme state
  const [layoutMode, setLayoutMode] = useState<'cockpit' | 'grid'>('cockpit');
  const [isDarkTheme, setIsDarkTheme] = useState<boolean>(true);
  const [selectedVoyage, setSelectedVoyage] = useState<MaritimeVoyage | null>(null);

  // Contract data
  const [stats, setStats] = useState<ContractStats | null>(null);
  const [voyages, setVoyages] = useState<MaritimeVoyage[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [userProfile, setUserProfile] = useState<ReputationDossier | null>(null);
  const [selectedPledges, setSelectedPledges] = useState<SyndicatePledge[]>([]);

  // UI state
  const [activeFilter, setActiveFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isLoadingAction, setIsLoadingAction] = useState<boolean>(false);
  const [notification, setNotification] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);

  // Active modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isTelemetryOpen, setIsTelemetryOpen] = useState(false);
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [isAppealOpen, setIsAppealOpen] = useState(false);
  const [isSyndicateOpen, setIsSyndicateOpen] = useState(false);
  const [isLeaderboardOpen, setIsLeaderboardOpen] = useState(false);
  const [activeVoyage, setActiveVoyage] = useState<MaritimeVoyage | null>(null);

  // RPC Contract Read helper
  const callContractView = async (functionName: string, args: any[] = []): Promise<any> => {
    try {
      const response = await fetch(STUDIONET_RPC_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: Date.now(),
          method: 'gen_call',
          params: [
            {
              to: DEFAULT_CONTRACT_ADDRESS,
              data: {
                function_name: functionName,
                args: args,
              },
            },
            'latest',
          ],
        }),
      });
      const data = await response.json();
      if (data?.result) {
        if (typeof data.result === 'string') {
          try {
            return JSON.parse(data.result);
          } catch {
            return data.result;
          }
        }
        return data.result;
      }
      return null;
    } catch (err) {
      console.warn(`Error calling view ${functionName}:`, err);
      return null;
    }
  };

  // Fetch all on-chain data
  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      // 1. Fetch Stats
      const statsData = await callContractView('get_stats', []);
      if (statsData) {
        setStats(statsData);
      }

      // 2. Fetch All Voyages
      const voyagesData = await callContractView('get_all_voyages', []);
      if (Array.isArray(voyagesData)) {
        setVoyages(voyagesData);
        setSelectedVoyage((prev) =>
          prev
            ? (voyagesData.find((v) => v.voyage_id === prev.voyage_id) ?? voyagesData[0])
            : voyagesData[0]
        );
      }

      // 3. Fetch Leaderboard
      const boardData = await callContractView('get_maritime_leaderboard', []);
      if (Array.isArray(boardData)) {
        setLeaderboard(boardData);
      }

      // 4. Fetch User Profile if connected
      if (account) {
        const profileData = await callContractView('get_reputation_profile', [account]);
        if (profileData) {
          setUserProfile(profileData);
        }
      }
    } catch (err) {
      console.error('Failed to load contract state:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, [account]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Wallet Connection
  const connectWallet = async () => {
    if (typeof window !== 'undefined' && (window as any).ethereum) {
      try {
        const ethereum = (window as any).ethereum;
        const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
        if (accounts.length > 0) {
          setAccount(accounts[0]);
          const chainHex = await ethereum.request({ method: 'eth_chainId' });
          setChainId(parseInt(chainHex, 16));

          // Fetch Balance
          const balHex = await ethereum.request({
            method: 'eth_getBalance',
            params: [accounts[0], 'latest'],
          });
          setBalance(BigInt(balHex).toString());
        }
      } catch (err: any) {
        setNotification({ type: 'error', message: err.message || 'Failed to connect wallet.' });
      }
    } else {
      setNotification({
        type: 'error',
        message: 'MetaMask or Web3 wallet extension not detected.',
      });
    }
  };

  const disconnectWallet = () => {
    setAccount(null);
    setBalance('0');
    setUserProfile(null);
    setNotification({
      type: 'info',
      message: 'Wallet disconnected from AgentShip session.',
    });
  };

  const switchNetwork = async () => {
    if (typeof window !== 'undefined' && (window as any).ethereum) {
      try {
        const ethereum = (window as any).ethereum;
        await ethereum.request({
          method: 'wallet_switchEthereumChain',
          params: [{ chainId: STUDIONET_CHAIN_ID_HEX }],
        });
      } catch (switchError: any) {
        if (switchError.code === 4902) {
          try {
            const ethereum = (window as any).ethereum;
            await ethereum.request({
              method: 'wallet_addEthereumChain',
              params: [STUDIONET_CHAIN_CONFIG],
            });
          } catch (addError) {
            console.error('Failed to add chain:', addError);
          }
        }
      }
    }
  };

  // Transaction execution helper
  const sendContractTransaction = async (
    functionName: string,
    args: any[],
    valueWei: bigint = BigInt(0)
  ) => {
    if (!account) {
      connectWallet();
      return;
    }
    setIsLoadingAction(true);
    setNotification({ type: 'info', message: `Submitting ${functionName} to GenVM...` });

    try {
      const ethereum = (window as any).ethereum;
      // Send transaction with GenLayer encoded data
      const txParams = {
        from: account,
        to: DEFAULT_CONTRACT_ADDRESS,
        value: '0x' + valueWei.toString(16),
        data: {
          function_name: functionName,
          args: args,
        },
      };

      const txHash = await ethereum.request({
        method: 'eth_sendTransaction',
        params: [txParams],
      });

      setNotification({
        type: 'success',
        message: `Transaction confirmed on StudioNet: ${txHash.substring(0, 10)}...`,
      });
      setTimeout(fetchData, 2000);
    } catch (err: any) {
      console.error(err);
      setNotification({
        type: 'error',
        message: err.message || `Transaction for ${functionName} failed.`,
      });
    } finally {
      setIsLoadingAction(false);
    }
  };

  // Action handlers
  const handleCreateVoyage = async (data: {
    vesselImo: string;
    laytimeHours: number;
    freightGen: string;
    demurrageGen: string;
    durationBlocks: number;
  }) => {
    const freightWei = BigInt(Math.floor(parseFloat(data.freightGen) * 1e18));
    const demurrageWei = BigInt(Math.floor(parseFloat(data.demurrageGen) * 1e18));
    const totalWei = freightWei + demurrageWei;

    await sendContractTransaction(
      'create_voyage_escrow',
      [data.vesselImo, data.laytimeHours, demurrageWei.toString(), data.durationBlocks],
      totalWei
    );
    setIsCreateOpen(false);
  };

  const handleSubmitTelemetry = async (
    voyageId: number,
    aisUrl: string,
    weatherUrl: string
  ) => {
    await sendContractTransaction('submit_voyage_logs', [voyageId, aisUrl, weatherUrl], BigInt(0));
    setIsTelemetryOpen(false);
  };

  const handleAdjudicateDemurrage = async (voyageId: number) => {
    await sendContractTransaction('adjudicate_demurrage', [voyageId], BigInt(0));
  };

  const handleFileAppeal = async (
    voyageId: number,
    disputeReason: string,
    bondWei: bigint
  ) => {
    await sendContractTransaction('appeal_verdict', [voyageId, disputeReason], bondWei);
    setIsAppealOpen(false);
  };

  const handleFinalizeSettlement = async (voyageId: number) => {
    await sendContractTransaction('finalize_settlement', [voyageId], BigInt(0));
  };

  const handleCancelOrReclaim = async (voyageId: number) => {
    await sendContractTransaction('cancel_or_reclaim', [voyageId], BigInt(0));
  };

  const handlePledgeSyndicate = async (voyageId: number, pledgeGen: string) => {
    const pledgeWei = BigInt(Math.floor(parseFloat(pledgeGen) * 1e18));
    await sendContractTransaction('pledge_voyage_escrow', [voyageId], pledgeWei);
    setIsSyndicateOpen(false);
  };

  // Open modals
  const openTelemetryModal = (v: MaritimeVoyage) => {
    setActiveVoyage(v);
    setIsTelemetryOpen(true);
  };

  const openInspectorModal = (v: MaritimeVoyage) => {
    setActiveVoyage(v);
    setIsInspectorOpen(true);
  };

  const openAppealModal = (v: MaritimeVoyage) => {
    setActiveVoyage(v);
    setIsAppealOpen(true);
  };

  const openSyndicateModal = async (v: MaritimeVoyage) => {
    setActiveVoyage(v);
    const pledges = await callContractView('get_voyage_pledges', [v.voyage_id]);
    setSelectedPledges(Array.isArray(pledges) ? pledges : []);
    setIsSyndicateOpen(true);
  };

  // Filter & Search logic
  const filteredVoyages = voyages.filter((v) => {
    const matchesSearch =
      v.vessel_imo_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.charterer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.carrier.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (activeFilter === 'ALL') return true;
    if (activeFilter === 'OPEN') return v.status === 0;
    if (activeFilter === 'TRANSIT') return v.status === 1;
    if (activeFilter === 'PAYOUT') return v.status === 2;
    if (activeFilter === 'DISPUTED') return v.status === 6;
    if (activeFilter === 'SETTLED') return [3, 4, 5].includes(v.status);
    return true;
  });

  const activeInTransitCount = voyages.filter((v) => v.status === 1).length;

  return (
    <div
      className={`min-h-screen font-sans antialiased selection:bg-ocean-500 selection:text-white transition-colors duration-200 ${
        isDarkTheme ? 'bg-slate-950 text-slate-100' : 'bg-slate-100/70 text-slate-900'
      }`}
    >
      {/* Navigation */}
      <Navbar
        account={account}
        balance={balance}
        chainId={chainId}
        layoutMode={layoutMode}
        isDarkTheme={isDarkTheme}
        onToggleLayout={() => setLayoutMode((m) => (m === 'cockpit' ? 'grid' : 'cockpit'))}
        onToggleTheme={() => setIsDarkTheme((t) => !t)}
        onConnect={connectWallet}
        onDisconnect={disconnectWallet}
        onSwitchNetwork={switchNetwork}
        onOpenCreate={() => setIsCreateOpen(true)}
        onOpenLeaderboard={() => setIsLeaderboardOpen(true)}
        onRefresh={fetchData}
        isRefreshing={isRefreshing}
      />

      {/* Live Oceanic Telemetry Ribbon */}
      <MaritimeTickerRibbon />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Banner Notification */}
        {notification && (
          <div
            className={`mb-6 p-4 rounded-2xl border flex items-center justify-between text-xs sm:text-sm animate-in fade-in slide-in-from-top-2 duration-200 ${
              notification.type === 'success'
                ? isDarkTheme
                  ? 'bg-emerald-950/60 border-emerald-800 text-emerald-200'
                  : 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : notification.type === 'error'
                ? isDarkTheme
                  ? 'bg-rose-950/60 border-rose-800 text-rose-200'
                  : 'bg-rose-50 border-rose-200 text-rose-800'
                : isDarkTheme
                ? 'bg-sky-950/60 border-sky-800 text-sky-200'
                : 'bg-blue-50 border-blue-200 text-blue-800'
            }`}
          >
            <div className="flex items-center space-x-2">
              {notification.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
              ) : notification.type === 'error' ? (
                <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
              ) : (
                <Info className="w-5 h-5 text-sky-500 shrink-0" />
              )}
              <span>{notification.message}</span>
            </div>
            <button
              onClick={() => setNotification(null)}
              className="text-slate-400 hover:text-slate-200 text-xs font-bold px-2 py-1"
            >
              Dismiss
            </button>
          </div>
        )}

        {layoutMode === 'cockpit' ? (
          /* Alternate UI: 3-Panel Tactical Oceanic Radar Cockpit */
          <CockpitConsole
            voyages={filteredVoyages}
            selectedVoyage={selectedVoyage || filteredVoyages[0] || null}
            onSelectVoyage={setSelectedVoyage}
            currentAccount={account}
            leaderboard={leaderboard}
            userProfile={userProfile}
            onOpenTelemetry={openTelemetryModal}
            onOpenInspector={openInspectorModal}
            onOpenAppeal={openAppealModal}
            onOpenSyndicate={openSyndicateModal}
            onAdjudicate={handleAdjudicateDemurrage}
            onFinalize={handleFinalizeSettlement}
            isLoadingAction={isLoadingAction}
            isDarkTheme={isDarkTheme}
          />
        ) : (
          /* Classic Layout: Oceanic Grid & Cards */
          <>
            {/* Hero Headline */}
            <div className="mb-8">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-navy-900 text-white text-xs font-semibold uppercase tracking-wider mb-3 shadow-2xs">
                <Anchor className="w-3.5 h-3.5 text-sky-400" />
                <span>Autonomous Admiralty Jurisdiction</span>
              </div>
              <h1
                className={`text-3xl sm:text-4xl font-extrabold font-space tracking-tight ${
                  isDarkTheme ? 'text-white' : 'text-navy-900'
                }`}
              >
                Maritime Demurrage & Weather Risk Court
              </h1>
              <p
                className={`text-base mt-2 max-w-3xl ${
                  isDarkTheme ? 'text-slate-400' : 'text-slate-600'
                }`}
              >
                Decentralized laytime contract escrow with AI subjective consensus evaluating live
                AIS satellite telemetry and oceanic NOAA weather stations to adjudicate Force
                Majeure storm waivers and delay penalties.
              </p>
            </div>

            {/* Protocol Statistics */}
            <StatsOverview stats={stats} activeCount={activeInTransitCount} />

            {/* Filter Controls & Search */}
            <div
              className={`p-4 rounded-2xl border shadow-xs mb-6 flex flex-col md:flex-row items-center justify-between gap-4 ${
                isDarkTheme
                  ? 'bg-slate-900/90 border-slate-800'
                  : 'bg-white border-slate-200'
              }`}
            >
              {/* Status Tabs */}
              <div className="flex flex-wrap items-center gap-1.5 w-full md:w-auto">
                {[
                  { id: 'ALL', label: 'All Voyages' },
                  { id: 'OPEN', label: 'Open Escrows' },
                  { id: 'TRANSIT', label: 'In Transit' },
                  { id: 'PAYOUT', label: 'Awaiting Payout' },
                  { id: 'DISPUTED', label: 'Disputed' },
                  { id: 'SETTLED', label: 'Settled' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveFilter(tab.id)}
                    className={`px-3.5 py-1.5 text-xs font-semibold rounded-xl transition-all ${
                      activeFilter === tab.id
                        ? isDarkTheme
                          ? 'bg-sky-500 text-slate-950 font-bold shadow-xs'
                          : 'bg-navy-900 text-white shadow-xs'
                        : isDarkTheme
                        ? 'text-slate-400 hover:text-white hover:bg-slate-800'
                        : 'text-slate-600 hover:text-navy-900 hover:bg-slate-100'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Search Bar */}
              <div className="relative w-full md:w-72">
                <input
                  type="text"
                  placeholder="Search by IMO or Address..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`w-full pl-9 pr-4 py-2 text-xs font-mono border rounded-xl focus:outline-hidden focus:ring-2 focus:ring-ocean-500 ${
                    isDarkTheme
                      ? 'bg-slate-950 border-slate-700 text-slate-100 placeholder-slate-500'
                      : 'bg-slate-50/60 border-slate-200 text-slate-900 placeholder-slate-400'
                  }`}
                />
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>

            {/* Voyages Grid */}
            {filteredVoyages.length === 0 ? (
              <div
                className={`rounded-2xl border p-12 text-center shadow-xs ${
                  isDarkTheme
                    ? 'bg-slate-900/60 border-slate-800'
                    : 'bg-white border-slate-200'
                }`}
              >
                <div
                  className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 ${
                    isDarkTheme ? 'bg-slate-800 text-slate-400' : 'bg-slate-100 text-slate-400'
                  }`}
                >
                  <Ship className="w-8 h-8" />
                </div>
                <h3
                  className={`font-space font-bold text-lg mb-1 ${
                    isDarkTheme ? 'text-white' : 'text-navy-900'
                  }`}
                >
                  No Voyages Match Your Criteria
                </h3>
                <p
                  className={`text-sm max-w-md mx-auto mb-5 ${
                    isDarkTheme ? 'text-slate-400' : 'text-slate-500'
                  }`}
                >
                  Create a new maritime booking escrow to start monitoring vessel laytime and ocean
                  weather on GenLayer.
                </p>
                <button
                  onClick={() => setIsCreateOpen(true)}
                  className="px-5 py-2.5 text-sm font-semibold text-white bg-sky-600 hover:bg-sky-500 rounded-xl shadow-sm transition-colors"
                >
                  Book Voyage Escrow
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {filteredVoyages.map((voyage) => (
                  <VoyageCard
                    key={voyage.voyage_id}
                    voyage={voyage}
                    currentAccount={account}
                    onOpenTelemetry={openTelemetryModal}
                    onOpenInspector={openInspectorModal}
                    onOpenAppeal={openAppealModal}
                    onOpenSyndicate={openSyndicateModal}
                    onAdjudicate={handleAdjudicateDemurrage}
                    onFinalize={handleFinalizeSettlement}
                    onCancel={handleCancelOrReclaim}
                    isLoadingAction={isLoadingAction}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </main>

      {/* Modals & Drawers */}
      <CreateVoyageModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={handleCreateVoyage}
        isSubmitting={isLoadingAction}
      />

      <SubmitTelemetryModal
        voyage={activeVoyage}
        isOpen={isTelemetryOpen}
        onClose={() => setIsTelemetryOpen(false)}
        onSubmit={handleSubmitTelemetry}
        isSubmitting={isLoadingAction}
      />

      <AdmiraltyInspectorModal
        voyage={activeVoyage}
        isOpen={isInspectorOpen}
        onClose={() => setIsInspectorOpen(false)}
      />

      <AppealModal
        voyage={activeVoyage}
        isOpen={isAppealOpen}
        onClose={() => setIsAppealOpen(false)}
        onSubmit={handleFileAppeal}
        isSubmitting={isLoadingAction}
      />

      <SyndicateModal
        voyage={activeVoyage}
        pledges={selectedPledges}
        isOpen={isSyndicateOpen}
        onClose={() => setIsSyndicateOpen(false)}
        onSubmit={handlePledgeSyndicate}
        isSubmitting={isLoadingAction}
      />

      <LeaderboardDrawer
        isOpen={isLeaderboardOpen}
        onClose={() => setIsLeaderboardOpen(false)}
        leaderboard={leaderboard}
        userProfile={userProfile}
      />
    </div>
  );
};

export default App;
