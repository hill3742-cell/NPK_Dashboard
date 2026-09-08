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

# Theme color hex codes
BG_SURFACE = "#1e222a"
BG_SURFACE_LIGHT = "#282c37"
ACCENT_AMBER = "#ffb300"
COLOR_GREEN = "#4caf50"
COLOR_RED = "#e53935"


def create_option(key: str, text: str = None):
    """Maintains dropdown option compatibility across Flet versions."""
    label = text if text is not None else str(key)
    if hasattr(ft, "DropdownOption"):
        return ft.DropdownOption(key=str(key), text=label)
    return ft.dropdown.Option(str(key), label)


# ---------------------------------------------------------
# TAB: WEEKLY HUB (PINCH ZOOM & AUTO-COLLAPSIBLE CONTROLS)
# ---------------------------------------------------------
def get_weekly_items():
    """Scans assets/weekly for files matching: YYYY_W{num}_(preview|recap)[_p{num}].ext"""
    items = []
    pattern = re.compile(
        r"^(\d{4})_W(?:eek)?_?(\d+)_?(preview|recap)(?:_p\d+)?\.(png|jpg|jpeg|webp|txt)$",
        re.IGNORECASE,
    )

    if os.path.exists(WEEKLY_DIR):
        for fname in sorted(os.listdir(WEEKLY_DIR)):
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
    status_label = ft.Text("", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)

    weekly_scale = [1.0]
    weekly_zoom_label = ft.Text("100%", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)
    weekly_containers = []

    def set_weekly_zoom(factor, reset=False):
        if reset:
            weekly_scale[0] = 1.0
        else:
            weekly_scale[0] = max(0.6, min(4.0, round(weekly_scale[0] + factor, 2)))

        weekly_zoom_label.value = f"{int(weekly_scale[0] * 100)}%"
        new_w = int(750 * weekly_scale[0])
        new_h = int(680 * weekly_scale[0])
        for c in weekly_containers:
            c.width = new_w
            c.height = new_h
        page.update()

    weekly_zoom_bar = ft.Container(
        content=ft.Row(
            [
                ft.Text("Zoom:", weight=ft.FontWeight.BOLD, size=13),
                ft.Button("➖", on_click=lambda e: set_weekly_zoom(-0.25)),
                weekly_zoom_label,
                ft.Button("➕", on_click=lambda e: set_weekly_zoom(0.25)),
                ft.Button("↺ Reset", on_click=lambda e: set_weekly_zoom(0, reset=True)),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=BG_SURFACE_LIGHT,
        padding=6,
        border_radius=8,
    )

    dd_year = ft.Dropdown(label="Year", width=105)
    dd_preview = ft.Dropdown(label="Past Previews", width=155)
    dd_recap = ft.Dropdown(label="Past Recaps", width=155)

    # Collapsible container holding dropdowns and zoom controls
    controls_box = ft.Column(
        controls=[
            ft.Row([dd_year, dd_preview, dd_recap], wrap=True, spacing=8),
            weekly_zoom_bar,
        ],
        spacing=8,
        visible=False,  # Starts collapsed to give maximum room to document
    )

    def toggle_controls(e=None):
        controls_box.visible = not controls_box.visible
        btn_toggle.text = "Hide Controls ▲" if controls_box.visible else "Select / Zoom ▼"
        page.update()

    btn_toggle = ft.TextButton(
        "Select / Zoom ▼",
        icon=ft.Icons.TUNE,
        on_click=toggle_controls,
    )

    header_bar = ft.Container(
        content=ft.Row(
            [status_label, btn_toggle],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=BG_SURFACE_LIGHT,
        padding=8,
        border_radius=8,
    )

    def display_week_group(year: int, week: int, media_type: str, auto_collapse: bool = True):
        content_display.controls.clear()
        weekly_containers.clear()
        weekly_scale[0] = 1.0
        weekly_zoom_label.value = "100%"

        if auto_collapse:
            controls_box.visible = False
            btn_toggle.text = "Select / Zoom ▼"

        items = get_weekly_items()
        matching_pages = [
            i for i in items
            if i["year"] == year and i["week"] == week and i["type"] == media_type
        ]

        if not matching_pages:
            status_label.value = "No Previews or Recaps found."
            content_display.controls.append(ft.Text("Add files to assets/weekly/ to view them here.", italic=True))
        else:
            status_label.value = f"Showing: {year} W{week} {media_type}"
            for page_item in matching_pages:
                if page_item["ext"] in ["png", "jpg", "jpeg", "webp"]:
                    # InteractiveViewer enables native 2-finger pinch and drag panning
                    viewer = ft.InteractiveViewer(
                        content=ft.Image(src=page_item["path"], fit="contain"),
                        min_scale=1.0,
                        max_scale=4.0,
                    )
                    c = ft.Container(
                        content=viewer,
                        width=750,
                        height=680,
                    )
                    weekly_containers.append(c)

                    scrollable_row = ft.Row(
                        controls=[c],
                        scroll=ft.ScrollMode.ADAPTIVE,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                    content_display.controls.append(
                        ft.Card(
                            content=ft.Container(content=scrollable_row, padding=6),
                            margin=ft.Margin(0, 4, 0, 8),
                        )
                    )
                elif page_item["ext"] == "txt":
                    full_path = os.path.join(WEEKLY_DIR, page_item["filename"])
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            text_content = f.read()
                    except Exception:
                        text_content = "Could not read text file."

                    content_display.controls.append(
                        ft.Container(
                            content=ft.Text(text_content, size=15),
                            padding=15,
                            bgcolor=BG_SURFACE_LIGHT,
                            border_radius=8,
                        )
                    )
        page.update()

    def on_selection_change(e):
        val = e.control.value
        if not val:
            return
        parts = val.split("_")
        sel_year, sel_week, sel_type = int(parts[0]), int(parts[1]), parts[2]

        if e.control == dd_preview:
            dd_recap.value = None
        else:
            dd_preview.value = None

        display_week_group(sel_year, sel_week, sel_type, auto_collapse=True)

    def populate_controls(selected_year=None):
        items = get_weekly_items()
        available_years = sorted(list(set(i["year"] for i in items)), reverse=True)
        current_year = datetime.now().year

        if not available_years:
            available_years = [current_year]

        target_year = selected_year or (current_year if current_year in available_years else available_years[0])
        dd_year.options = [create_option(str(y)) for y in available_years]
        dd_year.value = str(target_year)

        year_items = [i for i in items if i["year"] == target_year]

        preview_weeks = sorted(list(set(i["week"] for i in year_items if i["type"] == "Preview")), reverse=True)
        dd_preview.options = [create_option(f"{target_year}_{w}_Preview", f"Week {w} Preview") for w in preview_weeks]
        dd_preview.value = None

        recap_weeks = sorted(list(set(i["week"] for i in year_items if i["type"] == "Recap")), reverse=True)
        dd_recap.options = [create_option(f"{target_year}_{w}_Recap", f"Week {w} Recap") for w in recap_weeks]
        dd_recap.value = None

        if year_items:
            latest = max(year_items, key=lambda x: x["priority"])
            key_val = f"{latest['year']}_{latest['week']}_{latest['type']}"
            if latest["type"] == "Preview":
                dd_preview.value = key_val
            else:
                dd_recap.value = key_val
            display_week_group(latest["year"], latest["week"], latest["type"], auto_collapse=True)
        else:
            status_label.value = "No Previews or Recaps found."
            content_display.controls.clear()
            content_display.controls.append(ft.Text("Add files to assets/weekly/ to view them here.", italic=True))
            page.update()

    def on_year_change(e):
        populate_controls(int(dd_year.value))

    dd_year.on_change = on_year_change
    if hasattr(dd_year, "on_select"):
        dd_year.on_select = on_year_change

    dd_preview.on_change = on_selection_change
    if hasattr(dd_preview, "on_select"):
        dd_preview.on_select = on_selection_change

    dd_recap.on_change = on_selection_change
    if hasattr(dd_recap, "on_select"):
        dd_recap.on_select = on_selection_change

    populate_controls()

    fixed_top_header = ft.Column(
        controls=[
            header_bar,
            controls_box,
            ft.Divider(height=6),
        ],
        spacing=6,
    )

    scrollable_viewer = ft.Column(
        controls=[content_display],
        scroll=ft.ScrollMode.ADAPTIVE,
        expand=True,
    )

    return ft.Column(
        controls=[fixed_top_header, scrollable_viewer],
        expand=True,
        spacing=4,
    )


# ---------------------------------------------------------
# TAB: HISTORY ARCHIVES (PINCH ZOOM & AUTO-COLLAPSIBLE)
# ---------------------------------------------------------
def build_history_tab(page: ft.Page) -> ft.Control:
    history_display = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    history_status = ft.Text("Showing Season: 2025", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)

    history_scale = [1.0]
    history_zoom_label = ft.Text("100%", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)
    history_containers = []

    def set_history_zoom(factor, reset=False):
        if reset:
            history_scale[0] = 1.0
        else:
            history_scale[0] = max(0.6, min(4.0, round(history_scale[0] + factor, 2)))

        history_zoom_label.value = f"{int(history_scale[0] * 100)}%"
        new_w = int(750 * history_scale[0])
        new_h = int(680 * history_scale[0])
        for c in history_containers:
            c.width = new_w
            c.height = new_h
        page.update()

    history_zoom_bar = ft.Container(
        content=ft.Row(
            [
                ft.Text("Zoom:", weight=ft.FontWeight.BOLD, size=13),
                ft.Button("➖", on_click=lambda e: set_history_zoom(-0.25)),
                history_zoom_label,
                ft.Button("➕", on_click=lambda e: set_history_zoom(0.25)),
                ft.Button("↺ Reset", on_click=lambda e: set_history_zoom(0, reset=True)),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=BG_SURFACE_LIGHT,
        padding=6,
        border_radius=8,
    )

    years = [str(y) for y in range(2025, 2010, -1)]
    dd_history_year = ft.Dropdown(
        label="Select Season",
        options=[create_option(y) for y in years],
        value="2025",
        width=150,
    )

    history_controls_box = ft.Column(
        controls=[
            ft.Row([dd_history_year], alignment=ft.MainAxisAlignment.START),
            history_zoom_bar,
        ],
        spacing=8,
        visible=False,
    )

    def toggle_history_controls(e=None):
        history_controls_box.visible = not history_controls_box.visible
        btn_hist_toggle.text = "Hide Controls ▲" if history_controls_box.visible else "Season / Zoom ▼"
        page.update()

    btn_hist_toggle = ft.TextButton(
        "Season / Zoom ▼",
        icon=ft.Icons.TUNE,
        on_click=toggle_history_controls,
    )

    history_header_bar = ft.Container(
        content=ft.Row(
            [history_status, btn_hist_toggle],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=BG_SURFACE_LIGHT,
        padding=8,
        border_radius=8,
    )

    def load_season_images(year, auto_collapse: bool = True):
        history_display.controls.clear()
        history_containers.clear()
        history_scale[0] = 1.0
        history_zoom_label.value = "100%"
        history_status.value = f"Showing Season: {year}"

        if auto_collapse:
            history_controls_box.visible = False
            btn_hist_toggle.text = "Season / Zoom ▼"

        search_dirs = [HISTORY_DIR, ASSETS_DIR]
        pattern = re.compile(rf"^{year}.*\.(png|jpg|jpeg|webp)$", re.IGNORECASE)
        found_images = []

        for d in search_dirs:
            if os.path.exists(d):
                for fname in sorted(os.listdir(d)):
                    if pattern.match(fname):
                        rel_path = f"/history/{fname}" if d == HISTORY_DIR else f"/{fname}"
                        found_images.append(rel_path)

        if found_images:
            for img_path in found_images:
                viewer = ft.InteractiveViewer(
                    content=ft.Image(src=img_path, fit="contain"),
                    min_scale=1.0,
                    max_scale=4.0,
                )
                c = ft.Container(
                    content=viewer,
                    width=750,
                    height=680,
                )
                history_containers.append(c)

                scrollable_row = ft.Row(
                    controls=[c],
                    scroll=ft.ScrollMode.ADAPTIVE,
                    alignment=ft.MainAxisAlignment.CENTER,
                )
                history_display.controls.append(
                    ft.Card(
                        content=ft.Container(content=scrollable_row, padding=6),
                        margin=ft.Margin(0, 4, 0, 8),
                    )
                )
        else:
            history_display.controls.append(
                ft.Text(f"No archive images found for season {year}.", italic=True, size=15)
            )
        page.update()

    def on_year_select(e):
        load_season_images(dd_history_year.value, auto_collapse=True)

    dd_history_year.on_change = on_year_select
    if hasattr(dd_history_year, "on_select"):
        dd_history_year.on_select = on_year_select

    load_season_images("2025", auto_collapse=True)

    fixed_top_header = ft.Column(
        controls=[
            history_header_bar,
            history_controls_box,
            ft.Divider(height=6),
        ],
        spacing=6,
    )

    scrollable_viewer = ft.Column(
        controls=[history_display],
        scroll=ft.ScrollMode.ADAPTIVE,
        expand=True,
    )

    return ft.Column(
        controls=[fixed_top_header, scrollable_viewer],
        expand=True,
        spacing=4,
    )


# ---------------------------------------------------------
# TAB: KEEPER CALCULATOR & VALIDATOR
# ---------------------------------------------------------
def build_keeper_tab(page: ft.Page) -> ft.Control:
    txt_player = ft.TextField(label="Player Name", value="Kyren Williams", expand=True)
    dd_side = ft.Dropdown(
        label="Side of Ball",
        value="Offense",
        options=[
            create_option("Offense"),
            create_option("Defense"),
            create_option("Special Teams"),
        ],
        width=160,
    )
    dd_year = ft.Dropdown(
        label="Years Kept",
        value="1",
        options=[
            create_option("1", "1st Time (2nd Year)"),
            create_option("2", "2nd Time (3rd Year)"),
            create_option("3", "3rd+ Time (4th+ Year)"),
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
    lbl_calc_result = ft.Text("2026 Draft Pick Cost: Round 10", size=20, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)

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
    if hasattr(dd_side, "on_select"):
        dd_side.on_select = calculate_cost

    dd_year.on_change = calculate_cost
    if hasattr(dd_year, "on_select"):
        dd_year.on_select = calculate_cost

    txt_player.on_change = calculate_cost
    txt_prior_round.on_change = calculate_cost

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
                validator_result.controls.append(ft.Text(err, color=COLOR_RED, size=15))
        else:
            validator_result.controls.append(
                ft.Text("✅ This sample keeper roster is 100% compliant with NPK rules!", color=COLOR_GREEN, size=15)
            )
        page.update()

    run_validation()

    return ft.ListView(
        expand=True,
        spacing=15,
        padding=15,
        controls=[
            ft.Text("Keeper Cost Calculator", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("Calculate draft pick cost based on official NPK rules.", italic=True),
            ft.Row([txt_player, dd_side], wrap=True),
            ft.Row([dd_year, txt_prior_round], wrap=True),
            chk_undrafted,
            rg_priority,
            ft.Container(
                content=lbl_calc_result,
                padding=15,
                bgcolor=BG_SURFACE_LIGHT,
                border_radius=8,
            ),
            ft.Divider(height=25),
            ft.Text("Team Keeper Roster Validator", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("Checks max 4 keepers, offense/defense split, and Rounds 1-4 restrictions.", italic=True),
            validator_result,
        ],
    )


# ---------------------------------------------------------
# TAB: RULES & SETTINGS
# ---------------------------------------------------------
def build_rules_tab(page: ft.Page) -> ft.Control:
    return ft.ListView(
        expand=True,
        spacing=15,
        padding=15,
        controls=[
            ft.Text("Official League Rules & Guidelines", size=22, weight=ft.FontWeight.BOLD),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("League Configuration", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("• Format: 12-Team H2H, Snake Draft (24 Rounds)"),
                        ft.Text("• Buy-In: $100 entry fee"),
                        ft.Text("• Keeper Deadline: Friday, August 21 (2:00 AM CDT)"),
                        ft.Text("• Draft Date: Saturday, August 29 (7:45 PM CDT)"),
                        ft.Text("• Waivers: FAAB bidding"),
                    ], spacing=6),
                )
            ),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Roster & Position Constraints", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("• Roster Size: 24 Total (15 Starters, 9 Bench)"),
                        ft.Text("• Bench Constraint: Max 6 per side of ball (Offense, Defense, or ST)"),
                        ft.Text("• IR Slots: 2 total (Max 1 Offense, 1 Defense)"),
                    ], spacing=6),
                )
            ),
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("Keeper Roster Limits", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("• Total Keepers: Up to 4 players"),
                        ft.Text("• 2 Keepers: Max 1 Offense, Max 1 Defense/ST"),
                        ft.Text("• 3 or 4 Keepers: Max 2 Offense, Max 2 Defense/ST"),
                        ft.Text("• Rounds 1–4 Rule: Only 1 player allowed in rounds 1 through 4"),
                        ft.Text("• Undrafted Free Agents: 13th / 12th round (Offense), 20th / 19th round (Defense)"),
                    ], spacing=6),
                )
            ),
        ],
    )


# ---------------------------------------------------------
# MAIN APP ENTRY POINT (Pinned Header Navigation)
# ---------------------------------------------------------
def main(page: ft.Page):
    page.title = "NPK Fantasy Football League Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 8

    views = [
        build_weekly_tab(page),
        build_history_tab(page),
        build_keeper_tab(page),
        build_rules_tab(page),
    ]

    body = ft.Container(content=views[0], expand=True)

    def switch_tab(idx):
        body.content = views[idx]
        page.update()

    nav_row = ft.Row(
        controls=[
            ft.Button("Weekly Hub", on_click=lambda e: switch_tab(0)),
            ft.Button("History Archives", on_click=lambda e: switch_tab(1)),
            ft.Button("Keeper Calculator", on_click=lambda e: switch_tab(2)),
            ft.Button("Rules & Settings", on_click=lambda e: switch_tab(3)),
        ],
        scroll=ft.ScrollMode.ADAPTIVE,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    page.add(
        ft.Column(
            controls=[
                nav_row,
                ft.Divider(height=8),
                body,
            ],
            expand=True,
            spacing=4,
        )
    )


# ---------------------------------------------------------
# RUNNER: ENVIRONMENT-AWARE FOR CLOUD & LOCAL
# ---------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    if "PORT" in os.environ:
        ft.run(main, host="0.0.0.0", port=port, assets_dir="assets")
    else:
        ft.run(main, assets_dir="assets", view=ft.AppView.WEB_BROWSER)