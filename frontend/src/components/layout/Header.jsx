import React from 'react';

const Header = () => {
  return (
    <header className="bg-gray-800 text-white p-4 shadow-md">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-xl font-bold">APEX Financial OS</h1>
        <div>
          {/* Navigation or User Info can go here */}
        </div>
      </div>
    </header>
  );
};

export default Header;
