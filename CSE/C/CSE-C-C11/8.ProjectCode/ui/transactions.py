"""Transaction management page: add/edit/delete/search/filter/sort."""
from __future__ import annotations

from datetime import date
import streamlit as st
import pandas as pd

from services.transaction_service import (
    add_transaction, update_transaction, delete_transaction, get_transactions, get_all_categories,
)
from ml.expense_classifier import predict_category, learn_from_correction
from utils.validators import is_valid_amount
from utils.helpers import format_currency
from services.data_import_service import load_and_validate, clean_and_prepare, commit_import


def render(user):
    st.title("💳 Transactions")

    tab_add, tab_view, tab_import = st.tabs(["Add Transaction", "View / Manage", "Import CSV/Excel"])

    with tab_add:
        _render_add_form(user)

    with tab_view:
        _render_transaction_list(user)

    with tab_import:
        _render_import(user)


def _render_import(user):
    st.write("Upload a CSV or Excel file with columns: **date, description, amount, category, type**. "
             "If category is missing, transactions are auto-categorized.")
    uploaded = st.file_uploader("Choose file", type=["csv", "xlsx", "xls"])
    if not uploaded:
        return

    df, errors = load_and_validate(uploaded)
    if errors:
        for e in errors:
            st.error(e)
        return

    cleaned_df, warnings = clean_and_prepare(df)
    for w in warnings:
        st.warning(w)

    if cleaned_df.empty:
        st.error("No valid rows found to import.")
        return

    st.write(f"**Preview ({len(cleaned_df)} valid rows ready to import):**")
    st.dataframe(cleaned_df, use_container_width=True, hide_index=True)

    if st.button("Confirm Import", type="primary"):
        count = commit_import(user.id, cleaned_df)
        st.success(f"Imported {count} transactions.")


def _render_add_form(user):
    categories = get_all_categories(user.id)
    with st.form("add_transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            txn_date = st.date_input("Date", value=date.today())
            description = st.text_input("Description", placeholder="e.g. Swiggy order")
            amount = st.number_input("Amount", min_value=0.0, step=10.0)
        with col2:
            transaction_type = st.selectbox("Type", ["expense", "income"])
            category_choice = st.selectbox("Category (leave as Auto-detect to let AI classify)",
                                            ["Auto-detect"] + categories + ["+ New category"])
            new_category = ""
            if category_choice == "+ New category":
                new_category = st.text_input("New category name")
            payment_method = st.selectbox("Payment Method", ["UPI", "Card", "Cash", "Bank Transfer", "Other"])
        notes = st.text_area("Notes (optional)", "")
        submitted = st.form_submit_button("Add Transaction", use_container_width=True)

    if submitted:
        if not description.strip():
            st.error("Please enter a description.")
            return
        if not is_valid_amount(amount):
            st.error("Please enter a valid amount greater than zero.")
            return

        if category_choice == "Auto-detect":
            category = predict_category(description)
            st.info(f"AI categorized this as **{category}**.")
        elif category_choice == "+ New category":
            if not new_category.strip():
                st.error("Please enter a name for the new category.")
                return
            category = new_category.strip()
        else:
            category = category_choice
            # Treat a manual category pick that differs from the model's own
            # prediction as a correction the model can learn from.
            predicted = predict_category(description)
            if predicted != category:
                history = [(t["description"], t["category"]) for t in get_transactions(user.id)]
                try:
                    learn_from_correction(description, category, history)
                except Exception:
                    pass  # learning is best-effort; never block adding the transaction

        try:
            add_transaction(user.id, txn_date, description, category, amount, transaction_type, payment_method, notes)
            st.success(f"{transaction_type.capitalize()} of {format_currency(amount)} added to {category}.")
        except ValueError as e:
            st.error(str(e))


def _render_transaction_list(user):
    categories = ["All"] + get_all_categories(user.id)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_date = st.date_input("From", value=None, key="filter_start")
    with col2:
        end_date = st.date_input("To", value=None, key="filter_end")
    with col3:
        category_filter = st.selectbox("Category", categories, key="filter_cat")
    with col4:
        type_filter = st.selectbox("Type", ["All", "income", "expense"], key="filter_type")

    search_term = st.text_input("Search description", "")

    rows = get_transactions(
        user.id,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None,
        category=category_filter,
        transaction_type=type_filter,
    )
    if search_term.strip():
        rows = [r for r in rows if search_term.strip().lower() in r["description"].lower()]

    if not rows:
        st.info("No transactions match your filters yet.")
        return

    df = pd.DataFrame(rows)
    sort_col = st.selectbox("Sort by", ["date", "amount", "category"], key="sort_col")
    ascending = st.checkbox("Ascending", value=False)
    df = df.sort_values(sort_col, ascending=ascending)

    display_df = df.copy()
    display_df["amount"] = display_df["amount"].apply(format_currency)
    st.dataframe(
        display_df[["id", "date", "description", "category", "amount", "transaction_type", "payment_method"]],
        use_container_width=True, hide_index=True,
    )

    st.divider()
    st.subheader("Edit or Delete a Transaction")
    txn_id = st.number_input("Transaction ID", min_value=0, step=1, value=0)
    if txn_id > 0:
        match = df[df["id"] == txn_id]
        if match.empty:
            st.warning("No transaction with that ID in the current filtered view.")
        else:
            row = match.iloc[0]
            col1, col2 = st.columns(2)
            with col1:
                new_desc = st.text_input("Description", value=row["description"], key="edit_desc")
                new_amount = st.number_input("Amount", min_value=0.0, value=float(row["amount"]) if isinstance(row["amount"], (int, float)) else 0.0, key="edit_amount")
            with col2:
                new_category = st.text_input("Category", value=row["category"], key="edit_cat")

            btn1, btn2 = st.columns(2)
            with btn1:
                if st.button("Save Changes", use_container_width=True):
                    update_transaction(user.id, int(txn_id), description=new_desc, amount=new_amount, category=new_category)
                    st.success("Transaction updated.")
                    st.rerun()
            with btn2:
                if st.button("Delete Transaction", type="primary", use_container_width=True):
                    if delete_transaction(user.id, int(txn_id)):
                        st.success("Transaction deleted.")
                        st.rerun()
                    else:
                        st.error("Could not delete that transaction.")
