"""
Stock Analysis Script with AI Agent Integration

This script fetches stock price data for a 2-month period and sends it to AI agents for analysis.
It handles market closures by using the nearest previous trading day.
"""

import yfinance as yf
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import os
import sys


def get_stock_symbol():
    """
    Ask the user to input a stock symbol.
    
    Returns:
        str: The stock symbol entered by the user (uppercase)
    """
    while True:
        symbol = input("Enter stock symbol (e.g., AAPL, TSLA, SPY): ").strip().upper()
        if symbol:
            return symbol
        print("Please enter a valid stock symbol.")


def get_end_date():
    """
    Ask the user to input an end date in YYYY-MM-DD format.
    Validates the date format and ensures it's not in the future.
    
    Returns:
        datetime: The validated end date
    """
    while True:
        date_str = input("Enter end date (YYYY-MM-DD): ").strip()
        try:
            end_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Check if date is in the future
            if end_date > datetime.now():
                print("Error: End date cannot be in the future. Please try again.")
                continue
                
            return end_date
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD format.")


def calculate_start_date(end_date):
    """
    Calculate the start date exactly 2 months before the end date.
    
    Args:
        end_date (datetime): The end date
        
    Returns:
        datetime: The start date (2 months before end_date)
    """
    # Use relativedelta to subtract exactly 2 months
    start_date = end_date - relativedelta(months=2)
    return start_date


def get_closing_price(symbol, target_date):
    """
    Get the closing price of a stock on a specific date.
    If the market is closed on that date, uses the nearest previous trading day.
    
    Args:
        symbol (str): Stock symbol
        target_date (datetime): The target date
        
    Returns:
        tuple: (actual_date, closing_price) - The actual trading date and closing price
    """
    # Create a date range: fetch up to 10 days before target_date to ensure we get data
    # even if there are holidays or weekends
    start_fetch = target_date - timedelta(days=10)
    end_fetch = target_date + timedelta(days=1)  # Include target_date
    
    # Download stock data
    stock = yf.Ticker(symbol)
    hist = stock.history(
        start=start_fetch.strftime("%Y-%m-%d"),
        end=end_fetch.strftime("%Y-%m-%d")
    )
    
    # Check if we got any data
    if hist.empty:
        raise ValueError(f"No data found for {symbol}. Please check the symbol and try again.")
    
    # Find the closest trading day on or before the target date
    hist = hist[hist.index <= target_date]
    
    if hist.empty:
        raise ValueError(f"No trading data available on or before {target_date.strftime('%Y-%m-%d')}")
    
    # Get the last (most recent) trading day on or before target_date
    actual_date = hist.index[-1]
    closing_price = hist['Close'].iloc[-1]
    
    return actual_date, closing_price


def send_to_ai_agents(stock_data):
    """
    Send stock analysis data to the AI agents orchestrator.
    
    This function prepares the data and sends it to the agent system for analysis.
    The agents will debate and analyze the stock performance.
    
    Args:
        stock_data (dict): Dictionary containing stock analysis data
    """
    print("\n" + "="*60)
    print("SENDING DATA TO AI AGENTS")
    print("="*60)
    
    # Format the data for the agents
    agent_message = {
        "type": "stock_analysis_request",
        "timestamp": datetime.now().isoformat(),
        "data": stock_data,
        "request": {
            "market_agent": "Analyze market sentiment and trends for this stock",
            "strategy_agent": "Evaluate investment opportunity based on 2-month performance",
            "risk_agent": "Assess risk factors and volatility",
            "explainer_agent": "Provide user-friendly explanation of findings"
        }
    }
    
    # Pretty print the data being sent to agents
    print(json.dumps(agent_message, indent=2))
    
    # TODO: Integrate with actual agent orchestrator when implemented
    # For now, save to a file that agents can pick up
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "mock-data")
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"stock_analysis_{stock_data['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(output_file, 'w') as f:
        json.dump(agent_message, f, indent=2)
    
    print(f"\n✓ Data saved to: {output_file}")
    print("✓ Ready for AI agent processing")
    print("="*60)


def calculate_performance(start_price, end_price):
    """
    Calculate the performance metrics for the stock.
    
    Args:
        start_price (float): Starting price
        end_price (float): Ending price
        
    Returns:
        dict: Performance metrics
    """
    absolute_change = end_price - start_price
    percent_change = ((end_price - start_price) / start_price) * 100
    
    return {
        "absolute_change": round(absolute_change, 2),
        "percent_change": round(percent_change, 2)
    }


def main():
    """
    Main function that orchestrates the stock analysis workflow.
    """
    print("="*60)
    print("STOCK ANALYSIS TOOL - 2 MONTH PERFORMANCE")
    print("="*60)
    print()
    
    try:
        # Step 1: Get stock symbol from user
        symbol = get_stock_symbol()
        print(f"✓ Selected stock: {symbol}\n")
        
        # Step 2: Get end date from user
        end_date = get_end_date()
        print(f"✓ End date: {end_date.strftime('%Y-%m-%d')}\n")
        
        # Step 3: Calculate start date (2 months before end date)
        start_date = calculate_start_date(end_date)
        print(f"✓ Start date (2 months prior): {start_date.strftime('%Y-%m-%d')}\n")
        
        print("Fetching stock data from Yahoo Finance...")
        print("-" * 60)
        
        # Step 4: Get closing price on start date
        actual_start_date, start_price = get_closing_price(symbol, start_date)
        print(f"✓ Start Date: {actual_start_date.strftime('%Y-%m-%d')}")
        print(f"  Closing Price: ${start_price:.2f}")
        
        # Step 5: Get closing price on end date
        actual_end_date, end_price = get_closing_price(symbol, end_date)
        print(f"✓ End Date: {actual_end_date.strftime('%Y-%m-%d')}")
        print(f"  Closing Price: ${end_price:.2f}")
        
        # Calculate performance metrics
        performance = calculate_performance(start_price, end_price)
        
        print("\n" + "-" * 60)
        print("PERFORMANCE SUMMARY")
        print("-" * 60)
        print(f"Absolute Change: ${performance['absolute_change']:.2f}")
        print(f"Percent Change: {performance['percent_change']:.2f}%")
        
        if performance['percent_change'] > 0:
            print(f"📈 Stock is UP over the 2-month period")
        elif performance['percent_change'] < 0:
            print(f"📉 Stock is DOWN over the 2-month period")
        else:
            print(f"➡️  Stock is FLAT over the 2-month period")
        
        # Prepare data package for AI agents
        stock_data = {
            "symbol": symbol,
            "start_date": actual_start_date.strftime('%Y-%m-%d'),
            "start_price": round(start_price, 2),
            "end_date": actual_end_date.strftime('%Y-%m-%d'),
            "end_price": round(end_price, 2),
            "performance": performance,
            "period_days": (actual_end_date - actual_start_date).days
        }
        
        # Step 6: Send data to AI agents for analysis
        send_to_ai_agents(stock_data)
        
        print("\n✅ Analysis complete!")
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
