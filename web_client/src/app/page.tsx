'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Phone,
  TrendingUp,
  Users,
  Package,
  DollarSign,
  Clock,
  ThumbsUp,
  ThumbsDown,
  Minus,
  AlertCircle,
  X,
  Activity
} from 'lucide-react';
import { useApiGet } from '@/hooks/useApi';

// Interface for metrics data matching the API response
interface MetricsData {
  period: {
    start: string;
    end: string;
    days: number;
  };
  call_metrics: {
    total_calls: number;
    unique_carriers: number;
    average_duration_seconds: number;
    peak_hour: string;
    by_outcome: {
      accepted: number;
      declined: number;
      negotiation_failed: number;
      no_equipment: number;
      callback_requested: number;
      not_eligible: number;
      wrong_lane: number;
      information_only: number;
    };
  };
  conversion_metrics: {
    loads_booked: number;
    booking_rate: number;
    average_negotiation_rounds: number;
    first_offer_acceptance_rate: number;
    average_time_to_accept_minutes: number;
  };
  financial_metrics: {
    total_booked_revenue: number;
    average_load_value: number;
    average_agreed_rate: number;
    average_loadboard_rate: number;
    average_margin_percentage: number;
  };
  sentiment_analysis: {
    positive: number;
    neutral: number;
    negative: number;
    average_score: number;
    trend: string;
  };
  carrier_metrics: {
    repeat_callers: number;
    new_carriers: number;
    top_equipment_types: Array<{ type: string; count: number }>;
    average_mc_verification_time_ms: number;
  };
  performance_indicators: {
    api_availability: number;
    average_response_time_ms: number;
    error_rate: number;
    handoff_success_rate: number;
  };
  generated_at: string;
}

