from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Company Performance Dashboard", page_icon="📊", layout="wide")

DATA_PATH = Path(__file__).parent / "data" / "company_performance_dataset.xlsx"

SALES_COLS = ["Date", "Branch", "Product", "Units Sold", "Unit Price (RWF)", "Unit Cost (RWF)",
              "Revenue (RWF)", "Total Cost (RWF)", "Profit (RWF)"]
FOREX_COLS = ["Date", "Currency", "Units Traded", "Buy Rate (RWF per unit)", "Sell Rate (RWF per unit)",
              "Cost (RWF)", "Revenue (RWF)", "Profit (RWF)"]


def rwf(x: float) -> str:
    return f"{x:,.0f}"


@st.cache_data(show_spinner="Loading data...")
def load_data(source):
    sales = pd.read_excel(source, sheet_name="Sales_Data", engine="openpyxl")
    forex = pd.read_excel(source, sheet_name="Forex_Trades", engine="openpyxl")
    missing = [c for c in SALES_COLS if c not in sales.columns] + \
              [c for c in FOREX_COLS if c not in forex.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    sales["Date"] = pd.to_datetime(sales["Date"])
    forex["Date"] = pd.to_datetime(forex["Date"])
    return sales, forex


# ---------- Sidebar ----------
st.sidebar.title("📊 Filters")
uploaded = st.sidebar.file_uploader("Upload your own Excel (optional)", type=["xlsx"])
try:
    sales, forex = load_data(uploaded if uploaded else DATA_PATH)
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

dmin = min(sales["Date"].min(), forex["Date"].min()).date()
dmax = max(sales["Date"].max(), forex["Date"].max()).date()
date_range = st.sidebar.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
else:
    start, end = dmin, dmax

branches = st.sidebar.multiselect("Branch", sorted(sales["Branch"].unique()), default=sorted(sales["Branch"].unique()))
products = st.sidebar.multiselect("Product", sorted(sales["Product"].unique()), default=sorted(sales["Product"].unique()))
currencies = st.sidebar.multiselect("Currency", sorted(forex["Currency"].unique()), default=sorted(forex["Currency"].unique()))

s = sales[(sales["Date"].dt.date >= start) & (sales["Date"].dt.date <= end)
          & sales["Branch"].isin(branches) & sales["Product"].isin(products)].copy()
f = forex[(forex["Date"].dt.date >= start) & (forex["Date"].dt.date <= end)
          & forex["Currency"].isin(currencies)].copy()

if s.empty and f.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# ---------- Header & KPIs ----------
st.title("Company Performance Dashboard (RWF)")
st.caption(f"Period: {start} to {end}")

s_rev, s_cost, s_profit = s["Revenue (RWF)"].sum(), s["Total Cost (RWF)"].sum(), s["Profit (RWF)"].sum()
f_cost, f_rev, f_profit = f["Cost (RWF)"].sum(), f["Revenue (RWF)"].sum(), f["Profit (RWF)"].sum()
total_profit = s_profit + f_profit
s_margin = s_profit / s_rev if s_rev else 0
f_return = f_profit / f_cost if f_cost else 0
f_share = f_profit / total_profit if total_profit else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Sales Revenue", rwf(s_rev))
c2.metric("Sales Profit", rwf(s_profit))
c3.metric("Sales Margin", f"{s_margin:.1%}")
c4.metric("Total Profit (Sales + Forex)", rwf(total_profit))
c5, c6, c7, c8 = st.columns(4)
c5.metric("Forex Cost (bought)", rwf(f_cost))
c6.metric("Forex Revenue (sold)", rwf(f_rev))
c7.metric("Forex Profit", rwf(f_profit))
c8.metric("Forex Return", f"{f_return:.2%}", f"{f_share:.1%} of total profit", delta_color="off")

tab_over, tab_sales, tab_forex, tab_calc, tab_data = st.tabs(
    ["Overview", "Sales", "Forex", "Forex Calculator", "Data"])

# ---------- Overview ----------
with tab_over:
    daily = (s.groupby("Date")[["Revenue (RWF)", "Profit (RWF)"]].sum()
             .rename(columns={"Revenue (RWF)": "Sales Revenue", "Profit (RWF)": "Sales Profit"})
             .join(f.groupby("Date")["Profit (RWF)"].sum().rename("Forex Profit"), how="outer")
             .fillna(0).sort_index())
    daily["Total Profit"] = daily["Sales Profit"] + daily["Forex Profit"]
    daily = daily.reset_index()

    st.subheader("Daily profit")
    fig = px.line(daily, x="Date", y=["Sales Profit", "Forex Profit", "Total Profit"],
                  labels={"value": "RWF", "variable": ""})
    st.plotly_chart(fig, width="stretch")

    st.subheader("Monthly performance")
    daily["Month"] = daily["Date"].dt.to_period("M").astype(str)
    monthly = daily.groupby("Month")[["Sales Revenue", "Sales Profit", "Forex Profit", "Total Profit"]].sum().reset_index()
    col_a, col_b = st.columns([3, 2])
    with col_a:
        fig = px.bar(monthly, x="Month", y=["Sales Profit", "Forex Profit"], barmode="stack",
                     labels={"value": "RWF", "variable": ""})
        st.plotly_chart(fig, width="stretch")
    with col_b:
        st.dataframe(monthly.style.format({c: "{:,.0f}" for c in monthly.columns[1:]}),
                     width="stretch", hide_index=True)

    st.subheader("Profit source")
    fig = px.pie(values=[s_profit, f_profit], names=["Sales", "Forex"], hole=0.5)
    st.plotly_chart(fig, width="stretch")

# ---------- Sales ----------
with tab_sales:
    col1, col2 = st.columns(2)
    by_branch = s.groupby("Branch")[["Revenue (RWF)", "Profit (RWF)"]].sum().reset_index()
    by_branch["Margin %"] = by_branch["Profit (RWF)"] / by_branch["Revenue (RWF)"]
    by_prod = s.groupby("Product")[["Revenue (RWF)", "Profit (RWF)"]].sum().reset_index()
    by_prod["Margin %"] = by_prod["Profit (RWF)"] / by_prod["Revenue (RWF)"]
    with col1:
        st.subheader("By branch")
        st.plotly_chart(px.bar(by_branch, x="Branch", y=["Revenue (RWF)", "Profit (RWF)"], barmode="group",
                               labels={"value": "RWF", "variable": ""}), width="stretch")
        st.dataframe(by_branch.style.format({"Revenue (RWF)": "{:,.0f}", "Profit (RWF)": "{:,.0f}", "Margin %": "{:.1%}"}),
                     width="stretch", hide_index=True)
    with col2:
        st.subheader("By product")
        st.plotly_chart(px.bar(by_prod, x="Product", y=["Revenue (RWF)", "Profit (RWF)"], barmode="group",
                               labels={"value": "RWF", "variable": ""}), width="stretch")
        st.dataframe(by_prod.style.format({"Revenue (RWF)": "{:,.0f}", "Profit (RWF)": "{:,.0f}", "Margin %": "{:.1%}"}),
                     width="stretch", hide_index=True)

    st.subheader("Revenue by branch and product")
    bp = s.groupby(["Branch", "Product"])["Revenue (RWF)"].sum().reset_index()
    st.plotly_chart(px.bar(bp, x="Branch", y="Revenue (RWF)", color="Product", barmode="stack"),
                    width="stretch")

    st.subheader("Weekday pattern (average daily revenue)")
    wd = s.groupby("Date")["Revenue (RWF)"].sum().reset_index()
    wd["Weekday"] = wd["Date"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    wd = wd.groupby("Weekday")["Revenue (RWF)"].mean().reindex(order).reset_index()
    st.plotly_chart(px.bar(wd, x="Weekday", y="Revenue (RWF)"), width="stretch")

# ---------- Forex ----------
with tab_forex:
    by_cur = f.groupby("Currency").agg(Trades=("Currency", "size"), Cost=("Cost (RWF)", "sum"),
                                       Revenue=("Revenue (RWF)", "sum"), Profit=("Profit (RWF)", "sum")).reset_index()
    by_cur["Return %"] = by_cur["Profit"] / by_cur["Cost"]
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Profit by currency")
        st.plotly_chart(px.bar(by_cur, x="Currency", y="Profit", labels={"Profit": "Profit (RWF)"}),
                        width="stretch")
    with col2:
        st.subheader("Return % by currency")
        st.plotly_chart(px.bar(by_cur, x="Currency", y="Return %"), width="stretch")
    st.dataframe(by_cur.style.format({"Cost": "{:,.0f}", "Revenue": "{:,.0f}", "Profit": "{:,.0f}", "Return %": "{:.2%}"}),
                 width="stretch", hide_index=True)

    st.subheader("Rates over time (buy vs sell)")
    cur = st.selectbox("Currency", sorted(f["Currency"].unique()))
    rates = f[f["Currency"] == cur].sort_values("Date")
    st.plotly_chart(px.line(rates, x="Date", y=["Buy Rate (RWF per unit)", "Sell Rate (RWF per unit)"],
                            labels={"value": "RWF per unit", "variable": ""}), width="stretch")

    n_loss = int((f["Profit (RWF)"] < 0).sum())
    st.info(f"Loss-making trades in selection: {n_loss} of {len(f)}")

# ---------- Forex calculator ----------
with tab_calc:
    st.subheader("How a forex trade makes (or loses) money")
    st.caption("Buy at the bid rate, sell at the ask rate. Change the values to test your own numbers.")
    cc1, cc2, cc3 = st.columns(3)
    units = cc1.number_input("Amount traded (units)", min_value=0.0, value=10000.0, step=100.0)
    buy = cc2.number_input("Buy rate (RWF per unit)", min_value=0.0, value=1440.0, step=1.0)
    sell = cc3.number_input("Sell rate (RWF per unit)", min_value=0.0, value=1455.0, step=1.0)
    cost, rev = units * buy, units * sell
    profit = rev - cost
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Cost", rwf(cost))
    r2.metric("Revenue", rwf(rev))
    r3.metric("Profit / Loss", rwf(profit))
    r4.metric("Return", f"{profit / cost:.2%}" if cost else "n/a")
    st.success("Profit") if profit > 0 else st.error("Loss") if profit < 0 else st.info("Break-even")

# ---------- Data ----------
with tab_data:
    st.subheader("Sales data")
    st.dataframe(s, width="stretch", hide_index=True)
    st.download_button("Download sales (CSV)", s.to_csv(index=False).encode(), "sales_filtered.csv", "text/csv")
    st.subheader("Forex trades")
    st.dataframe(f, width="stretch", hide_index=True)
    st.download_button("Download forex (CSV)", f.to_csv(index=False).encode(), "forex_filtered.csv", "text/csv")
