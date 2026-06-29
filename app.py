import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# 1. Page Configuration
st.set_page_config(page_title="Gold Elite Terminal", layout="wide")
st.title("🥇 Gold Elite Professional Terminal")

# 2. Telegram Logic (ប្រើ Requests ធម្មតា មិនឱ្យរាំងស្ទះ App)
TELEGRAM_TOKEN = "8878257373:AAGE5_2shXyNOGRg8P3pjHL7npcB6-NZN20"
TELEGRAM_CHAT_ID = "@GOLDFXsignal" # បើមិនចេញសាកល្បងដាក់ ID លេខ

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
        requests.get(url, params=params, timeout=5)
    except Exception as e:
        st.sidebar.error(f"Telegram Error: {e}")

# 3. ទាញយក និងគណនាទិន្នន័យ
@st.cache_data(ttl=60)
def get_data(tf):
    period = "5d" if tf in ["15m", "30m"] else "1y"
    df = yf.download("GC=F", period=period, interval=tf)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    if len(df) < 20: 
        return pd.DataFrame()
    
    # គណនា Alligator
    alligator = ta.alligator(df['High'], df['Low'], df['Close'], 
                            jaw_period=13, jaw_shift=8, 
                            teeth_period=8, teeth_shift=5, 
                            lips_period=5, lips_shift=3)
    df = pd.concat([df, alligator], axis=1).dropna()
    return df

# 4. Sidebar & Data
timeframe = st.sidebar.selectbox("ជ្រើសរើស Timeframe:", ["15m", "30m", "1h", "4h", "1d"])
data = get_data(timeframe)

# 5. Logic សញ្ញា និង Chart
if data.empty:
    st.error("មិនមានទិន្នន័យ! សូមរង់ចាំបន្តិច...")
else:
    # បង្កើត Chart
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.7])
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Price"), row=1, col=1)
    
    # បង្ហាញសញ្ញាលើ Chart
    fig.add_trace(go.Scatter(x=data.index, y=data.iloc[:, -3], line=dict(color='blue', width=1), name="Jaws"), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data.iloc[:, -2], line=dict(color='red', width=1), name="Teeth"), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data.iloc[:, -1], line=dict(color='green', width=1), name="Lips"), row=1, col=1)

    # ពិនិត្យសញ្ញា BUY/SELL
    last_row = data.iloc[-1]
    lips = data.iloc[-1, -1]
    teeth = data.iloc[-1, -2]

    if 'last_signal' not in st.session_state:
        st.session_state.last_signal = None

    current_signal = "WAIT"
    if last_row['Close'] > lips > teeth:
        current_signal = "BUY"
    elif last_row['Close'] < lips < teeth:
        current_signal = "SELL"

    # ផ្ញើសារ
    if current_signal != "WAIT" and current_signal != st.session_state.last_signal:
        msg = f"🔔 Gold {current_signal} Detected!\nPrice: {last_row['Close']:.2f}"
        send_telegram_msg(msg)
        st.session_state.last_signal = current_signal
        st.success(f"Signal sent: {current_signal}")

    # Volume
    colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for index, row in data.iterrows()]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=colors, name="Volume"), row=2, col=1)

    fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, width='stretch')