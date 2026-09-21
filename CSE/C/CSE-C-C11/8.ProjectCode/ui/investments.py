"""Investment portfolio management page."""
from __future__ import annotations

from datetime import date
import streamlit as st
import plotly.express as px
import pandas as pd

from services.investment_service import (
    add_investment, delete_investment, refresh_price, get_investments, portfolio_summary, ASSET_TYPES,
)
from utils.helpers import format_currency


def render(user):
    st.title("📈 Investments")

    with st.expander("➕ Add Investment"):
        with st.form("investment_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                asset_name = st.text_input("Asset Name", placeholder="e.g. Nifty 50 Index Fund")
                symbol = st.text_input("Ticker Symbol (optional, enables live price refresh)", placeholder="e.g. NIFTYBEES.NS")
                asset_type = st.selectbox("Asset Type", ASSET_TYPES)
            with col2:
                quantity = st.number_input("Quantity", min_value=0.0, step=1.0)
                purchase_price = st.number_input("Purchase Price (per unit)", min_value=0.0, step=1.0)
                current_price = st.number_input("Current Price (per unit, or leave 0 to use purchase price)", min_value=0.0, step=1.0)
            purchase_date = st.date_input("Purchase Date", value=date.today())
            submitted = st.form_submit_button("Add Investment")

        if submitted:
            if not asset_name.strip():
                st.error("Please enter an asset name.")
            elif quantity <= 0 or purchase_price <= 0:
                st.error("Quantity and purchase price must be greater than zero.")
            else:
                add_investment(user.id, asset_name, symbol, asset_type, quantity,
                                purchase_price, current_price, purchase_date)
                st.success(f"Added {asset_name} to your portfolio.")
                st.rerun()

    st.divider()
    summary = portfolio_summary(user.id)
    if not summary["holdings"]:
        st.info("No investments yet — add one above.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Invested", format_currency(summary["total_invested"]))
    c2.metric("Current Value", format_currency(summary["total_current_value"]))
    c3.metric("Profit / Loss", format_currency(summary["total_profit_loss"]))
    c4.metric("Return %", f"{summary['total_return_percent']:.2f}%")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(names=[h["asset_name"] for h in summary["holdings"]],
                      values=[h["current_value"] for h in summary["holdings"]],
                      title="Portfolio Allocation")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(x=[h["asset_name"] for h in summary["holdings"]],
                      y=[h["profit_loss"] for h in summary["holdings"]],
                      title="Profit / Loss by Asset", labels={"x": "Asset", "y": "P/L"})
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Holdings")
    for h in summary["holdings"]:
        with st.container(border=True):
            cols = st.columns([3, 1, 1, 1, 1, 1])
            cols[0].markdown(f"**{h['asset_name']}** ({h['asset_type']}){' — ' + h['symbol'] if h['symbol'] else ''}")
            cols[1].metric("Qty", h["quantity"])
            cols[2].metric("Invested", format_currency(h["invested_amount"]))
            cols[3].metric("Value", format_currency(h["current_value"]))
            cols[4].metric("P/L", format_currency(h["profit_loss"]), delta=f"{h['return_percent']:.1f}%")
            with cols[5]:
                if h["symbol"] and st.button("Refresh price", key=f"refresh_{h['id']}"):
                    ok, msg = refresh_price(user.id, h["id"])
                    (st.success if ok else st.warning)(msg)
                    if ok:
                        st.rerun()
                if st.button("Delete", key=f"del_inv_{h['id']}"):
                    delete_investment(user.id, h["id"])
                    st.rerun()

    st.caption("Note: predicted or historical returns are not guaranteed. Live prices depend on "
               "market-data availability and fall back to your manually entered price when offline.")
