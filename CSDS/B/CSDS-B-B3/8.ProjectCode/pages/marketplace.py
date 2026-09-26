"""KnowledgeX AI - Learn & Earn Marketplace"""
import streamlit as st

from database.models import StudentProfile, Resource
from services.marketplace_service import (
    list_resources, get_author_name, purchase_resource, get_purchase_history,
    get_seller_dashboard, upload_resource, has_purchased, get_wallet_profile,
)
from services.gamification_service import award_xp, grant_badge

CATEGORIES = ["All", "Notes", "Projects", "Interview Prep", "Courses", "Cheat Sheets", "Practice Questions",
              "Coding Templates"]
RESOURCE_TYPES = ["Notes", "Study Material", "Project Report", "Coding Template",
                   "Interview Preparation Material", "Course", "Cheat Sheet",
                   "Practice Questions", "Mini Project"]


def render(session, user):
    st.title("🛍️ Learn & Earn Marketplace")
    st.caption("Buy and sell notes, projects, courses and more. Payments are simulated using your in-app wallet.")

    wallet_profile = get_wallet_profile(session, user)

    tabs = st.tabs(["🏬 Browse", "🛒 My Purchases", "📤 Upload Resource", "💼 Seller Dashboard"])

    # ---------------- Browse ----------------
    with tabs[0]:
        c1, c2, c3 = st.columns([2, 1, 1])
        search = c1.text_input("Search resources", placeholder="e.g. Machine Learning notes")
        category = c2.selectbox("Category", CATEGORIES)
        only_free = c3.checkbox("Free only")

        resources = list_resources(session, category=category, search=search, only_free=only_free)
        if wallet_profile:
            st.caption(f"Wallet balance: ₹{wallet_profile.wallet_balance:.0f}")

        if not resources:
            st.info("No resources match your filters.")
        for r in resources:
            with st.container(border=True):
                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"**{r.title}**  \n{r.description}")
                    st.caption(f"By {get_author_name(session, r.author_id)} • {r.resource_type} • "
                              f"⭐ {r.rating} ({r.rating_count}) • ⬇ {r.downloads} downloads • "
                              f"Tags: {r.skill_tags}")
                with cols[1]:
                    price_label = "FREE" if r.price == 0 else f"₹{r.price:.0f}"
                    st.markdown(f"### {price_label}")
                    already_owned = has_purchased(session, user.id, r.id)
                    if already_owned:
                        st.success("Owned ✓")
                    elif st.button("Get Resource", key=f"buy_{r.id}", use_container_width=True):
                        success, msg = purchase_resource(session, user, r)
                        if success:
                            award_xp(session, user.id, "resource_purchased")
                            session.commit()
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    # ---------------- My Purchases ----------------
    with tabs[1]:
        history = get_purchase_history(session, user.id)
        if not history:
            st.info("You haven't purchased or claimed any resources yet.")
        for item in history:
            r = item["resource"]
            with st.container(border=True):
                st.markdown(f"**{r.title}** — {r.resource_type}")
                st.caption(f"Purchased: {item['purchase'].purchased_at.strftime('%Y-%m-%d')} • "
                          f"Paid: ₹{item['purchase'].price_paid:.0f}")
                st.markdown(r.description)

    # ---------------- Upload ----------------
    with tabs[2]:
        st.subheader("Share & Monetize Your Knowledge")
        with st.form("upload_resource_form"):
            title = st.text_input("Title")
            description = st.text_area("Description")
            category = st.selectbox("Category", CATEGORIES[1:])
            rtype = st.selectbox("Resource Type", RESOURCE_TYPES)
            price = st.number_input("Price (₹, 0 = Free)", min_value=0, max_value=5000, value=0, step=10)
            tags = st.text_input("Skill Tags (comma separated)", placeholder="Python, Machine Learning")
            uploaded_file = st.file_uploader("Attach file (optional, for demo purposes)")
            submit = st.form_submit_button("Publish to Marketplace", type="primary")

        if submit:
            if not title or not description:
                st.error("Title and description are required.")
            else:
                upload_resource(session, user, title, description, category, rtype, price, tags)
                award_xp(session, user.id, "resource_uploaded")
                if price > 0:
                    grant_badge(session, user.id, "Knowledge Seller", "Published a paid resource")
                else:
                    grant_badge(session, user.id, "Knowledge Sharer", "Shared a free resource")
                session.commit()
                st.success(f"'{title}' has been published to the marketplace!")

    # ---------------- Seller Dashboard ----------------
    with tabs[3]:
        dash = get_seller_dashboard(session, user.id)
        c1, c2, c3 = st.columns(3)
        c1.metric("📦 Resources Listed", len(dash["resources"]))
        c2.metric("🧾 Total Sales", dash["total_sales"])
        c3.metric("💰 Total Earnings", f"₹{dash['total_earnings']:.0f}")

        st.markdown("#### Your Listed Resources")
        for r in dash["resources"]:
            st.markdown(f"- **{r.title}** — ₹{r.price:.0f} • ⭐ {r.rating} ({r.rating_count}) • "
                       f"⬇ {r.downloads} downloads")
