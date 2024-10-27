import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import ta

# Page Config
st.set_page_config(page_title="Stock Analysis", page_icon="📈", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .stApp {background-color: #f0f2f6}
    .stock-header {
        font-size: 2rem;
        text-align: center;
        background: linear-gradient(90deg, #3a7bd5, #00d2ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

class StockAnalyzer:
    def __init__(self):
        self.exchange_map = {
            'NSE': '.NS',
            'BSE': '.BO',
            'NYSE': '',
            'LSE': '.L',
            'EUR': '.DE',
            'JPX': '.T',
            'HKEX': '.HK'
        }

    def get_stock_data(self, symbol, days):
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            stock = yf.Ticker(symbol)
            df = stock.history(start=start, end=end)
            
            if df.empty:
                return None, None, "No data found"
                
            # Add technical indicators
            df = self.add_indicators(df)
            info = stock.info
            
            return df, info, None
        except Exception as e:
            return None, None, f"Error: {str(e)}"
    
    def add_indicators(self, df):
        if df is not None and not df.empty:
            # Basic indicators
            df['SMA20'] = ta.trend.sma_indicator(df['Close'], 20)
            df['SMA50'] = ta.trend.sma_indicator(df['Close'], 50)
            df['RSI'] = ta.momentum.rsi(df['Close'])
            
            # MACD
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['Close'])
            df['BB_Upper'] = bb.bollinger_hband()
            df['BB_Lower'] = bb.bollinger_lband()
        return df

def create_chart(df, symbol):
    fig = make_subplots(rows=3, cols=1, 
                       shared_xaxes=True,
                       vertical_spacing=0.03,
                       row_heights=[0.6, 0.2, 0.2])
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name='OHLC'
    ), row=1, col=1)
    
    # Add moving averages
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name='SMA20', line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name='SMA50', line=dict(color='blue')), row=1, col=1)
    
    # Volume
    colors = ['red' if close < open else 'green' for open, close in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=colors), row=2, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    fig.update_layout(height=800, showlegend=True, xaxis_rangeslider_visible=False)
    return fig

def main():
    st.title("📈 Stock Market Analysis")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        exchange = st.selectbox("Exchange", 
            ["NSE", "BSE", "NYSE", "LSE", "EUR", "JPX", "HKEX"])
        
        symbol = st.text_input("Stock Symbol", "RELIANCE").upper()
        if exchange != "NYSE":  # Add exchange suffix
            symbol += StockAnalyzer().exchange_map[exchange]
            
        timeframe = st.selectbox("Timeframe", 
            ["1M", "3M", "6M", "1Y"], 
            format_func=lambda x: {"1M": "1 Month", "3M": "3 Months", 
                                 "6M": "6 Months", "1Y": "1 Year"}[x])
        
        days = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}[timeframe]
    
    # Main content
    if st.button("Analyze", use_container_width=True):
        with st.spinner("Analyzing..."):
            analyzer = StockAnalyzer()
            df, info, error = analyzer.get_stock_data(symbol, days)
            
            if error:
                st.error(error)
            elif df is not None:
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                current_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                change = ((current_price - prev_price) / prev_price) * 100
                
                with col1:
                    st.metric("Price", f"₹{current_price:.2f}", f"{change:+.2f}%")
                with col2:
                    st.metric("Volume", f"{df['Volume'].iloc[-1]:,.0f}")
                with col3:
                    st.metric("RSI", f"{df['RSI'].iloc[-1]:.1f}")
                with col4:
                    high = df['High'].max()
                    low = df['Low'].min()
                    st.metric("Range", f"₹{high:.2f} - ₹{low:.2f}")
                
                # Display chart
                st.plotly_chart(create_chart(df, symbol), use_container_width=True)
                
                # Export data
                if st.button("Download Data"):
                    st.download_button(
                        "Download CSV",
                        df.to_csv().encode('utf-8'),
                        f"{symbol}_analysis.csv",
                        "text/csv"
                    )
    
    st.markdown("<div style='text-align:center'>Made with ❤️ by Viraj P.</div>", 
                unsafe_allow_html=True)

if __name__ == "__main__":
    main()