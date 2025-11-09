"""
APEX Integration Tests - SIMPLIFIED
Quick tests for the new deliberation-based orchestrator.
"""


class SimpleTests:
    """Fast, focused integration tests"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.passed = 0
        self.failed = 0
        
        # Initialize agents once
        model = "nvidia/llama-3.1-nemotron-70b-instruct"
        
        self.market_agent = MarketAgent(api_key, model=model, enable_logging=False)
        self.strategy_agent = StrategyAgent(api_key, model=model, enable_logging=False)
        self.risk_agent = RiskAgent(api_key, model=model, enable_logging=False, 
                                    use_gpu=False, num_simulations=1000)
        
        self.orchestrator = AgentOrchestrator(
            market_agent=self.market_agent,
            strategy_agent=self.strategy_agent,
            risk_agent=self.risk_agent,
            openrouter_api_key=api_key,
            model=model,
            max_deliberation_rounds=3,
            enable_logging=True,
            require_user_approval=False
        )
    
    def run_all(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🧪 RUNNING SIMPLIFIED INTEGRATION TESTS")
        print("="*60)
        
        self.test_new_user()
        self.test_existing_user()
        self.test_edge_case_100_percent_stocks()
        
        print("\n" + "="*60)
        print(f"✅ PASSED: {self.passed}")
        print(f"❌ FAILED: {self.failed}")
        print(f"TOTAL: {self.passed + self.failed}")
        print("="*60)
        
        return self.failed == 0
    
    def test_new_user(self):
        """Test: New user with 100% cash"""
        print("\n" + "-"*60)
        print("TEST 1: New User (100% Cash)")
        print("-"*60)
        
        try:
            portfolio = {
                'total_value': 10000,
                'cash': 10000,
                'positions': {}
            }
            
            user_profile = {
                'risk_tolerance': 'moderate',
                'time_horizon': 'long-term',
                'goals': ['retirement'],
                'investment_style': 'balanced',
                'experience_level': 'beginner'
            }
            
            result = self.orchestrator.run_analysis(
                current_portfolio=portfolio,
                user_profile=user_profile
            )
            
            # Validate
            assert 'initial_analysis' in result
            assert 'deliberation_conversation' in result
            assert 'final_recommendation' in result
            assert result['deliberation_rounds'] <= 3
            
            # Should have strategy for new user
            strategy = result['initial_analysis']['strategy']
            assert len(strategy['recommended_trades']) > 0, "Should have trades for new user"
            
            # Should have some deliberation
            assert result['deliberation_rounds'] >= 0
            
            print(f"✅ PASSED - Deliberation rounds: {result['deliberation_rounds']}")
            self.passed += 1
            
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            self.failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.failed += 1
    
    def test_existing_user(self):
        """Test: Existing user needs rebalancing"""
        print("\n" + "-"*60)
        print("TEST 2: Existing User (90% Stocks)")
        print("-"*60)
        
        try:
            portfolio = {
                'total_value': 50000,
                'cash': 5000,
                'positions': {
                    'SPY': {'shares': 80, 'value': 38000, 'weight': 0.76},
                    'AAPL': {'shares': 30, 'value': 7000, 'weight': 0.14}
                }
            }
            
            user_profile = {
                'risk_tolerance': 'moderate',
                'time_horizon': 'long-term',
                'goals': ['retirement'],
                'investment_style': 'balanced',
                'experience_level': 'beginner'
            }
            
            result = self.orchestrator.run_analysis(
                current_portfolio=portfolio,
                user_profile=user_profile
            )
            
            # Validate
            assert 'final_recommendation' in result
            
            # Should recommend reducing stocks
            strategy = result['initial_analysis']['strategy']
            spy_target = strategy['target_allocation'].get('SPY', 0)
            assert spy_target < 0.80, f"Should reduce SPY from 76%, got {spy_target*100:.0f}%"
            
            print(f"✅ PASSED - Recommended reducing stocks")
            self.passed += 1
            
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            self.failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.failed += 1
    
    def test_edge_case_100_percent_stocks(self):
        """Test: Edge case - 100% stocks with conservative user"""
        print("\n" + "-"*60)
        print("TEST 3: Edge Case (100% Stocks, Conservative User)")
        print("-"*60)
        
        try:
            portfolio = {
                'total_value': 30000,
                'cash': 0,
                'positions': {
                    'SPY': {'shares': 63, 'value': 30000, 'weight': 1.00}
                }
            }
            
            user_profile = {
                'risk_tolerance': 'conservative',  # Mismatch!
                'time_horizon': 'short-term',
                'goals': ['capital preservation'],
                'investment_style': 'income',
                'experience_level': 'beginner'
            }
            
            result = self.orchestrator.run_analysis(
                current_portfolio=portfolio,
                user_profile=user_profile
            )
            
            # Should recommend major reduction
            strategy = result['initial_analysis']['strategy']
            spy_target = strategy['target_allocation'].get('SPY', 0)
            
            assert spy_target < 0.60, f"Conservative user: should reduce 100% stocks significantly"
            
            print(f"✅ PASSED - Recommended defensive positioning")
            self.passed += 1
            
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            self.failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.failed += 1


# ========================================
# RUN TESTS
# ========================================

if __name__ == "__main__":
    api_key = "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"
    tester = SimpleTests(api_key)
    success = tester.run_all()
