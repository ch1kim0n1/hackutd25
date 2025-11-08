import React from 'react';

const Sidebar = () => {
  return (
    <aside className="bg-gray-900 text-white w-64 min-h-screen p-4">
      <nav>
        <ul>
          <li className="mb-2"><a href="#" className="block hover:text-gray-300">Dashboard</a></li>
          <li className="mb-2"><a href="#" className="block hover:text-gray-300">War Room</a></li>
          <li className="mb-2"><a href="#" className="block hover:text-gray-300">Market Simulator</a></li>
          <li className="mb-2"><a href="#" className="block hover:text-gray-300">Settings</a></li>
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