// MetricCard component
function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color = "blue"
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  trend?: { value: number; isPositive: boolean };
  color?: "blue" | "green" | "orange" | "purple" | "red";
}) {
  const colorClasses = {
    blue: "bg-blue-50 border-blue-200 text-blue-600",
    green: "bg-green-50 border-green-200 text-green-600",
    orange: "bg-orange-50 border-orange-200 text-orange-600",
    purple: "bg-purple-50 border-purple-200 text-purple-600",
    red: "bg-red-50 border-red-200 text-red-600"
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`p-6 rounded-lg border-2 ${colorClasses[color]} hover:shadow-lg transition-shadow duration-200`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
          {trend && (
            <div className={`flex items-center mt-2 text-sm ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
              <TrendingUp className={`w-4 h-4 mr-1 ${!trend.isPositive ? 'rotate-180' : ''}`} />
              {Math.abs(trend.value)}% from last week
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </motion.div>
  );
}

// Call Agent Modal component
function CallAgentModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">Call Sales Agent</h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="p-1 rounded-full hover:bg-gray-100 transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-2">Web Call Trigger</h4>
                  <p className="text-sm text-blue-700">
                    To test the voice agent, click the button below to trigger a test call:
                  </p>
                  <button type="button" className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                    <Phone className="w-4 h-4 inline mr-2" />
                    Start Test Call
                  </button>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-semibold text-gray-900 mb-2">Call Flow</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Agent asks for MC number</li>
                    <li>• Verifies carrier eligibility</li>
                    <li>• Searches for matching loads</li>
                    <li>• Handles price negotiation</li>
                    <li>• Transfers to sales rep on agreement</li>
                  </ul>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default function HomePage() {
  const [showCallModal, setShowCallModal] = useState(false);

  // Fetch metrics data from the API
  const { data: metrics, isLoading, error } = useApiGet<MetricsData>('/api/v1/metrics/summary');

  // Mock data for development (fallback)
  const mockMetrics: MetricsData = {
    period: {
      start: "2024-08-01T00:00:00Z",
      end: "2024-08-15T23:59:59Z",
      days: 15
    },
    call_metrics: {
      total_calls: 247,
      unique_carriers: 189,
      average_duration_seconds: 240,
      peak_hour: "14:00",
      by_outcome: {
        accepted: 89,
        declined: 67,
        negotiation_failed: 45,
        no_equipment: 23,
        callback_requested: 12,
        not_eligible: 8,
        wrong_lane: 3,
        information_only: 0
      }
    },
    conversion_metrics: {
      loads_booked: 89,
      booking_rate: 36.1,
      average_negotiation_rounds: 1.8,
      first_offer_acceptance_rate: 42.7,
      average_time_to_accept_minutes: 4.2
    },
    financial_metrics: {
      total_booked_revenue: 241750.00,
      average_load_value: 2715.17,
      average_agreed_rate: 2850.50,
      average_loadboard_rate: 2720.00,
      average_margin_percentage: 4.8
    },
    sentiment_analysis: {
      positive: 145,
      neutral: 78,
      negative: 24,
      average_score: 0.74,
      trend: "IMPROVING"
    },
    carrier_metrics: {
      repeat_callers: 45,
      new_carriers: 144,
      top_equipment_types: [
        { type: "53-foot van", count: 98 },
        { type: "Reefer", count: 67 },
        { type: "Flatbed", count: 45 }
      ],
      average_mc_verification_time_ms: 420
    },
    performance_indicators: {
      api_availability: 99.96,
      average_response_time_ms: 118,
      error_rate: 0.015,
      handoff_success_rate: 97.2
    },
    generated_at: new Date().toISOString()
  };

  const displayMetrics = metrics || mockMetrics;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">HappyRobot FDE</h1>
              <p className="text-sm text-gray-600">Inbound Carrier Sales</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center text-sm text-gray-500">
                <Activity className="w-4 h-4 mr-1" />
                Live Dashboard
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl font-bold text-gray-900 mb-4"
          >
            Automated Voice Agent for Carrier Load Matching
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto"
          >
            Real-time dashboard showing voice agent performance, carrier interactions, and load negotiation outcomes.
          </motion.p>

          {/* Call Agent Button */}
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            type="button"
            onClick={() => setShowCallModal(true)}
            className="inline-flex items-center px-8 py-4 bg-blue-600 text-white font-semibold rounded-xl shadow-lg hover:bg-blue-700 transform hover:scale-105 transition-all duration-200"
          >
            <Phone className="w-5 h-5 mr-3" />
            Call Sales Agent
          </motion.button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading metrics...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <p className="text-red-700">Failed to load metrics. Showing demo data.</p>
            </div>
          </div>
        )}

        {/* Metrics Dashboard */}
        {!isLoading && (
          <>
            {/* Key Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <MetricCard
                title="Total Calls Today"
                value={displayMetrics.call_metrics.total_calls}
                icon={Phone}
                color="blue"
                trend={{ value: 12, isPositive: true }}
              />
              <MetricCard
                title="Unique Carriers"
                value={displayMetrics.call_metrics.unique_carriers}
                subtitle={`${Math.round((displayMetrics.call_metrics.unique_carriers / displayMetrics.call_metrics.total_calls) * 100)}% of total calls`}
                icon={Users}
                color="green"
                trend={{ value: 8, isPositive: true }}
              />
              <MetricCard
                title="Loads Booked"
                value={displayMetrics.conversion_metrics.loads_booked}
                subtitle={`${displayMetrics.conversion_metrics.booking_rate.toFixed(1)}% booking rate`}
                icon={Package}
                color="orange"
                trend={{ value: 5, isPositive: true }}
              />
              <MetricCard
                title="Revenue Booked"
                value={`$${(displayMetrics.financial_metrics.total_booked_revenue / 1000).toFixed(0)}K`}
                subtitle={`$${displayMetrics.financial_metrics.average_load_value.toFixed(0)} avg per load`}
                icon={DollarSign}
                color="purple"
                trend={{ value: 3, isPositive: true }}
              />
            </div>

            {/* Additional Metrics Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <MetricCard
                title="Average Response Time"
                value={`${(displayMetrics.performance_indicators.average_response_time_ms / 1000).toFixed(1)}s`}
                subtitle="Time to first response"
                icon={Clock}
                color="blue"
              />
              <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Activity className="w-5 h-5 mr-2 text-purple-600" />
                  Sentiment Distribution
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <ThumbsUp className="w-4 h-4 mr-2 text-green-600" />
                      <span className="text-sm font-medium">Positive</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-2xl font-bold text-green-600 mr-2">
                        {displayMetrics.sentiment_analysis.positive}
                      </span>
                      <span className="text-sm text-gray-500">
                        ({Math.round((displayMetrics.sentiment_analysis.positive / displayMetrics.call_metrics.total_calls) * 100)}%)
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Minus className="w-4 h-4 mr-2 text-gray-600" />
                      <span className="text-sm font-medium">Neutral</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-2xl font-bold text-gray-600 mr-2">
                        {displayMetrics.sentiment_analysis.neutral}
                      </span>
                      <span className="text-sm text-gray-500">
                        ({Math.round((displayMetrics.sentiment_analysis.neutral / displayMetrics.call_metrics.total_calls) * 100)}%)
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <ThumbsDown className="w-4 h-4 mr-2 text-red-600" />
                      <span className="text-sm font-medium">Negative</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-2xl font-bold text-red-600 mr-2">
                        {displayMetrics.sentiment_analysis.negative}
                      </span>
                      <span className="text-sm text-gray-500">
                        ({Math.round((displayMetrics.sentiment_analysis.negative / displayMetrics.call_metrics.total_calls) * 100)}%)
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* System Status */}
            <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                  <span className="text-sm">Voice Agent: Online</span>
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                  <span className="text-sm">FMCSA API: Connected</span>
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                  <span className="text-sm">Load Database: Active</span>
                </div>
              </div>
            </div>
          </>
        )}
      </main>

      {/* Call Agent Modal */}
      <CallAgentModal isOpen={showCallModal} onClose={() => setShowCallModal(false)} />
    </div>
  );
}
