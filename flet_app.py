import os
import re
from datetime import datetime
import flet as ft
from keeper_rules import calculate_keeper_cost, validate_keeper_selections

# ---------------------------------------------------------
# DIRECTORY CONFIGURATIONS
# ---------------------------------------------------------
ASSETS_DIR = "assets"
WEEKLY_DIR = os.path.join(ASSETS_DIR, "weekly")
HISTORY_DIR = os.path.join(ASSETS_DIR, "history")

os.makedirs(WEEKLY_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)


# ---------------------------------------------------------
# TAB 1: KEEPER CALCULATOR & VALIDATOR
# ---------------------------------------------------------
def build_keeper_tab(page: ft.Page) -> ft.Control:
    txt_player = ft.TextField(label="Player Name", value="Kyren Williams", expand=True)
    dd_side = ft.Dropdown(
        label="Side of Ball",
        value="Offense",
        options=[ft.dropdown.Option("Offense"), ft.dropdown.Option("Defense"), ft.dropdown.Option("Special Teams")],
        width=160,
    )
    dd_year = ft.Dropdown(
        label="Years Kept",
        value="1",
        options=[
            ft.dropdown.Option("1", "1st Time (2nd Year)"),
            ft.dropdown.Option("2", "2nd Time (3rd Year)"),
            ft.dropdown.Option("3", "3rd+ Time (4th+ Year)"),
        ],
        width=200,
    )
    chk_undrafted = ft.Checkbox(label="Was Undrafted FA last season?", value=False)
    rg_priority = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="1", label="1st Undrafted"),
            ft.Radio(value="2", label="2nd Undrafted"),
        ]),
        value="1",
    )
    txt_prior_round = ft.TextField(label="Prior Draft Round (1-24)", value="10", width=190)
    lbl_calc_result = ft.Text("2026 Draft Pick Cost: Round 10", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)

    def calculate_cost(e=None):
        side = dd_side.value
        k_year = int(dd_year.value or 1)
        is_undr = chk_undrafted.value
        undr_prio = int(rg_priority.value or 1)
        try:
            p_round = int(txt_prior_round.value or 1)
        except ValueError:
            p_round = 1

        cost = calculate_keeper_cost(
            side="Offense" if side == "Offense" else "Defense",
            keeper_year=k_year,
            prior_round=p_round,
            is_undrafted=is_undr,
            undrafted_count=undr_prio,
        )
        p_name = txt_player.value.strip() or "Player"
        lbl_calc_result.value = f"2026 Draft Pick Cost for {p_name}: Round {cost}"
        page.update()

    def on_undrafted_toggle(e):
        txt_prior_round.disabled = chk_undrafted.value
        rg_priority.visible = chk_undrafted.value
        calculate_cost()

    chk_undrafted.on_change = on_undrafted_toggle
    rg_priority.visible = False
    rg_priority.on_change = calculate_cost
    dd_side.on_change = calculate_cost
    dd_year.on_change = calculate_cost
    txt_player.on_change = calculate_cost
    txt_prior_round.on_change = calculate_cost

    # Keeper Validator Section
    validator_result = ft.Column()

    def run_validation(e=None):
        demo_team = [
            {"name": "Ja'Marr Chase", "side": "Offense", "cost_round": 1},
            {"name": "Kyren Williams", "side": "Offense", "cost_round": 10},
            {"name": "Fred Warner", "side": "Defense", "cost_round": 13},
            {"name": "T.J. Watt", "side": "Defense", "cost_round": 4},
        ]
        violations = validate_keeper_selections(demo_team)
        validator_result.controls.clear()
        if violations:
            for err in violations:
                validator_result.controls.append(ft.Text(err, color=ft.Colors.RED_400, size=15))
        else:
            validator_result.controls.append(
                ft.Text("✅ This sample keeper roster is 100% compliant with NPK rules!", color=ft.Colors.GREEN_400, size=15)
            )
        page.update()

    run_validation()

    return ft.ListView(
        expand=True,
        spacing=15,
        padding=20,
        controls=[
            ft.Text("Keeper Cost Calculator", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("Calculate draft pick cost based on official NPK rules[cite: 3].", italic=True),
            ft.Row([txt_player, dd_side], wrap=True),
            ft.Row([dd_year, txt_prior_round], wrap=True),
            chk_undrafted,
            rg_priority,
            ft.Container(
                content=lbl_calc_result,
                padding=15,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                border_radius=8,
            ),
            ft.Divider(height=30),
            ft.Text("Team Keeper Roster Validator", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("Checks max 4 keepers, offense/defense split, and Rounds 1-4 restrictions[cite: 4, 5].", italic=True),
            validator_result,
        ],
    )


# ---------------------------------------------------------
# TAB 2: RULES & SETTINGS
# ---------------------------------------------------------
def build_rules_tab(page: ft.Page) -> ft.Control:
    return ft.ListView(
        expand=True,
        spacing=15,
        padding=20,
        controls=[
            ft.Text("Official League Rules & Guidelines", size=22, weight=ft.FontWeight.BOLD),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("League Configuration", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("• Format: 12-Team H2H, Snake Draft (24 Rounds)[cite: 3, 4]"),
                        ft.Text("• Buy-In: $100 entry fee[cite: 4]"),
                        ft.Text("• Keeper Deadline: Friday, August 21 (2:00 AM CDT)[cite: 3, 4]"),
                        ft.Text("• Draft Date: Saturday, August 29 (7:45 PM CDT)[cite: 3, 4]"),
                        ft.Text("• Waivers: FAAB bidding[cite: 3, 5]"),
                    ], spacing=6),
                )
            ),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Roster & Position Constraints", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("• Roster Size: 24 Total (15 Starters, 9 Bench)[cite: 3, 4]"),
                        ft.Text("• Bench Constraint: Max 6 per side of ball (Offense, Defense, or ST)[cite: 3, 4]"),
                        ft.Text("• IR Slots: 2 total (Max 1 Offense, 1 Defense)[cite: 3, 4]"),
                    ], spacing=6),
                )
            ),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Keeper Roster Limits", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("• Total Keepers: Up to 4 players[cite: 4]"),
                        ft.Text("• 2 Keepers: Max 1 Offense, Max 1 Defense/ST[cite: 4, 5]"),
                        ft.Text("• 3 or 4 Keepers: Max 2 Offense, Max 2 Defense/ST[cite: 4, 5]"),
                        ft.Text("• Rounds 1–4 Rule: Only 1 player allowed in rounds 1 through 4[cite: 3, 4, 5]"),
                        ft.Text("• Undrafted Free Agents: 13th / 12th round (Offense), 20th / 19th round (Defense)[cite: 4, 5]"),
                    ], spacing=6),
                )
            ),
        ],
    )


