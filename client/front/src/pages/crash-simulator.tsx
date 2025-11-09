import { useState } from "react";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";

const CrashSimulator = () => {
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);

  const scenarios = [
    {
      id: "2008",
      name: "2008 Financial Crisis",
      description: "Replicate the 2008 housing market crash and banking crisis",
      duration: "Historical: 18 months",
      maxDrawdown: "-56.4%",
      recovery: "5+ years"
    },
    {
      id: "2020",
      name: "COVID-19 Pandemic",
      description: "Simulate the market crash triggered by the global pandemic",
      duration: "Historical: 5 weeks",
      maxDrawdown: "-33.9%",
      recovery: "1 year"
    },
    {
      id: "dotcom",
      name: "Dot-com Bubble Burst",
      description: "Recreate the 2000-2002 tech bubble collapse",
      duration: "Historical: 2.5 years",
      maxDrawdown: "-49.1%",
      recovery: "4 years"
    }
  ];

  const runSimulation = () => {
    if (!selectedScenario) return;

    setIsRunning(true);
    setProgress(0);

    // Simulate progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunning(false);
          return 100;
        }
        return prev + Math.random() * 15;
      });
    }, 500);
  };

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">Market Crash Simulator</h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Experience historical market crashes in fast-forward. Compare APEX AI strategies against buy-and-hold approaches.
          </p>
        </div>

        {/* Scenario Selection */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {scenarios.map((scenario) => (
            <Card
              key={scenario.id}
              className={`cursor-pointer transition-all ${
                selectedScenario === scenario.id
                  ? 'bg-purple-900/50 border-purple-500'
                  : 'bg-slate-800/50 border-slate-700 hover:bg-slate-700/50'
              }`}
              onClick={() => setSelectedScenario(scenario.id)}
            >
              <CardHeader>
                <h3 className="text-xl font-bold text-white">{scenario.name}</h3>
              </CardHeader>
              <CardBody>
                <p className="text-gray-300 mb-4">{scenario.description}</p>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Duration:</span>
                    <span className="text-white">{scenario.duration}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Max Drawdown:</span>
                    <span className="text-red-400">{scenario.maxDrawdown}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Recovery Time:</span>
                    <span className="text-green-400">{scenario.recovery}</span>
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>

        {/* Simulation Controls */}
        <div className="text-center mb-12">
          <Button
            size="lg"
            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-12 py-4 text-lg"
            onPress={runSimulation}
            disabled={!selectedScenario || isRunning}
          >
            {isRunning ? "Running Simulation..." : "🚀 Run Crash Simulation"}
          </Button>
          {!selectedScenario && (
            <p className="text-gray-400 mt-2">Select a scenario above to begin</p>
          )}
        </div>

        {/* Progress Bar */}
        {isRunning && (
          <div className="mb-12">
            <div className="max-w-2xl mx-auto">
              <div className="flex justify-between mb-2">
                <span className="text-white">Simulation Progress</span>
                <span className="text-white">{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-4">
                <div
                  className="bg-purple-600 h-4 rounded-full transition-all duration-500"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="text-gray-400 mt-2 text-center">
                Fast-forwarding through {selectedScenario} scenario at 100x speed...
              </p>
            </div>
          </div>
        )}

        {/* Results Placeholder */}
        {progress >= 100 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Performance Comparison */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <h3 className="text-2xl font-bold text-white">Performance Comparison</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-4 bg-slate-700/50 rounded-lg">
                    <div>
                      <h4 className="text-white font-semibold">APEX AI Strategy</h4>
                      <p className="text-gray-400 text-sm">Dynamic risk management</p>
                    </div>
                    <Chip color="success" variant="flat" className="text-lg">
                      -12.3%
                    </Chip>
                  </div>

                  <div className="flex justify-between items-center p-4 bg-slate-700/50 rounded-lg">
                    <div>
                      <h4 className="text-white font-semibold">Buy & Hold</h4>
                      <p className="text-gray-400 text-sm">Traditional approach</p>
                    </div>
                    <Chip color="danger" variant="flat" className="text-lg">
                      -45.6%
                    </Chip>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-green-900/20 border border-green-700 rounded-lg">
                  <h4 className="text-green-400 font-semibold mb-2">APEX Advantage</h4>
                  <p className="text-gray-300 text-sm">
                    APEX reduced losses by 73% through intelligent risk management and timely position adjustments.
                  </p>
                </div>
              </CardBody>
            </Card>

            {/* Key Insights */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <h3 className="text-2xl font-bold text-white">Key Insights</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="p-4 bg-blue-900/20 border border-blue-700 rounded-lg">
                    <h4 className="text-blue-400 font-semibold mb-2">Risk Management</h4>
                    <p className="text-gray-300 text-sm">
                      APEX automatically reduced exposure during early warning signals, avoiding the worst of the downturn.
                    </p>
                  </div>

                  <div className="p-4 bg-purple-900/20 border border-purple-700 rounded-lg">
                    <h4 className="text-purple-400 font-semibold mb-2">Recovery Strategy</h4>
                    <p className="text-gray-300 text-sm">
                      Gradual re-entry into the market during recovery periods maximized upside capture.
                    </p>
                  </div>

                  <div className="p-4 bg-yellow-900/20 border border-yellow-700 rounded-lg">
                    <h4 className="text-yellow-400 font-semibold mb-2">Agent Coordination</h4>
                    <p className="text-gray-300 text-sm">
                      Market, Risk, and Strategy agents worked together to optimize timing and position sizing.
                    </p>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-16">
          <p className="text-gray-400 mb-4">
            This simulation demonstrates how APEX AI agents work together to protect and grow your investments.
          </p>
          <Button
            variant="bordered"
            className="border-slate-600 text-slate-300"
            onPress={() => window.history.back()}
          >
            ← Back to APEX
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CrashSimulator;
