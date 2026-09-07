import os
import flet as ft
from keeper_rules import calculate_keeper_cost, validate_keeper_selections

def main(page: ft.Page):
    page.title = "NPK FF League"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20

    # --- Header ---
    header = ft.Column([
        ft.Text("🏈 NPK Fantasy Football League", size=28, weight=ft.FontWeight.BOLD),
        ft.Text("League ID: 31198 | 12 Teams | 24 Draft Rounds", color=ft.Colors.GREY_700),
        ft.Divider()
    ])

    # --- TAB 1: Keeper Calculator & Validator ---
    player_name = ft.TextField(label="Player Name", value="Kyren Williams", expand=True)
    player_side = ft.Dropdown(
        label="Side of Ball",
        options=[
            ft.DropdownOption(key="Offense", text="Offense"),
            ft.DropdownOption(key="Defense", text="Defense"),
            ft.DropdownOption(key="Special Teams", text="Special Teams")
        ],
        value="Offense",
        expand=True
    )
    keeper_year = ft.Dropdown(
        label="Years Kept",
        options=[
            ft.DropdownOption(key="1", text="1st Time (2nd Year)"),
            ft.DropdownOption(key="2", text="2nd Time (3rd Year)"),
            ft.DropdownOption(key="3", text="3rd+ Time (4th+ Year)")
        ],
        value="1",
        expand=True
    )
    is_undrafted = ft.Checkbox(label="Was Undrafted FA last season?", value=False)
    undrafted_num = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="1", label="1st Undrafted"),
            ft.Radio(value="2", label="2nd Undrafted")
        ]),
        value="1"
    )
    prior_round = ft.TextField(label="Prior Season Draft Round", value="10", expand=True)
    cost_display = ft.Text("2026 Draft Pick Cost: Round 10", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)

    def update_cost(e):
        try:
            round_val = int(prior_round.value) if prior_round.value else 10
        except ValueError:
            round_val = 10

        cost = calculate_keeper_cost(
            side="Offense" if player_side.value == "Offense" else "Defense",
            keeper_year=int(keeper_year.value),
            prior_round=round_val,
            is_undrafted=is_undrafted.value,
            undrafted_count=int(undrafted_num.value)
        )
        cost_display.value = f"2026 Draft Pick Cost: Round {cost}"
        page.update()

    def toggle_undrafted(e):
        prior_round.disabled = is_undrafted.value
        update_cost(e)

    if hasattr(player_side, "on_select"):
        player_side.on_select = update_cost
        keeper_year.on_select = update_cost
    else:
        player_side.on_change = update_cost
        keeper_year.on_change = update_cost

    prior_round.on_change = update_cost
    is_undrafted.on_change = toggle_undrafted
    undrafted_num.on_change = update_cost

    calc_tab = ft.Column([
        ft.Text("Keeper Cost Calculator", size=20, weight=ft.FontWeight.BOLD),
        ft.Text("Calculate a player's upcoming draft pick cost based on official NPK rules."),
        ft.Row([player_name, player_side]),
        ft.Row([keeper_year, prior_round]),
        is_undrafted,
        ft.Text("Undrafted Priority:", size=12, color=ft.Colors.GREY_600),
        undrafted_num,
        cost_display,
        ft.Divider()
    ], scroll=ft.ScrollMode.AUTO, expand=True)

    # --- TAB 2: League Rules & Settings ---
    rules_tab = ft.Column([
        ft.Text("League Configuration & Settings", size=20, weight=ft.FontWeight.BOLD),
        ft.Markdown("""
* **Format:** 12-Team H2H, Snake Draft (24 Rounds)
* **Keeper Deadline:** Friday, August 21 (2:00 AM CDT)
* **Draft Date:** Saturday, August 29 (7:45 PM CDT)
* **Waivers:** FAAB
* **Roster Size:** 24 Total (15 Starters, 9 Bench)
* **Bench Rule:** Max 6 Offense, Defense, or ST on bench
* **IR Slots:** 2 total (Max 1 Offense, 1 Defense)
* **Round 1-4 Rule:** Max 1 keeper allowed in rounds 1–4
        """)
    ], scroll=ft.ScrollMode.AUTO, expand=True)

    # --- TAB 3: Season Archive Image Viewer ---
    history_container = ft.Column(scroll=ft.ScrollMode.AUTO)

    def show_history(e):
        history_container.controls.clear()
        selected_year = year_dropdown.value
        history_path = os.path.join("assets", "history")

        page_num = 1
        found_images = False

        while True:
            filename = f"{selected_year}_season_history_page_{page_num}.png"
            file_path = os.path.join(history_path, filename)

            if os.path.exists(file_path):
                history_container.controls.append(
                    ft.Image(
                        src=f"history/{filename}",
                        fit="contain",
                        border_radius=8
                    )
                )
                history_container.controls.append(ft.Divider())
                page_num += 1
                found_images = True
            else:
                break

        if not found_images:
            history_container.controls.append(
                ft.Text(f"⚠️ No history pages found for {selected_year} in assets/history.", color=ft.Colors.ORANGE_800)
            )
        page.update()

    years = [str(y) for y in range(2025, 2010, -1)]
    year_dropdown = ft.Dropdown(
        label="Choose Season Archive Year",
        options=[ft.DropdownOption(key=y, text=y) for y in years],
        value="2011",
        width=300
    )

    if hasattr(year_dropdown, "on_select"):
        year_dropdown.on_select = show_history
    else:
        year_dropdown.on_change = show_history

    history_tab = ft.Column([
        ft.Text("League History & Archives", size=20, weight=ft.FontWeight.BOLD),
        year_dropdown,
        history_container
    ], scroll=ft.ScrollMode.AUTO, expand=True)

    # --- Modern Flet Tab Structure ---
    tabs = ft.Tabs(
        length=3,
        selected_index=0,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Keeper Calculator"),
                        ft.Tab(label="Rules & Settings"),
                        ft.Tab(label="History Archives"),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        calc_tab,
                        rules_tab,
                        history_tab,
                    ]
                )
            ]
        )
    )

    page.add(header, tabs)
    show_history(None)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    if "PORT" in os.environ:
        # Render cloud mode (binds to Render's dynamic port)
        ft.run(main, host="0.0.0.0", port=port, assets_dir="assets")
    else:
        # Local computer mode (opens your browser)
        ft.run(main, assets_dir="assets", view=ft.AppView.WEB_BROWSER)