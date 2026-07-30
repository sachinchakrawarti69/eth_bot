'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { 
  ArrowUpIcon, 
  ArrowDownIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  SignalIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  MinusCircleIcon,
} from '@heroicons/react/24/solid';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [metrics, setMetrics] = useState({
    price: 0,
    signal: '--',
    confidence: 0,
    totalTrades: 0,
    totalPnl: 0,
    winRate: 0,
  });
  const [priceData, setPriceData] = useState({ dates: [], prices: [] });
  const [signals, setSignals] = useState([]);
  const [trades, setTrades] = useState([]);
  const [lastUpdate, setLastUpdate] = useState('--');

  const fetchData = async () => {
    try {
      setRefreshing(true);

      // Fetch latest metrics
      const latestRes = await axios.get('/api/latest');
      const latest = latestRes.data;
      setMetrics({
        price: latest.price || 0,
        signal: latest.signal || '--',
        confidence: latest.confidence || 0,
        totalTrades: latest.total_trades || 0,
      });

      // Fetch performance
      const perfRes = await axios.get('/api/performance');
      const perf = perfRes.data;
      setMetrics(prev => ({
        ...prev,
        totalPnl: perf.total_pnl || 0,
        winRate: perf.win_rate || 0,
      }));

      // Fetch price chart data
      const priceRes = await axios.get('/api/price');
      setPriceData({
        dates: priceRes.data.dates || [],
        prices: priceRes.data.prices || [],
      });

      // Fetch signals
      const signalsRes = await axios.get('/api/signals');
      setSignals(signalsRes.data || []);

      // Fetch trades
      const tradesRes = await axios.get('/api/trades');
      setTrades(tradesRes.data || []);

      setLastUpdate(new Date().toLocaleTimeString());
      setLoading(false);
      setRefreshing(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getSignalBadge = (signal) => {
    const colors = {
      BUY: 'bg-green-500 text-white',
      SELL: 'bg-red-500 text-white',
      HOLD: 'bg-yellow-500 text-black',
    };
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-bold ${colors[signal] || 'bg-gray-500 text-white'}`}>
        {signal || 'HOLD'}
      </span>
    );
  };

  const getSignalIcon = (signal) => {
    if (signal === 'BUY') return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
    if (signal === 'SELL') return <XCircleIcon className="w-5 h-5 text-red-500" />;
    return <MinusCircleIcon className="w-5 h-5 text-yellow-500" />;
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#8888aa' },
      },
    },
    scales: {
      x: {
        grid: { color: '#1a1a3e' },
        ticks: { color: '#8888aa', maxTicksLimit: 20 },
      },
      y: {
        grid: { color: '#1a1a3e' },
        ticks: { color: '#8888aa' },
      },
    },
  };

  const chartData = {
    labels: priceData.dates.slice(-30),
    datasets: [
      {
        label: 'ETH Price (USD)',
        data: priceData.prices.slice(-30),
        borderColor: '#4ecca3',
        backgroundColor: 'rgba(78, 204, 163, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 6,
      },
    ],
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a1a] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#4ecca3] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-[#8888aa]">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a1a] p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-[#1a1a3e] rounded-xl p-4 md:p-6 mb-6 border border-[#2a2a5e]">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-[#4ecca3]">🚀 ETH Trading Dashboard</h1>
              <div className="flex items-center mt-2 text-xs md:text-sm text-[#8888aa]">
                <span className="w-2 h-2 bg-green-500 rounded-full inline-block mr-2 animate-pulse"></span>
                <span>Online</span>
                <span className="mx-2 md:mx-4">|</span>
                <span>Last update: {lastUpdate || '--'}</span>
              </div>
            </div>
            <button
              onClick={fetchData}
              disabled={refreshing}
              className="bg-[#4ecca3] text-[#0a0a1a] px-4 py-2 rounded-lg font-bold hover:opacity-80 transition flex items-center gap-2 disabled:opacity-50 text-sm md:text-base"
            >
              <ArrowPathIcon className={`w-4 h-4 md:w-5 md:h-5 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-6">
          {/* Price Card */}
          <div className="bg-[#1a1a3e] rounded-xl p-4 md:p-6 border border-[#2a2a5e] hover:border-[#4ecca3] transition cursor-pointer">
            <div className="flex items-center justify-between">
              <h3 className="text-[#8888aa] text-xs uppercase tracking-wider">💰 Price</h3>
              <CurrencyDollarIcon className="w-5 h-5 md:w-6 md:h-6 text-[#4ecca3]" />
            </div>
            <div className="text-2xl md:text-3xl font-bold text-white mt-2">
              {metrics.price ? `$${metrics.price.toFixed(2)}` : '--'}
            </div>
            <div className="text-xs md:text-sm text-[#8888aa] mt-1">24h change: --</div>
          </div>

          {/* Signal Card */}
          <div className="bg-[#1a1a3e] rounded-xl p-4 md:p-6 border border-[#2a2a5e] hover:border-[#4ecca3] transition cursor-pointer">
            <div className="flex items-center justify-between">
              <h3 className="text-[#8888aa] text-xs uppercase tracking-wider">📈 Signal</h3>
              <SignalIcon className="w-5 h-5 md:w-6 md:h-6 text-[#4ecca3]" />
            </div>
            <div className="mt-2 flex items-center gap-2">
              {getSignalIcon(metrics.signal)}
              {getSignalBadge(metrics.signal)}
            </div>
            <div className="text-xs md:text-sm text-[#8888aa] mt-1">
              Confidence: {metrics.confidence ? `${(metrics.confidence * 100).toFixed(1)}%` : '--'}
            </div>
          </div>

          {/* Trades Card */}
          <div className="bg-[#1a1a3e] rounded-xl p-4 md:p-6 border border-[#2a2a5e] hover:border-orange-400 transition cursor-pointer">
            <div className="flex items-center justify-between">
              <h3 className="text-[#8888aa] text-xs uppercase tracking-wider">📊 Trades</h3>
              <ChartBarIcon className="w-5 h-5 md:w-6 md:h-6 text-orange-400" />
            </div>
            <div className="text-2xl md:text-3xl font-bold text-orange-400 mt-2">
              {metrics.totalTrades || 0}
            </div>
            <div className="text-xs md:text-sm text-[#8888aa] mt-1">
              Win rate: {metrics.winRate ? `${metrics.winRate.toFixed(1)}%` : '--'}
            </div>
          </div>

          {/* P&L Card */}
          <div className="bg-[#1a1a3e] rounded-xl p-4 md:p-6 border border-[#2a2a5e] hover:border-[#4ecca3] transition cursor-pointer">
            <div className="flex items-center justify-between">
              <h3 className="text-[#8888aa] text-xs uppercase tracking-wider">💰 P&L</h3>
              {metrics.totalPnl >= 0 ? (
                <ArrowUpIcon className="w-5 h-5 md:w-6 md:h-6 text-green-500" />
              ) : (
                <ArrowDownIcon className="w-5 h-5 md:w-6 md:h-6 text-red-500" />
              )}
            </div>
            <div className={`text-2xl md:text-3xl font-bold mt-2 ${metrics.totalPnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {metrics.totalPnl ? `$${metrics.totalPnl.toFixed(2)}` : '$0.00'}
            </div>
            <div className="text-xs md:text-sm text-[#8888aa] mt-1">Avg P&L: --</div>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-[#1a1a3e] rounded-xl p-4 md:p-6 border border-[#2a2a5e] mb-6">
          <h3 className="text-[#8888aa] text-xs uppercase tracking-wider mb-4">📈 Price Chart</h3>
          <div className="h-60 md:h-72">
            {priceData.prices.length > 0 ? (
              <Line data={chartData} options={chartOptions} />
            ) : (
              <div className="h-full flex items-center justify-center text-[#8888aa]">
                No price data available
              </div>
            )}
          </div>
        </div>

        {/* Signals Table */}
        <div className="bg-[#1a1a3e] rounded-xl p-4 md:p-6 border border-[#2a2a5e] mb-6">
          <h3 className="text-[#8888aa] text-xs uppercase tracking-wider mb-4">📊 Recent Signals</h3>
          {signals.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[#8888aa] text-xs uppercase tracking-wider">
                    <th className="pb-3">ID</th>
                    <th className="pb-3">Time</th>
                    <th className="pb-3">Signal</th>
                    <th className="pb-3">Price</th>
                    <th className="pb-3">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {signals.slice(0, 10).map((s) => (
                    <tr key={s.id} className="border-t border-[#2a2a5e]/50">
                      <td className="py-3">{s.id}</td>
                      <td className="py-3 text-[#8888aa]">
                        {s.timestamp ? new Date(s.timestamp).toLocaleString() : '--'}
                      </td>
                      <td className="py-3">{getSignalBadge(s.signal_type)}</td>
                      <td className="py-3">${s.current_price?.toFixed(2) || '--'}</td>
                      <td className="py-3">
                        {s.confidence ? `${(s.confidence * 100).toFixed(1)}%` : '--'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-[#8888aa] py-8">No signals found</div>
          )}
        </div>

        {/* Trades Table */}
        <div className="bg-[#1a1a3e] rounded-xl p-4 md:p-6 border border-[#2a2a5e]">
          <h3 className="text-[#8888aa] text-xs uppercase tracking-wider mb-4">💰 Recent Trades</h3>
          {trades.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[#8888aa] text-xs uppercase tracking-wider">
                    <th className="pb-3">ID</th>
                    <th className="pb-3">Time</th>
                    <th className="pb-3">Type</th>
                    <th className="pb-3">Price</th>
                    <th className="pb-3">Quantity</th>
                    <th className="pb-3">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.slice(0, 10).map((t) => (
                    <tr key={t.id} className="border-t border-[#2a2a5e]/50">
                      <td className="py-3">{t.id}</td>
                      <td className="py-3 text-[#8888aa]">
                        {t.timestamp ? new Date(t.timestamp).toLocaleString() : '--'}
                      </td>
                      <td className="py-3">{getSignalBadge(t.type)}</td>
                      <td className="py-3">${t.price?.toFixed(2) || '--'}</td>
                      <td className="py-3">{t.quantity || '--'}</td>
                      <td className={`py-3 font-bold ${(t.pnl || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        ${(t.pnl || 0).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-[#8888aa] py-8">No trades found</div>
          )}
        </div>
      </div>
    </div>
  );
}