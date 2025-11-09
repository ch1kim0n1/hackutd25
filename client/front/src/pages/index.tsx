import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";

export const IndexPage = () => {
  const navigate = useNavigate();
  const [agentsOnline, setAgentsOnline] = useState(6);

  // Simulate agents coming online
  useEffect(() => {
    const interval = setInterval(() => {
      setAgentsOnline(prev => Math.min(prev + 1, 6));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative max-w-7xl mx-auto px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">
              APEX
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-300">
              Multi-Agent Financial Operating System
            </p>
            <p className="mt-4 text-xl leading-8 text-gray-200 max-w-3xl mx-auto">
              <strong className="text-purple-400">Transparent AI</strong> for investment management with
              <strong className="text-purple-400"> human-in-the-loop</strong> design.
              Unlike black-box robo-advisors, APEX lets you observe and participate in AI agent discussions.
            </p>

            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Button
                size="lg"
                className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-8 py-3 text-lg"
                onPress={() => navigate("/war-room")}
              >
                🚀 Enter War Room
              </Button>
              <Button
                size="lg"
                variant="bordered"
                className="border-purple-400 text-purple-400 hover:bg-purple-400 hover:text-white"
                onPress={() => navigate("/crash-simulator")}
              >
                📊 Market Crash Simulator
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Status Section */}
      <div className="py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              6 Specialized AI Agents
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-300">
              Each agent brings unique expertise to your investment decisions
            </p>
          </div>

          <div className="mx-auto mt-16 max-w-7xl">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {/* Market Agent */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardBody className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-3 h-3 rounded-full ${agentsOnline >= 1 ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
                    <h3 className="text-lg font-semibold text-white">🔍 Market Agent</h3>
                  </div>
                  <p className="text-gray-300 text-sm">
                    Real-time market intelligence, news scraping, VIX tracking, sentiment analysis via Alpaca API
                  </p>
                </CardBody>
              </Card>

              {/* Strategy Agent */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardBody className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-3 h-3 rounded-full ${agentsOnline >= 2 ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
                    <h3 className="text-lg font-semibold text-white">🧠 Strategy Agent</h3>
                  </div>
                  <p className="text-gray-300 text-sm">
                    Portfolio optimization, opportunity evaluation, parallel scenario planning
                  </p>
                </CardBody>
              </Card>

              {/* Risk Agent */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardBody className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-3 h-3 rounded-full ${agentsOnline >= 3 ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
                    <h3 className="text-lg font-semibold text-white">⚠️ Risk Agent</h3>
                  </div>
                  <p className="text-gray-300 text-sm">
                    Risk limits, Monte Carlo simulations, stress testing, position sizing
                  </p>
                </CardBody>
              </Card>

              {/* Executor Agent */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardBody className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-3 h-3 rounded-full ${agentsOnline >= 4 ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
                    <h3 className="text-lg font-semibold text-white">⚡ Executor Agent</h3>
                  </div>
                  <p className="text-gray-300 text-sm">
                    Alpaca API integration, order validation, execution monitoring, error handling
                  </p>
                </CardBody>
              </Card>

              {/* Explainer Agent */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardBody className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-3 h-3 rounded-full ${agentsOnline >= 5 ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
                    <h3 className="text-lg font-semibold text-white">💬 Explainer Agent</h3>
                  </div>
                  <p className="text-gray-300 text-sm">
                    Plain English explanations, adaptive education (ELI5 to advanced), decision rationale
                  </p>
                </CardBody>
              </Card>

              {/* User Agent */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardBody className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-3 h-3 rounded-full ${agentsOnline >= 6 ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
                    <h3 className="text-lg font-semibold text-white">👤 User Agent</h3>
                  </div>
                  <p className="text-gray-300 text-sm">
                    Voice/text input processing, human insights integration, decision override workflows
                  </p>
                </CardBody>
              </Card>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-24 sm:py-32 bg-slate-800/30">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Core Features
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-300">
              Experience investment management like never before
            </p>
          </div>

          <div className="mx-auto mt-16 max-w-4xl">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2">
              {/* War Room */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardBody className="p-6">
                  <h3 className="text-xl font-semibold text-white mb-3">🎯 Visual Agent War Room</h3>
                  <ul className="text-gray-300 text-sm space-y-2">
                    <li>• Live multi-agent conversation display</li>
                    <li>• Color-coded debate tracking</li>
                    <li>• Real-time consensus visualization</li>
                    <li>• WebSocket-powered updates</li>
                  </ul>
                </CardBody>
              </Card>

              {/* Voice Interaction */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardBody className="p-6">
                  <h3 className="text-xl font-semibold text-white mb-3">🎤 Voice Interaction</h3>
                  <ul className="text-gray-300 text-sm space-y-2">
                    <li>• Push-to-talk with instant transcription</li>
                    <li>• "Hold on" error correction mechanism</li>
                    <li>• Natural language command processing</li>
                    <li>• Voice-guided goal setting</li>
                  </ul>
                </CardBody>
              </Card>

              {/* Crash Simulator */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardBody className="p-6">
                  <h3 className="text-xl font-semibold text-white mb-3">📈 Market Crash Simulator</h3>
                  <ul className="text-gray-300 text-sm space-y-2">
                    <li>• Time-compressed historical scenarios</li>
                    <li>• APEX vs buy-and-hold comparison</li>
                    <li>• 100x speed simulation with GPU acceleration</li>
                    <li>• Visual performance attribution</li>
                  </ul>
                </CardBody>
              </Card>

              {/* Personal Finance */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardBody className="p-6">
                  <h3 className="text-xl font-semibold text-white mb-3">💰 Personal Finance</h3>
                  <ul className="text-gray-300 text-sm space-y-2">
                    <li>• Plaid integration for net worth tracking</li>
                    <li>• AI goal planner with timeline projections</li>
                    <li>• Smart subscription tracker</li>
                    <li>• Performance vs S&P 500 comparison</li>
                  </ul>
                </CardBody>
              </Card>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to Experience Transparent AI Investing?
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-300">
              Join the future of investment management where AI agents work transparently with human oversight
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Button
                size="lg"
                className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-8 py-3 text-lg"
                onPress={() => navigate("/war-room")}
              >
                🚀 Start APEX Demo
              </Button>
            </div>
            <p className="mt-4 text-sm text-gray-400">
              Running in demo mode - no API keys required
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
