import streamlit as st
import pandas as pd
import os
from keeper_rules import calculate_keeper_cost, validate_keeper_selections

st.set_page_config(page_title="NPK FF League", page_icon="🏈", layout="wide")
st.title("🏈 NPK Fantasy Football League Dashboard")
st.caption("League ID: 31198 | 12 Teams | 24 Draft Rounds")

tab1, tab2, tab3 = st.tabs(["Keeper Calculator & Validator", "League Rules & Settings", "League Media"])

with tab1:
    st.subheader("Keeper Cost Calculator")
    st.write("Calculate a player's upcoming draft pick cost based on official NPK rules.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        player_name = st.text_input("Player Name", value="Kyren Williams")
        player_side = st.selectbox("Side of Ball", ["Offense", "Defense", "Special Teams"])
    with col2:
        keeper_year = st.selectbox("Years Kept (Times Kept)", [1, 2, 3], 
                                  format_func=lambda x: f"1st Time (2nd Year)" if x==1 else (f"2nd Time (3rd Year)" if x==2 else "3rd+ Time (4th+ Year)"))
    with col3:
        is_undrafted = st.checkbox("Was Undrafted FA last season?")
        undrafted_num = st.radio("Undrafted Priority", [1, 2], horizontal=True, help="Pick 1st or 2nd undrafted kept on this side") if is_undrafted else 1
    with col4:
        prior_round = st.number_input("Prior Season Draft Round", min_value=1, max_value=24, value=10, disabled=is_undrafted)

    cost = calculate_keeper_cost(
        side="Offense" if player_side == "Offense" else "Defense",
        keeper_year=keeper_year,
        prior_round=prior_round,
        is_undrafted=is_undrafted,
        undrafted_count=undrafted_num
    )

    st.metric(label=f"2026 Draft Pick Cost for {player_name}", value=f"Round {cost}")
    
    st.divider()
    st.subheader("Team Keeper Roster Validation Test")
    st.write("Simulate a team's 4 potential keepers to test NPK eligibility rules:")

    # Interactive sample team simulation
    demo_team = [
        {"name": "Ja'Marr Chase", "side": "Offense", "cost_round": 1},
        {"name": "Kyren Williams", "side": "Offense", "cost_round": 10},
        {"name": "Fred Warner", "side": "Defense", "cost_round": 13},
        {"name": "T.J. Watt", "side": "Defense", "cost_round": 4},
    ]

    team_df = pd.DataFrame(demo_team)
    st.dataframe(team_df, use_container_width=True)

    violations = validate_keeper_selections(demo_team)
    if violations:
        for err in violations:
            st.error(err)
    else:
        st.success("✅ This keeper selection is 100% compliant with NPK rules!")

with tab2:
    st.subheader("League Configuration")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        * **Format:** 12-Team H2H, Snake Draft (24 Rounds)
        * **Keeper Deadline:** Friday, August 21 (2:00 AM CDT)
        * **Draft Date:** Saturday, August 29 (7:45 PM CDT)
        * **Waivers:** FAAB
        """)
    with col_b:
        st.markdown("""
        * **Roster Size:** 24 Total (15 Starters, 9 Bench)
        * **Bench Rule:** Max 6 Offense, Defense, or ST on bench
        * **IR Slots:** 2 total (Max 1 Offense, 1 Defense)
        * **Round 1-4 Rule:** Max 1 keeper allowed in rounds 1–4
        """)

with tab3:
    st.subheader("League History & Archives")
    st.write("Select a season below to view its complete historical pages.")

    # Master Archive Download Button
    master_pdf = "No Pain Keeper League - All Seasons History.pdf"
    if os.path.exists(master_pdf):
        with open(master_pdf, "rb") as pdf_file:
            st.download_button(
                label="📥 Download Master All-Seasons History PDF",
                data=pdf_file,
                file_name=master_pdf,
                mime="application/pdf",
                use_container_width=True
            )

    st.divider()
    st.subheader("Season Archive Viewer")

    years = list(range(2025, 2010, -1))
    selected_year = st.selectbox("Choose Season Archive Year", years)

    if selected_year:
        st.info(f"📸 Displaying history pages for the **{selected_year} Season**:")
        
        # Loop through and display all available pages for the selected year
        page_num = 1
        images_found = False
        
        while True:
            image_filename = f"{selected_year}_season_history_page_{page_num}.png"
            if os.path.exists(image_filename):
                st.image(image_filename, use_container_width=True)
                # Add a small divider between pages if there are multiple
                st.markdown("---")
                page_num += 1
                images_found = True
            else:
                break
        
        if not images_found:
            st.warning(f"⚠️ Image archive for {selected_year} not found in the folder.")