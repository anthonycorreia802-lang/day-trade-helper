# Day Trade Helper

A Streamlit educational dashboard that shows delayed intraday market data, VWAP, EMA9, EMA20, RSI, volume, suggested stop/target levels, and a simple account-risk position size.

## Deploy on Streamlit Community Cloud

1. Open https://share.streamlit.io
2. Sign in with GitHub.
3. Choose **New app**.
4. Select repository `anthonycorreia802-lang/day-trade-helper`, branch `main`, and file `app.py`.
5. Click **Deploy**.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate the environment with `.venv\Scripts\activate`.

## Important

This application uses delayed free Yahoo Finance data and is for educational use only. It is not real-time, not financial advice, and does not guarantee results. Always paper trade and use appropriate risk controls.
