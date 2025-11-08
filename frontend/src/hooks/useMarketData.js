import { useState, useEffect } from 'react';
// import { alpacaApi } from '../../services/alpaca-api'; // Example import

const useMarketData = (symbol) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!symbol) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        // const response = await alpacaApi.get(`/marketdata/${symbol}`);
        // setData(response.data);
        setData({ price: Math.random() * 1000 }); // Mock data
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Fetch every 5 seconds

    return () => clearInterval(interval);
  }, [symbol]);

  return { data, loading, error };
};

export default useMarketData;
