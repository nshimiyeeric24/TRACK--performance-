# Company Performance Dashboard (RWF)

Interactive Streamlit dashboard built from `data/company_performance_dataset.xlsx`
(Sales and Forex trading, 1 Aug – 31 Oct 2026, amounts in Rwandan Francs).

## Features
- Sidebar filters: date range, branch, product, currency
- KPIs: sales revenue/profit/margin, forex profit/return, total profit
- Daily and monthly trends, branch/product breakdowns, forex by currency
- Forex trade calculator (buy low, sell high)
- Filtered data tables with CSV download
- Optional: upload your own Excel file with the same sheet layout

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push this repository to GitHub.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app** → choose the repo, branch `main`, main file `app.py`.
4. Click **Deploy**.

## Repository structure
```
.
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/config.toml
└── data/company_performance_dataset.xlsx
```

## Using your own data
Keep sheets `Sales_Data` and `Forex_Trades` with the same column names, then
either replace the file in `data/` or upload it in the app sidebar.