# ---------------------------------------------------------
# TAB 3: HISTORY ARCHIVES
# ---------------------------------------------------------
def build_history_tab(page: ft.Page) -> ft.Control:
    history_display = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def load_season_images(year):
        history_display.controls.clear()
        found_images = []

        # Check assets/history and assets for year images
        search_dirs = [HISTORY_DIR, ASSETS_DIR]
        pattern = re.compile(rf"^{year}.*\.(png|jpg|jpeg|webp)$", re.IGNORECASE)

        for d in search_dirs:
            if os.path.exists(d):
                for fname in sorted(os.listdir(d)):
                    if pattern.match(fname):
                        rel_path = f"/history/{fname}" if d == HISTORY_DIR else f"/{fname}"
                        found_images.append(rel_path)

        if found_images:
            for img_path in found_images:
                history_display.controls.append(
                    ft.Image(src=img_path, fit=ft.ImageFit.CONTAIN, expand=True)
                )
        else:
            history_display.controls.append(
                ft.Text(f"No archive images uploaded for {year} yet.", italic=True, size=15)
            )
        page.update()

    years = [str(y) for y in range(2025, 2010, -1)]
    dd_history_year = ft.Dropdown(
        label="Select Season",
        options=[ft.dropdown.Option(y) for y in years],
        value="2025",
        width=180,
    )

    def on_year_select(e):
        load_season_images(dd_history_year.value)

    dd_history_year.on_change = on_year_select
    load_season_images("2025")

    return ft.ListView(
        expand=True,
        spacing=15,
        padding=20,
        controls=[
            ft.Text("Historical Season Archives", size=22, weight=ft.FontWeight.BOLD),
            dd_history_year,
            ft.Divider(),
            history_display,
        ],
    )


# ---------------------------------------------------------
# TAB 4: WEEKLY HUB (PREVIEWS & RECAPS)
# ---------------------------------------------------------
def get_weekly_items():
    """Scans assets/weekly for files matching: YYYY_W{num}_(preview|recap).ext"""
    items = []
    pattern = re.compile(r"^(\d{4})_W(?:eek)?_?(\d+)_?(preview|recap)\.(png|jpg|jpeg|webp|txt)$", re.IGNORECASE)

    if os.path.exists(WEEKLY_DIR):
        for fname in os.listdir(WEEKLY_DIR):
            match = pattern.match(fname)
            if match:
                year, week, media_type, ext = match.groups()
                items.append({
                    "year": int(year),
                    "week": int(week),
                    "type": media_type.capitalize(),
                    "filename": fname,
                    "path": f"/weekly/{fname}",
                    "ext": ext.lower(),
                    "priority": int(week) * 10 + (2 if media_type.lower() == "recap" else 1),
                })
    return items


