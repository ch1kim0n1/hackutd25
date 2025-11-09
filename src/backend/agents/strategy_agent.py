"""
APEX Market Agent - NVIDIA 70B Edition (RECOMMENDED)
Uses NVIDIA Llama 3.1 Nemotron 70B - beats GPT-4o on benchmarks
"""


class MarketAgent:
    """
    Market scanning and analysis agent using NVIDIA's flagship 70B model.
    
    This model OUTPERFORMS GPT-4o and Claude 3.5 Sonnet on alignment benchmarks.
    Perfect for impressing hackathon judges while costing ~$0.50 total.
    """
    
    def __init__(
        self,
        openrouter_api_key: str,
        enable_logging: bool = True,
        model: str = "nvidia/llama-3.1-nemotron-70b-instruct"  # 🎯 THE GOOD ONE
    ):
        """
        Initialize Market Agent with OpenRouter API.
        
        Args:
            openrouter_api_key: API key from openrouter.ai
            enable_logging: Print status messages
            model: NVIDIA model selection
                   RECOMMENDED: "nvidia/llama-3.1-nemotron-70b-instruct" ($0.60/M)
                   Budget option: "nvidia/nemotron-nano-9b-v2:free" (FREE but weaker)
                   Balanced: "nvidia/llama-3.3-nemotron-super-49b-v1.5" ($0.80/M)
        """
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )
        
        self.model = model
        self.logging_enabled = enable_logging
        
        # RSS feeds for financial news
        self.news_feeds = [
            'https://feeds.finance.yahoo.com/rss/2.0/headline',
            'https://www.cnbc.com/id/100003114/device/rss/rss.html',
            'https://feeds.marketwatch.com/marketwatch/topstories/',
        ]
        
        self.previous_state = {
            'vix': None,
            'spy_price': None,
            'last_scan_time': None
        }
        
        self.cache = {
            'market_data': None,
            'cache_time': None,
            'cache_duration': 300
        }
        
        # Log model info
        model_display = self._get_model_display_name()
        self.log(f"✅ Initialized with {model_display}")
        if '70b' in model.lower():
            self.log(f"💎 Using flagship 70B model - beats GPT-4o on benchmarks!")
    
    def _get_model_display_name(self) -> str:
        """Get human-readable model name"""
        if '70b' in self.model.lower():
            return "NVIDIA Llama 3.1 Nemotron 70B (Flagship)"
        elif '49b' in self.model.lower():
            return "NVIDIA Nemotron Super 49B (Balanced)"
        elif '9b' in self.model.lower():
            return "NVIDIA Nemotron Nano 9B (Budget)"
        else:
            return self.model
    
    def log(self, message: str):
        """Print status message if logging enabled"""
        if self.logging_enabled:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 🔍 Market Agent: {message}")
    
    # ========================================
    # MAIN SCANNING FUNCTION
    # ========================================
    
    def scan_market(self, use_cache: bool = True) -> Dict:
        """
        Main function: Scan market conditions and generate analysis.
        
        Returns comprehensive market report with NVIDIA AI analysis.
        """
        self.log("Starting market scan...")
        
        if use_cache and self._is_cache_valid():
            self.log("📦 Using cached data")
            return self._get_cached_report()
        
        # 1. Fetch market data
        market_data = self._fetch_market_data()
        
        # 2. Fetch news
        news_summary = self._fetch_news_rss()
        
        # 3. Detect anomalies
        alerts = self._detect_anomalies(market_data)
        
        # 4. Synthesize with NVIDIA 70B
        self.log(f"🤖 Analyzing with NVIDIA {self._get_model_display_name()}...")
        analysis = self._synthesize_with_nvidia(market_data, news_summary, alerts)
        
        report = {
            'market_data': market_data,
            'news_summary': news_summary,
            'alerts': alerts,
            'analysis': analysis,
            'timestamp': datetime.now(),
            'model_used': self.model
        }
        
        self._update_cache(report)
        
        self.previous_state.update({
            'vix': market_data['vix'],
            'spy_price': market_data['spy_price'],
            'last_scan_time': datetime.now()
        })
        
        self.log("✅ Market scan complete")
        return report
    
    def _fetch_market_data(self) -> Dict:
        """Fetch current market indicators using yfinance"""
        self.log("📊 Fetching real-time market data...")
        
        try:
            spy = yf.download('SPY', period='5d', interval='1d', progress=False)
            spy_current = spy['Close'].iloc[-1]
            spy_previous = spy['Close'].iloc[-2]
            spy_change_pct = ((spy_current / spy_previous) - 1) * 100
            
            vix = yf.download('^VIX', period='5d', interval='1d', progress=False)
            current_vix = vix['Close'].iloc[-1]
            
            vix_change = 0
            if self.previous_state['vix'] is not None:
                vix_change = current_vix - self.previous_state['vix']
            
            avg_volume = spy['Volume'].iloc[:-1].mean()
            today_volume = spy['Volume'].iloc[-1]
            volume_ratio = today_volume / avg_volume
            
            market_open = self._is_market_open()
            
            return {
                'spy_price': float(spy_current),
                'spy_change_pct': float(spy_change_pct),
                'spy_previous': float(spy_previous),
                'vix': float(current_vix),
                'vix_change': float(vix_change),
                'volume_ratio': float(volume_ratio),
                'market_open': market_open,
                'data_timestamp': datetime.now()
            }
            
        except Exception as e:
            self.log(f"❌ Error: {e}")
            return self._get_mock_market_data()
    
    def _fetch_news_rss(self) -> Dict:
        """Fetch financial news from RSS feeds"""
        self.log("📰 Fetching financial news...")
        
        headlines = []
        
        try:
            for feed_url in self.news_feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    
                    for entry in feed.entries[:3]:
                        published = datetime.now()
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published = datetime(*entry.published_parsed[:6])
                        
                        headlines.append({
                            'title': entry.title,
                            'source': feed.feed.title if hasattr(feed.feed, 'title') else 'Financial News',
                            'published': published.isoformat(),
                            'url': entry.link if hasattr(entry, 'link') else '#'
                        })
                except:
                    continue
            
            headlines.sort(key=lambda x: x['published'], reverse=True)
            
            return {
                'headlines': headlines[:10],
                'total_articles': len(headlines),
                'fetch_timestamp': datetime.now()
            }
            
        except Exception as e:
            self.log(f"❌ Error: {e}")
            return self._get_mock_news()
    
    def _detect_anomalies(self, market_data: Dict) -> List[str]:
        """Detect unusual market conditions"""
        alerts = []
        
        if market_data['vix'] > 30:
            alerts.append("🚨 EXTREME FEAR: VIX above 30 - market panic")
        elif market_data['vix'] > 20:
            alerts.append("⚠️ ELEVATED VOLATILITY: VIX above 20")
        elif market_data['vix_change'] > 5:
            alerts.append(f"📈 VIX SPIKE: +{market_data['vix_change']:.1f} points")
        
        spy_change = market_data['spy_change_pct']
        if abs(spy_change) > 2:
            direction = "📉 DOWN" if spy_change < 0 else "📈 UP"
            alerts.append(f"{direction} BIG MOVE: SPY {spy_change:+.1f}%")
        elif abs(spy_change) > 1:
            alerts.append(f"📊 NOTABLE: SPY {spy_change:+.1f}%")
        
        if market_data['volume_ratio'] > 1.5:
            alerts.append(f"💹 HIGH VOLUME: {market_data['volume_ratio']:.1f}x avg")
        
        if not alerts:
            alerts.append("✅ STABLE: Normal market activity")
        
        return alerts
    
    def _synthesize_with_nvidia(
        self,
        market_data: Dict,
        news: Dict,
        alerts: List[str]
    ) -> str:
        """Use NVIDIA 70B to synthesize market analysis"""
        
        prompt = self._build_synthesis_prompt(market_data, news, alerts)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are the Market Analysis Agent in APEX, a professional multi-agent investment system. Provide expert-level market analysis with clear, actionable insights for institutional investors."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,  # More tokens for 70B's detailed analysis
                temperature=0.6,  # Slightly lower for more focused output
                extra_headers={
                    "HTTP-Referer": "https://apex-financial.com",
                    "X-Title": "APEX Market Agent"
                }
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.log(f"❌ API Error: {e}")
            return self._generate_fallback_analysis(market_data, alerts)
    
    def _build_synthesis_prompt(
        self,
        market_data: Dict,
        news: Dict,
        alerts: List[str]
    ) -> str:
        """Build comprehensive prompt for 70B model"""
        
        headlines_text = "\n".join([
            f"- {h['title']} ({h['source']})"
            for h in news['headlines'][:5]
        ])
        
        alerts_text = "\n".join(alerts)
        
        prompt = f"""Analyze current market conditions for institutional-grade investment decisions.

**MARKET DATA ({market_data['data_timestamp'].strftime('%I:%M %p')} ET):**
- S&P 500 (SPY): ${market_data['spy_price']:.2f} ({market_data['spy_change_pct']:+.2f}% today)
- VIX (Volatility): {market_data['vix']:.1f} ({market_data['vix_change']:+.1f} change)
- Trading Volume: {market_data['volume_ratio']:.2f}x average
- Market Status: {'OPEN' if market_data['market_open'] else 'CLOSED'}

**DETECTED ANOMALIES:**
{alerts_text}

**BREAKING FINANCIAL NEWS:**
{headlines_text if headlines_text else "No major headlines"}

**ANALYSIS FRAMEWORK:**
Provide a structured institutional-grade assessment:

**Market Condition:** [Bullish/Bearish/Neutral/Volatile/Mixed] with conviction level
**Risk Level:** [Low/Medium/High/Extreme] with quantified reasoning
**Key Insight:** 2-3 sentences synthesizing the macro environment, technical signals, and news catalysts
**Strategic Recommendation:** Specific, actionable guidance for the Strategy Agent on position sizing, sector allocation, and risk management

Focus on: correlation between VIX and equity movements, volume patterns signaling institutional activity, and news impact on forward guidance."""

        return prompt
    
    def _is_market_open(self) -> bool:
        """Check if market is open"""
        now = datetime.now()
        if now.weekday() >= 5:
            return False
        market_open = now.replace(hour=9, minute=30, second=0)
        market_close = now.replace(hour=16, minute=0, second=0)
        return market_open <= now <= market_close
    
    def _is_cache_valid(self) -> bool:
        """Check cache validity"""
        if self.cache['cache_time'] is None:
            return False
        elapsed = (datetime.now() - self.cache['cache_time']).total_seconds()
        return elapsed < self.cache['cache_duration']
    
    def _get_cached_report(self) -> Dict:
        return self.cache['market_data']
    
    def _update_cache(self, report: Dict):
        self.cache['market_data'] = report
        self.cache['cache_time'] = datetime.now()
    
    def _get_mock_market_data(self) -> Dict:
        return {
            'spy_price': 475.32,
            'spy_change_pct': -0.82,
            'spy_previous': 479.25,
            'vix': 18.5,
            'vix_change': 2.1,
            'volume_ratio': 1.15,
            'market_open': True,
            'data_timestamp': datetime.now()
        }
    
    def _get_mock_news(self) -> Dict:
        return {
            'headlines': [
                {
                    'title': 'Fed signals data-dependent approach to rate cuts',
                    'source': 'Reuters',
                    'published': datetime.now().isoformat(),
                    'url': '#'
                }
            ],
            'total_articles': 1,
            'fetch_timestamp': datetime.now()
        }
    
    def _generate_fallback_analysis(self, market_data: Dict, alerts: List[str]) -> str:
        """Fallback if API fails"""
        spy_change = market_data['spy_change_pct']
        vix = market_data['vix']
        
        if spy_change < -1.5:
            condition = "Bearish"
            risk = "High"
        elif spy_change > 1.5:
            condition = "Bullish"
            risk = "Medium"
        elif vix > 25:
            condition = "Volatile"
            risk = "High"
        else:
            condition = "Neutral"
            risk = "Medium"
        
        return f"""**Market Condition:** {condition}
**Risk Level:** {risk}
**Key Insight:** SPY {spy_change:+.1f}%, VIX at {vix:.1f}. {alerts[0]}
**Strategic Recommendation:** {'Defensive positioning advised' if risk == 'High' else 'Maintain balanced allocations'}"""
    
    def get_formatted_report(self, report: Dict = None) -> str:
        """Format report for display"""
        if report is None:
            report = self.scan_market()
        
        data = report['market_data']
        model_name = self._get_model_display_name()
        
        output = f"""
╔════════════════════════════════════════════════╗
║     🔍 APEX MARKET AGENT (NVIDIA AI)          ║
╚════════════════════════════════════════════════╝

⏰ Scan Time: {report['timestamp'].strftime('%I:%M:%S %p')}
🤖 AI Model: {model_name}

📊 MARKET SNAPSHOT:
   S&P 500:  ${data['spy_price']:.2f} ({data['spy_change_pct']:+.2f}%)
   VIX:      {data['vix']:.1f} ({data['vix_change']:+.1f})
   Volume:   {data['volume_ratio']:.2f}x average
   Status:   {'🟢 OPEN' if data['market_open'] else '🔴 CLOSED'}

🚨 ALERTS:
"""
        for alert in report['alerts']:
            output += f"   {alert}\n"
        
        output += f"""
📰 HEADLINES:
"""
        for h in report['news_summary']['headlines'][:3]:
            output += f"   • {h['title'][:70]}\n"
        
        output += f"""
💎 NVIDIA {model_name.upper()} ANALYSIS:
{report['analysis']}

════════════════════════════════════════════════
"""
        return output


# ========================================
# USAGE
# ========================================

if __name__ == "__main__":
    agent = MarketAgent(
        openrouter_api_key="YOUR_KEY_HERE",
        model="nvidia/llama-3.1-nemotron-70b-instruct"  # 🎯 THE FLAGSHIP
    )
    
    print("\n🚀 Running market analysis with NVIDIA's flagship 70B model...\n")
    report = agent.scan_market()
    print(agent.get_formatted_report(report))
    
    print(f"\n💰 Cost estimate: ~$0.0006 per scan (~$0.50 for entire hackathon)")
    print(f"🏆 This model beats GPT-4o on Arena Hard (85.0 vs 79.3)")
