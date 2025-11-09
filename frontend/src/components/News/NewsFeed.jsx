import React from 'react';
import Card from '../ui/Card';

const NewsFeed = ({ news }) => {
  if (!news || news.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="font-bold text-lg mb-4">📰 Financial News</h3>
        <p className="text-gray-500 text-center py-4">No news available</p>
      </Card>
    );
  }

  const getCategoryColor = (category) => {
    const colors = {
      'Monetary Policy': 'bg-purple-100 text-purple-800',
      'Equities': 'bg-green-100 text-green-800',
      'Commodities': 'bg-yellow-100 text-yellow-800',
      'Cryptocurrency': 'bg-blue-100 text-blue-800',
      'Real Estate': 'bg-red-100 text-red-800',
      'Forex': 'bg-indigo-100 text-indigo-800',
      'Technology': 'bg-cyan-100 text-cyan-800',
      'Economic Indicators': 'bg-orange-100 text-orange-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  return (
    <Card className="p-6">
      <h3 className="font-bold text-lg mb-4">📰 Financial News</h3>
      <div className="space-y-3 max-h-[600px] overflow-y-auto">
        {news.map((article, idx) => (
          <a
            key={idx}
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 mb-1 hover:text-blue-600">
                  {article.title}
                </h4>
                <p className="text-sm text-gray-600 mb-2">{article.summary}</p>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-1 rounded ${getCategoryColor(article.category)}`}>
                    {article.category}
                  </span>
                  <span className="text-xs text-gray-500">{article.source}</span>
                </div>
              </div>
            </div>
          </a>
        ))}
      </div>
    </Card>
  );
};

export default NewsFeed;
