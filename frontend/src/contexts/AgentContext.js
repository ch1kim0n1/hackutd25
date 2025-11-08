import React, { createContext, useContext, useState } from 'react';

const AgentContext = createContext();

export const useAgents = () => {
  return useContext(AgentContext);
};

export const AgentProvider = ({ children }) => {
  const [agents, setAgents] = useState([
    { id: 'market', name: 'Market Agent', status: 'Scanning...' },
    { id: 'strategy', name: 'Strategy Agent', status: 'Idle' },
    { id: 'risk', name: 'Risk Agent', status: 'Monitoring' },
  ]);

  const value = {
    agents,
    // Functions to update agent state can be added here
  };

  return (
    <AgentContext.Provider value={value}>
      {children}
    </AgentContext.Provider>
  );
};