def build_weekly_tab(page: ft.Page) -> ft.Control:
    content_display = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    status_label = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300)

    def display_item(item):
        content_display.controls.clear()
        if not item:
            status_label.value = "No Previews or Recaps found for this season."
            content_display.controls.append(ft.Text("Add files to assets/weekly/ to view them here.", italic=True))
        else:
            status_label.value = f"Showing: {item['year']} Week {item['week']} {item['type']}"
            if item["ext"] in ["png", "jpg", "jpeg", "webp"]:
                content_display.controls.append(
                    ft.Image(src=item["path"], fit=ft.ImageFit.CONTAIN, expand=True)
                )
            elif item["ext"] == "txt":
                full_path = os.path.join(WEEKLY_DIR, item["filename"])
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        text_content = f.read()
                except Exception:
                    text_content = "Could not read text file."

                content_display.controls.append(
                    ft.Container(
                        content=ft.Text(text_content, size=15),
                        padding=15,
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                        border_radius=8,
                    )
                )
        page.update()

    dd_year = ft.Dropdown(label="Year", width=120)
    dd_preview = ft.Dropdown(label="Past Previews", width=170)
    dd_recap = ft.Dropdown(label="Past Recaps", width=170)

    def on_selection_change(e):
        items = get_weekly_items()
        selected_file = e.control.value
        match = next((i for i in items if i["filename"] == selected_file), None)
        if match:
            if e.control == dd_preview:
                dd_recap.value = None
            else:
                dd_preview.value = None
            display_item(match)

    def populate_controls(selected_year=None):
        items = get_weekly_items()
        available_years = sorted(list(set(i["year"] for i in items)), reverse=True)
        current_year = datetime.now().year

        if not available_years:
            available_years = [current_year]

        target_year = selected_year or (current_year if current_year in available_years else available_years[0])
        dd_year.options = [ft.dropdown.Option(str(y)) for y in available_years]
        dd_year.value = str(target_year)

        year_items = [i for i in items if i["year"] == target_year]

        # Newest weeks first
        previews = sorted([i for i in year_items if i["type"] == "Preview"], key=lambda x: x["week"], reverse=True)
        dd_preview.options = [ft.dropdown.Option(p["filename"], f"Week {p['week']} Preview") for p in previews]
        dd_preview.value = None

        recaps = sorted([i for i in year_items if i["type"] == "Recap"], key=lambda x: x["week"], reverse=True)
        dd_recap.options = [ft.dropdown.Option(r["filename"], f"Week {r['week']} Recap") for r in recaps]
        dd_recap.value = None

        # Highest priority: Week * 10 + (2 for Recap, 1 for Preview)
        if year_items:
            latest = max(year_items, key=lambda x: x["priority"])
            if latest["type"] == "Preview":
                dd_preview.value = latest["filename"]
            else:
                dd_recap.value = latest["filename"]
            display_item(latest)
        else:
            display_item(None)

    def on_year_change(e):
        populate_controls(int(dd_year.value))

    dd_year.on_change = on_year_change
    dd_preview.on_change = on_selection_change
    dd_recap.on_change = on_selection_change

    populate_controls()

    return ft.ListView(
        expand=True,
        spacing=15,
        padding=20,
        controls=[
            ft.Row(
                controls=[dd_year, dd_preview, dd_recap],
                alignment=ft.MainAxisAlignment.START,
                wrap=True,
            ),
            status_label,
            ft.Divider(),
            content_display,
        ],
    )


# ---------------------------------------------------------
# MAIN APP ENTRY POINT
# ---------------------------------------------------------
def main(page: ft.Page):
    page.title = "NPK Fantasy Football League Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    page.appbar = ft.AppBar(
        leading=ft.Image(src="/icons/icon-192.png", fit=ft.ImageFit.CONTAIN),
        title=ft.Text("NPK Fantasy Football League"),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
    )

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Keeper Calculator", content=build_keeper_tab(page)),
            ft.Tab(text="Rules & Settings", content=build_rules_tab(page)),
            ft.Tab(text="History Archives", content=build_history_tab(page)),
            ft.Tab(text="Weekly Hub", content=build_weekly_tab(page)),
        ],
        expand=True,
    )

    page.add(tabs)


# ---------------------------------------------------------
# RUNNER: ENVIRONMENT-AWARE FOR CLOUD & LOCAL
# ---------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    if "PORT" in os.environ:
        ft.run(main, host="0.0.0.0", port=port, assets_dir="assets")
    else:
        ft.run(main, assets_dir="assets", view=ft.AppView.WEB_BROWSER)