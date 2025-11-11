/**
 * Example component showing how to use BackendAPI for authentication
 *
 * This demonstrates the proper way to:
 * 1. Use BackendAPI service instead of direct API calls
 * 2. Handle authentication state
 * 3. Manage tokens automatically
 * 4. Handle errors gracefully
 */

import React, { useState } from 'react';
import BackendAPI, { TokenManager } from '@/services/BackendAPI';

export function AuthExample() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(TokenManager.isAuthenticated());

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // Use BackendAPI instead of direct fetch
      const response = await BackendAPI.auth.login(username, password);

      console.log('Login successful:', response);
      setIsAuthenticated(true);

      // Tokens are automatically stored by BackendAPI
      // You can now make authenticated requests

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      console.error('Login error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await BackendAPI.auth.logout();
      setIsAuthenticated(false);
      setUsername('');
      setPassword('');
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  const fetchPortfolio = async () => {
    try {
      // Example of making an authenticated request
      const portfolio = await BackendAPI.portfolio.get();
      console.log('Portfolio data:', portfolio);
      alert(`Portfolio value: $${portfolio.total_value}`);
    } catch (err) {
      console.error('Error fetching portfolio:', err);
      alert('Failed to fetch portfolio');
    }
  };

  return (
    <div className="p-6 max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-4">
        Authentication Example
      </h2>

      {!isAuthenticated ? (
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border rounded"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border rounded"
              required
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      ) : (
        <div className="space-y-4">
          <p className="text-green-600 font-medium">
            ✓ Logged in successfully!
          </p>

          <div className="space-y-2">
            <button
              onClick={fetchPortfolio}
              className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700"
            >
              Fetch Portfolio (Example API Call)
            </button>

            <button
              onClick={handleLogout}
              className="w-full bg-gray-600 text-white py-2 rounded hover:bg-gray-700"
            >
              Logout
            </button>
          </div>
        </div>
      )}

      <div className="mt-6 p-4 bg-gray-100 rounded text-sm">
        <p className="font-semibold mb-2">How this works:</p>
        <ul className="list-disc pl-5 space-y-1">
          <li>Uses <code>BackendAPI.auth.login()</code> instead of direct fetch</li>
          <li>Tokens are automatically stored in localStorage</li>
          <li>All subsequent API calls include auth headers</li>
          <li>Token refresh happens automatically on 401 errors</li>
          <li>Logout clears all tokens</li>
        </ul>
      </div>
    </div>
  );
}

export default AuthExample;
