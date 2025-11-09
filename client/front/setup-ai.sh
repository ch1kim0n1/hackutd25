#!/bin/bash

# AI Integration Setup Script
# This script helps set up the OpenAI integration for the trading app

echo "🤖 AI Integration Setup"
echo "======================="
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Get your OpenAI API key:"
echo "   👉 Visit: https://platform.openai.com/api-keys"
echo "   👉 Sign in and create a new secret key"
echo ""
echo "2. Add your API key to the .env file:"
echo "   👉 Open: .env"
echo "   👉 Find: VITE_OPENAI_API_KEY=your_openai_api_key_here"
echo "   👉 Replace 'your_openai_api_key_here' with your actual key"
echo ""
echo "3. Restart the development server:"
echo "   👉 Stop the current server (Ctrl+C)"
echo "   👉 Run: npm run dev"
echo ""
echo "4. Test the AI features:"
echo "   👉 Go to Dashboard and click 'Analyze Portfolio'"
echo "   👉 Visit any asset page and click 'Analyze'"
echo "   👉 Use the chat to ask follow-up questions"
echo ""
echo "📖 For detailed documentation, see: AI_INTEGRATION.md"
echo ""
echo "💡 Tip: Start with small API key limits to test, then increase as needed"
echo ""
