import React from 'react';

const Sidebar = ({ currentPage, onNavigate }) => {
  const navItems = [
    { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
    { id: 'warroom', label: '🎯 War Room', icon: '🎯' },
    { id: 'trading', label: '💼 Trading', icon: '💼' },
    { id: 'crashsim', label: '📉 Crash Simulator', icon: '📉' },
  ];

  return (
    <aside className="bg-gray-900 text-white w-64 min-h-screen p-4">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">APEX</h1>
        <p className="text-xs text-gray-400">Multi-Agent Financial System</p>
      </div>
      <nav>
        <ul>
          {navItems.map(item => (
            <li key={item.id} className="mb-2">
              <button
                onClick={() => onNavigate && onNavigate(item.id)}
                className={`w-full text-left block px-3 py-2 rounded transition-colors ${
                  currentPage === item.id
                    ? 'bg-blue-600 text-white'
                    : 'hover:bg-gray-800 text-gray-300 hover:text-white'
                }`}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
