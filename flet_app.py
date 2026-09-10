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
# TAB 1: WEEKLY HUB (PREVIEWS & RECAPS WITH PINCH-TO-ZOOM)
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
    status_label = ft.Text("", size=15, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)

    weekly_scale = [1.0]
    weekly_zoom_label = ft.Text("100%", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)
    weekly_containers = []

    def set_weekly_zoom(factor, reset=False):
        if reset:
            weekly_scale[0] = 1.0
        else:
            weekly_scale[0] = max(0.4, min(2.5, round(weekly_scale[0] + factor, 2)))

        weekly_zoom_label.value = f"{int(weekly_scale[0] * 100)}%"
        new_w = int(750 * weekly_scale[0])
        for c in weekly_containers:
            c.width = new_w
        page.update()

    weekly_zoom_bar = ft.Container(
        content=ft.Row(
            [
                ft.Text("Zoom / Pinch:", weight=ft.FontWeight.BOLD, size=13),
                ft.Button("➖", on_click=lambda e: set_weekly_zoom(-0.25)),
                weekly_zoom_label,
                ft.Button("➕", on_click=lambda e: set_weekly_zoom(0.25)),
                ft.Button("↺ Reset", on_click=lambda e: set_weekly_zoom(0, reset=True)),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        ),
        bgcolor=BG_SURFACE_LIGHT,
        padding=6,
        border_radius=8,
    )

    weekly_controls_column = ft.Column(
        controls=[
            ft.Text("", size=1),
            status_label,
            weekly_zoom_bar,
        ],
        spacing=8,
        visible=True,
    )

    btn_toggle_controls = ft.TextButton(
        "▲ Hide Controls / Fullscreen",
        icon=ft.Icons.KEYBOARD_ARROW_UP,
    )

    def toggle_weekly_controls(e):
        weekly_controls_column.visible = not weekly_controls_column.visible
        if weekly_controls_column.visible:
            btn_toggle_controls.text = "▲ Hide Controls / Fullscreen"
            btn_toggle_controls.icon = ft.Icons.KEYBOARD_ARROW_UP
        else:
            btn_toggle_controls.text = "▼ Show Controls & Zoom Bar"
            btn_toggle_controls.icon = ft.Icons.KEYBOARD_ARROW_DOWN
        page.update()

    btn_toggle_controls.on_click = toggle_weekly_controls

    def display_week_group(year: int, week: int, media_type: str):
        content_display.controls.clear()
        weekly_containers.clear()
        weekly_scale[0] = 1.0
        weekly_zoom_label.value = "100%"

        items = get_weekly_items()
        matching_pages = [
            i for i in items
            if i["year"] == year and i["week"] == week and i["type"] == media_type
        ]

        if not matching_pages:
            status_label.value = "No Previews or Recaps found for this selection."
            content_display.controls.append(ft.Text("Add files to assets/weekly/ to view them here.", italic=True))
        else:
            status_label.value = f"Showing: {year} Week {week} {media_type}"
            for page_item in matching_pages:
                if page_item["ext"] in ["png", "jpg", "jpeg", "webp"]:
                    pinch_viewer = ft.InteractiveViewer(
                        content=ft.Image(src=page_item["path"], fit="contain"),
                        min_scale=0.4,
                        max_scale=2.5,
                        pan_enabled=True,
                        scale_enabled=True,
                    )
                    c = ft.Container(
                        content=pinch_viewer,
                        width=750,
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
                            margin=ft.Margin(0, 6, 0, 6),
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

    dd_year = ft.Dropdown(label="Year", width=110)
    dd_preview = ft.Dropdown(label="Past Previews", width=160)
    dd_recap = ft.Dropdown(label="Past Recaps", width=160)

    weekly_controls_column.controls[0] = ft.Row([dd_year, dd_preview, dd_recap], wrap=True, spacing=10)

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

        display_week_group(sel_year, sel_week, sel_type)

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
            display_week_group(latest["year"], latest["week"], latest["type"])
        else:
            status_label.value = "No Previews or Recaps found for this season."
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
            ft.Row([btn_toggle_controls], alignment=ft.MainAxisAlignment.END),
            weekly_controls_column,
            ft.Divider(height=10),
        ],
        spacing=4,
    )

    scrollable_viewer = ft.Column(
        controls=[content_display],
        scroll=ft.ScrollMode.ADAPTIVE,
        expand=True,
    )

    return ft.Column(
        controls=[fixed_top_header, scrollable_viewer],
        expand=True,
        spacing=5,
    )


# ---------------------------------------------------------
# TAB 2: HISTORY ARCHIVES (PINCH-TO-ZOOM & COLLAPSIBLE HEADER)
# ---------------------------------------------------------
def build_history_tab(page: ft.Page) -> ft.Control:
    history_display = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    history_scale = [1.0]
    history_zoom_label = ft.Text("100%", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)
    history_containers = []

    def set_history_zoom(factor, reset=False):
        if reset:
            history_scale[0] = 1.0
        else:
            history_scale[0] = max(0.4, min(2.5, round(history_scale[0] + factor, 2)))

        history_zoom_label.value = f"{int(history_scale[0] * 100)}%"
        new_w = int(750 * history_scale[0])
        for c in history_containers:
            c.width = new_w
        page.update()

    history_zoom_bar = ft.Container(
        content=ft.Row(
            [
                ft.Text("Zoom / Pinch:", weight=ft.FontWeight.BOLD, size=13),
                ft.Button("➖", on_click=lambda e: set_history_zoom(-0.25)),
                history_zoom_label,
                ft.Button("➕", on_click=lambda e: set_history_zoom(0.25)),
                ft.Button("↺ Reset", on_click=lambda e: set_history_zoom(0, reset=True)),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
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

    history_controls_column = ft.Column(
        controls=[
            ft.Text("Historical Season Archives", size=18, weight=ft.FontWeight.BOLD),
            ft.Row([dd_history_year], alignment=ft.MainAxisAlignment.START),
            history_zoom_bar,
        ],
        spacing=6,
        visible=True,
    )

    btn_toggle_history_controls = ft.TextButton(
        "▲ Hide Controls / Fullscreen",
        icon=ft.Icons.KEYBOARD_ARROW_UP,
    )

    def toggle_history_controls(e):
        history_controls_column.visible = not history_controls_column.visible
        if history_controls_column.visible:
            btn_toggle_history_controls.text = "▲ Hide Controls / Fullscreen"
            btn_toggle_history_controls.icon = ft.Icons.KEYBOARD_ARROW_UP
        else:
            btn_toggle_history_controls.text = "▼ Show Controls & Zoom Bar"
            btn_toggle_history_controls.icon = ft.Icons.KEYBOARD_ARROW_DOWN
        page.update()

    btn_toggle_history_controls.on_click = toggle_history_controls

    def load_season_images(year):
        history_display.controls.clear()
        history_containers.clear()
        history_scale[0] = 1.0
        history_zoom_label.value = "100%"

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
                pinch_viewer = ft.InteractiveViewer(
                    content=ft.Image(src=img_path, fit="contain"),
                    min_scale=0.4,
                    max_scale=2.5,
                    pan_enabled=True,
                    scale_enabled=True,
                )
                c = ft.Container(
                    content=pinch_viewer,
                    width=750,
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
                        margin=ft.Margin(0, 6, 0, 6),
                    )
                )
        else:
            history_display.controls.append(
                ft.Text(f"No archive images found for season {year}.", italic=True, size=15)
            )
        page.update()

    def on_year_select(e):
        load_season_images(dd_history_year.value)

    dd_history_year.on_change = on_year_select
    if hasattr(dd_history_year, "on_select"):
        dd_history_year.on_select = on_year_select

    load_season_images("2025")

    fixed_top_header = ft.Column(
        controls=[
            ft.Row([btn_toggle_history_controls], alignment=ft.MainAxisAlignment.END),
            history_controls_column,
            ft.Divider(height=10),
        ],
        spacing=4,
    )

    scrollable_viewer = ft.Column(
        controls=[history_display],
        scroll=ft.ScrollMode.ADAPTIVE,
        expand=True,
    )

    return ft.Column(
        controls=[fixed_top_header, scrollable_viewer],
        expand=True,
        spacing=5,
    )


# ---------------------------------------------------------
# TAB 3: KEEPER CALCULATOR & VALIDATOR
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
# EXCEL PAYOUT READER (FALLBACK & DYNAMIC WORKBOOK SYNC)
# ---------------------------------------------------------
def load_payouts_from_excel():
    possible_names = [
        "2026 Fantasy Football Payouts.xlsm",
        "2026 Fantasy Football Payouts.xlsx",
        os.path.join(ASSETS_DIR, "2026 Fantasy Football Payouts.xlsm"),
        os.path.join(ASSETS_DIR, "2026 Fantasy Football Payouts.xlsx"),
    ]
    target_file = None
    for p in possible_names:
        if os.path.exists(p):
            target_file = p
            break

    if not target_file:
        return None, None

    try:
        import openpyxl
        wb = openpyxl.load_workbook(target_file, data_only=True)
        target_sheet = None
        for name in wb.sheetnames:
            if "payout" in name.lower() or "winning" in name.lower() or "prize" in name.lower():
                target_sheet = name
                break
        if not target_sheet:
            target_sheet = wb.sheetnames[0]

        ws = wb[target_sheet]
        rows = []
        for r in ws.iter_rows(values_only=True):
            if any(cell is not None and str(cell).strip() != "" for cell in r):
                cleaned_row = [str(c).strip() if c is not None else "" for c in r]
                rows.append(cleaned_row)

        return {"filename": target_file, "sheet": target_sheet, "rows": rows}, None
    except Exception as err:
        return None, str(err)


# ---------------------------------------------------------
# TAB 4: RULES, SCORING & HELP CENTER (SEARCHABLE)
# ---------------------------------------------------------
def build_help_center_tab(page: ft.Page) -> ft.Control:
    # 1. KEEPER PROGRESSION DATA TABLES
    offense_rows = [
        ("1", "1", "1", "1", "1", "1", "1", "1"),
        ("2", "2", "1", "1", "1", "1", "1", "1"),
        ("3", "3", "1", "1", "1", "1", "1", "1"),
        ("4", "4", "1", "1", "1", "1", "1", "1"),
        ("5", "5", "2", "1", "1", "1", "1", "1"),
        ("6", "6", "2", "1", "1", "1", "1", "1"),
        ("7", "7", "3", "1", "1", "1", "1", "1"),
        ("8", "8", "3", "1", "1", "1", "1", "1"),
        ("9", "9", "4", "2", "1", "1", "1", "1"),
        ("10", "10", "4", "2", "1", "1", "1", "1"),
        ("11", "11", "5", "3", "1", "1", "1", "1"),
        ("12", "12", "5", "3", "1", "1", "1", "1"),
        ("13", "13", "6", "4", "2", "1", "1", "1"),
        ("14", "14", "6", "4", "2", "1", "1", "1"),
        ("15", "15", "6", "4", "2", "1", "1", "1"),
        ("16", "16", "6", "4", "2", "1", "1", "1"),
        ("17", "17", "7", "5", "3", "1", "1", "1"),
        ("18", "18", "7", "5", "3", "1", "1", "1"),
        ("19", "19", "8", "6", "4", "2", "1", "1"),
        ("20", "20", "8", "6", "4", "2", "1", "1"),
        ("21", "21", "9", "7", "5", "3", "1", "1"),
        ("22", "22", "9", "7", "5", "3", "1", "1"),
        ("23", "23", "10", "8", "6", "4", "2", "1"),
        ("24", "24", "10", "8", "6", "4", "2", "1"),
    ]

    dt_offense = ft.DataTable(
        heading_row_color=BG_SURFACE_LIGHT,
        columns=[
            ft.DataColumn(ft.Text("INITIAL DRAFT", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
            ft.DataColumn(ft.Text("2ND YEAR (1st Kept)", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("3RD YEAR (2nd Kept)", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("4th YEAR (3rd Kept)", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("5th YEAR", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("6th YEAR", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("7th YEAR", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("8th YEAR", weight=ft.FontWeight.BOLD)),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(r[0], weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
                    *[ft.DataCell(ft.Text(v)) for v in r[1:]],
                ]
            )
            for r in offense_rows
        ] + [
            ft.DataRow(
                color=BG_SURFACE_LIGHT,
                cells=[
                    ft.DataCell(ft.Text("RULE:", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
                    ft.DataCell(ft.Text("Same Round", italic=True)),
                    ft.DataCell(ft.Text("(Prior/2)-1 or -2", italic=True, color=ACCENT_AMBER)),
                    ft.DataCell(ft.Text("Prior - 2", italic=True)),
                    ft.DataCell(ft.Text("Prior - 2", italic=True)),
                    ft.DataCell(ft.Text("Prior - 2", italic=True)),
                    ft.DataCell(ft.Text("Prior - 2", italic=True)),
                    ft.DataCell(ft.Text("Prior - 2", italic=True)),
                ],
            )
        ],
        column_spacing=18,
    )

    defense_rows = [
        ("1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"),
        ("2", "2", "1", "1", "1", "1", "1", "1", "1", "1", "1"),
        ("3", "3", "1", "1", "1", "1", "1", "1", "1", "1", "1"),
        ("4", "4", "2", "1", "1", "1", "1", "1", "1", "1", "1"),
        ("5", "5", "3", "1", "1", "1", "1", "1", "1", "1", "1"),
        ("6", "6", "4", "2", "1", "1", "1", "1", "1", "1", "1"),
        ("7", "7", "4", "2", "1", "1", "1", "1", "1", "1", "1"),
        ("8", "8", "5", "3", "1", "1", "1", "1", "1", "1", "1"),
        ("9", "9", "6", "4", "2", "1", "1", "1", "1", "1", "1"),
        ("10", "10", "7", "5", "3", "1", "1", "1", "1", "1", "1"),
        ("11", "11", "7", "5", "3", "1", "1", "1", "1", "1", "1"),
        ("12", "12", "8", "6", "4", "2", "1", "1", "1", "1", "1"),
        ("13", "13", "9", "7", "5", "3", "1", "1", "1", "1", "1"),
        ("14", "14", "9", "7", "5", "3", "1", "1", "1", "1", "1"),
        ("15", "15", "9", "7", "5", "3", "1", "1", "1", "1", "1"),
        ("16", "16", "10", "8", "6", "4", "2", "1", "1", "1", "1"),
        ("17", "17", "11", "9", "7", "5", "3", "1", "1", "1", "1"),
        ("18", "18", "12", "10", "8", "6", "4", "2", "1", "1", "1"),
        ("19", "19", "12", "10", "8", "6", "4", "2", "1", "1", "1"),
        ("20", "20", "13", "11", "9", "7", "5", "3", "1", "1", "1"),
        ("21", "21", "14", "12", "10", "8", "6", "4", "2", "1", "1"),
        ("22", "22", "15", "13", "11", "9", "7", "5", "3", "1", "1"),
        ("23", "23", "15", "13", "11", "9", "7", "5", "3", "1", "1"),
        ("24", "24", "16", "14", "12", "10", "8", "6", "4", "2", "1"),
    ]

    dt_defense = ft.DataTable(
        heading_row_color=BG_SURFACE_LIGHT,
        columns=[
            ft.DataColumn(ft.Text("INITIAL DRAFT", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
            ft.DataColumn(ft.Text("2ND YR (1st)")),
            ft.DataColumn(ft.Text("3RD YR (2nd)")),
            ft.DataColumn(ft.Text("4th YR")),
            ft.DataColumn(ft.Text("5th YR")),
            ft.DataColumn(ft.Text("6th YR")),
            ft.DataColumn(ft.Text("7th YR")),
            ft.DataColumn(ft.Text("8th YR")),
            ft.DataColumn(ft.Text("9th YR")),
            ft.DataColumn(ft.Text("10th YR")),
            ft.DataColumn(ft.Text("11th YR")),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(r[0], weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
                    *[ft.DataCell(ft.Text(v)) for v in r[1:]],
                ]
            )
            for r in defense_rows
        ] + [
            ft.DataRow(
                color=BG_SURFACE_LIGHT,
                cells=[
                    ft.DataCell(ft.Text("RULE:", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
                    ft.DataCell(ft.Text("Same Round", italic=True)),
                    ft.DataCell(ft.Text("Prior-(P/4)-1/2", italic=True, color=ACCENT_AMBER)),
                    *[ft.DataCell(ft.Text("Prior - 2", italic=True)) for _ in range(8)],
                ],
            )
        ],
        column_spacing=12,
    )

    # 2. OFFICIAL PAYOUT TABLE (SYNCED WITH WORKSHEET)
    dt_official_payout = ft.DataTable(
        heading_row_color=BG_SURFACE_LIGHT,
        columns=[
            ft.DataColumn(ft.Text("Category / Award", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
            ft.DataColumn(ft.Text("Payout Amount", weight=ft.FontWeight.BOLD, color=COLOR_GREEN)),
            ft.DataColumn(ft.Text("Play Type / Qualification Rules", weight=ft.FontWeight.BOLD)),
        ],
        rows=[
            ft.DataRow(cells=[ft.DataCell(ft.Text("Super Bowl Winner", weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("$500.00", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Postseason Champion"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Season Point Leader", weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("$215.00", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Regular Season play only"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Top Offense Bonus")), ft.DataCell(ft.Text("$75.00", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Regular Season play only"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Top Defense Bonus")), ft.DataCell(ft.Text("$75.00", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Regular Season play only"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Top Special Teams Bonus")), ft.DataCell(ft.Text("$25.00", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Regular Season play only"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Weekly Highest Points Winner")), ft.DataCell(ft.Text("$10.00 / wk", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Regular Season play only"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Playoffs (Round 1) Bonus")), ft.DataCell(ft.Text("$10.00", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Rewarded by clinching Round 1"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Playoffs (Round 2) Bonus")), ft.DataCell(ft.Text("$15.00", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Rewarded by clinching Round 2"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Playoffs (Round 3) Bonus")), ft.DataCell(ft.Text("$25.00", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Rewarded by clinching Round 3"))]),
            ft.DataRow(
                color=BG_SURFACE_LIGHT,
                cells=[
                    ft.DataCell(ft.Text("TOTAL PRIZE POT", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
                    ft.DataCell(ft.Text("$1,200.00", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text("12 Players × $100 Entry Fee", weight=ft.FontWeight.BOLD)),
                ],
            ),
        ],
        column_spacing=18,
    )

    payout_info, _ = load_payouts_from_excel()
    excel_live_display = []
    if payout_info and payout_info.get("rows"):
        p_rows = payout_info["rows"]
        headers = [str(c) if str(c) != "" else f"Col {idx+1}" for idx, c in enumerate(p_rows[0])]
        data_rows = p_rows[1:]
        max_cols = max(len(r) for r in p_rows)

        columns = [ft.DataColumn(ft.Text(h, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)) for h in headers]
        if len(columns) < max_cols:
            for i in range(len(columns), max_cols):
                columns.append(ft.DataColumn(ft.Text(f"Col {i+1}", weight=ft.FontWeight.BOLD)))

        payout_data_rows = []
        for r in data_rows:
            padded_row = list(r) + [""] * (max_cols - len(r))
            payout_data_rows.append(
                ft.DataRow(cells=[ft.DataCell(ft.Text(str(val))) for val in padded_row[:max_cols]])
            )

        dt_excel = ft.DataTable(
            heading_row_color=BG_SURFACE_LIGHT,
            columns=columns,
            rows=payout_data_rows,
            column_spacing=15,
        )
        excel_live_display = [
            ft.Divider(height=15),
            ft.Text(f"📊 Live Workbook Ledger (Sheet: '{payout_info['sheet']}'):", color=COLOR_GREEN, weight=ft.FontWeight.BOLD),
            ft.Row([dt_excel], scroll=ft.ScrollMode.ADAPTIVE),
        ]

    # 3. INTERACTIVE DRAFT POSITION BUILDER (DEFAULT CONSOLATION CHAMP TO #1)
    dt_draft_reference = ft.DataTable(
        heading_row_color=BG_SURFACE_LIGHT,
        columns=[
            ft.DataColumn(ft.Text("Ranked Team", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
            ft.DataColumn(ft.Text("Draft Slot Range", weight=ft.FontWeight.BOLD, color=COLOR_GREEN)),
            ft.DataColumn(ft.Text("Selection / Shifting Rule", weight=ft.FontWeight.BOLD)),
        ],
        rows=[
            ft.DataRow(cells=[ft.DataCell(ft.Text("7th (Consolation Champ)", weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("1 - 12 (Default: #1)", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Can choose any position; all other teams shift accordingly."))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("8th")), ft.DataCell(ft.Text("1 or 2")), ft.DataCell(ft.Text("1st available non-champ slot"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("9th")), ft.DataCell(ft.Text("2 or 3")), ft.DataCell(ft.Text("2nd available non-champ slot"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("10th")), ft.DataCell(ft.Text("3 or 4")), ft.DataCell(ft.Text("3rd available non-champ slot"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("11th")), ft.DataCell(ft.Text("4 or 5")), ft.DataCell(ft.Text("4th available non-champ slot"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("12th")), ft.DataCell(ft.Text("5 or 6")), ft.DataCell(ft.Text("5th available non-champ slot"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("2nd (Super Bowl Runner-Up)")), ft.DataCell(ft.Text("6 or 7")), ft.DataCell(ft.Text("6th available non-champ slot"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("3rd")), ft.DataCell(ft.Text("7 or 8")), ft.DataCell(ft.Text("7th available non-champ slot"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("4th")), ft.DataCell(ft.Text("8 or 9")), ft.DataCell(ft.Text("8th available non-champ slot"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("5th")), ft.DataCell(ft.Text("9 or 10")), ft.DataCell(ft.Text("9th available non-champ slot"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("6th")), ft.DataCell(ft.Text("10 or 11")), ft.DataCell(ft.Text("10th available non-champ slot"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("1st (Super Bowl Champ)", weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("11 or 12", color=ACCENT_AMBER)), ft.DataCell(ft.Text("Last available non-champ slot"))]),
        ],
        column_spacing=18,
    )

    draft_board_column = ft.Column(spacing=6)

    def update_draft_board(champ_choice_str="1"):
        draft_board_column.controls.clear()
        try:
            choice = int(champ_choice_str)
        except (ValueError, TypeError):
            choice = 1

        ordered_ranks = [
            ("8th Place", "Consolation Participant"),
            ("9th Place", "Consolation Participant"),
            ("10th Place", "Consolation Participant"),
            ("11th Place", "Consolation Participant"),
            ("12th Place", "Consolation Participant"),
            ("2nd Place", "Super Bowl Runner-Up"),
            ("3rd Place", "Playoff Semifinalist"),
            ("4th Place", "Playoff Semifinalist"),
            ("5th Place", "Playoff Quarterfinalist"),
            ("6th Place", "Playoff Quarterfinalist"),
            ("1st Place", "Super Bowl Champion"),
        ]

        board = [None] * 12
        champ_idx = max(0, min(11, choice - 1))
        board[champ_idx] = ("7th Place (Consolation Champion)", "Defaulted / Chosen Slot", True)

        team_idx = 0
        for slot_idx in range(12):
            if board[slot_idx] is None:
                r_title, r_desc = ordered_ranks[team_idx]
                board[slot_idx] = (r_title, r_desc, False)
                team_idx += 1

        dt_simulated_board = ft.DataTable(
            heading_row_color=BG_SURFACE_LIGHT,
            columns=[
                ft.DataColumn(ft.Text("Draft Slot #", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
                ft.DataColumn(ft.Text("Team Entitled to Pick", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Shift Status / Context", weight=ft.FontWeight.BOLD)),
            ],
            rows=[
                ft.DataRow(
                    color=BG_SURFACE_LIGHT if is_champ else None,
                    cells=[
                        ft.DataCell(ft.Text(f"Pick #{i+1}", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER if is_champ else None)),
                        ft.DataCell(ft.Text(team_title, weight=ft.FontWeight.BOLD if is_champ else None, color=COLOR_GREEN if is_champ else None)),
                        ft.DataCell(ft.Text(desc, italic=True)),
                    ]
                )
                for i, (team_title, desc, is_champ) in enumerate(board)
            ],
            column_spacing=18,
        )

        draft_board_column.controls.append(ft.Row([dt_simulated_board], scroll=ft.ScrollMode.ADAPTIVE))
        page.update()

    dd_champ_choice = ft.Dropdown(
        label="Consolation Champ Selected Slot (Default: #1)",
        value="1",
        options=[create_option(str(i), f"Draft Slot #{i}" + (" (Default)" if i == 1 else "")) for i in range(1, 13)],
        width=260,
    )
    dd_champ_choice.on_change = lambda e: update_draft_board(dd_champ_choice.value)
    if hasattr(dd_champ_choice, "on_select"):
        dd_champ_choice.on_select = lambda e: update_draft_board(dd_champ_choice.value)

    update_draft_board("1")

    # 4. ANNUAL DIVISION REALIGNMENT BUILDER (THE BAD VS. THE UGLY)
    dt_div_rules = ft.DataTable(
        heading_row_color=BG_SURFACE_LIGHT,
        columns=[
            ft.DataColumn(ft.Text("Step #", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
            ft.DataColumn(ft.Text("Team Ranks Paired", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Assigned Division", weight=ft.FontWeight.BOLD, color=COLOR_GREEN)),
            ft.DataColumn(ft.Text("Rationale / Pairing Context", weight=ft.FontWeight.BOLD)),
        ],
        rows=[
            ft.DataRow(cells=[ft.DataCell(ft.Text("Step 1")), ft.DataCell(ft.Text("#1 & #7", weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("THE BAD", color=ACCENT_AMBER, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Super Bowl Champ & Consolation Champ"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Step 2")), ft.DataCell(ft.Text("#2 & #3", weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("THE UGLY", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Super Bowl Runner-Up & 3rd Place"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Step 3")), ft.DataCell(ft.Text("#4 & #5", weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("THE BAD", color=ACCENT_AMBER, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("4th & 5th Place Finishers"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Step 4")), ft.DataCell(ft.Text("#6 & #8", weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("THE UGLY", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("6th Place & Consolation Runner-Up"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Step 5")), ft.DataCell(ft.Text("#9 & #10", weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("THE BAD", color=ACCENT_AMBER, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("9th & 10th Place Finishers"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Step 6")), ft.DataCell(ft.Text("#11 & #12", weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("THE UGLY", color=COLOR_GREEN, weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text("Bottom Two Finishers (11th & 12th)"))]),
        ],
        column_spacing=18,
    )

    # Current sample standings for live in-season preview
    current_league_teams = [
        (1, "TBone Diva Manglers"),
        (2, "Samurai"),
        (3, "MotorBoaters"),
        (4, "Jack Wagons"),
        (5, "RAZINUDOWN"),
        (6, "Wild Card"),
        (7, "SilentXecution"),
        (8, "Ninja"),
        (9, "The Cinderella Boyz"),
        (10, "The Mad Scientist Syndicate"),
        (11, "Super Saiyan"),
        (12, "TD Master"),
    ]

    the_bad_ranks = [1, 4, 5, 7, 9, 10]
    the_ugly_ranks = [2, 3, 6, 8, 11, 12]

    dt_the_bad = ft.DataTable(
        heading_row_color=BG_SURFACE_LIGHT,
        columns=[
            ft.DataColumn(ft.Text("Rank", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
            ft.DataColumn(ft.Text("Team Name (The Bad)", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER)),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(f"#{r}", weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(next((name for rank, name in current_league_teams if rank == r), f"Rank {r}"))),
            ])
            for r in the_bad_ranks
        ],
        column_spacing=18,
    )

    dt_the_ugly = ft.DataTable(
        heading_row_color=BG_SURFACE_LIGHT,
        columns=[
            ft.DataColumn(ft.Text("Rank", weight=ft.FontWeight.BOLD, color=COLOR_GREEN)),
            ft.DataColumn(ft.Text("Team Name (The Ugly)", weight=ft.FontWeight.BOLD, color=COLOR_GREEN)),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(f"#{r}", weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(next((name for rank, name in current_league_teams if rank == r), f"Rank {r}"))),
            ])
            for r in the_ugly_ranks
        ],
        column_spacing=18,
    )

    # 5. KNOWLEDGE BASE ARTICLES (STRICT GROUPING & ORDERING)
    articles = [
        # --- 1. LEAGUE SETUP ---
        {
            "category": "Setup",
            "title": "League Structure & Format",
            "keywords": "setup format 12 teams divisions head to head h2h scoring week 1 fractional negative yahoo",
            "controls": [
                ft.Text("• League Size: 12 Teams across 2 Divisions (The Bad & The Ugly)."),
                ft.Text("• Format: Head-to-Head weekly matchups beginning Week 1."),
                ft.Text("• Scoring Modifiers: Fractional and negative points active across all positions."),
                ft.Text("• Can't Cut List: None (commissioner and managers retain full roster control)."),
            ],
        },
        {
            "category": "Setup",
            "title": "Annual Division Realignment (The Bad vs. The Ugly)",
            "keywords": "setup division divisions realignment building bad ugly ranks 1 4 5 7 9 10 2 3 6 8 11 12 pairing",
            "controls": [
                ft.Text("Official Division Building Rules (6-Step System)", size=17, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER),
                ft.Text("Each season, the two divisions are realigned based on the final end-of-year standings using this balanced pairing system:"),
                ft.Row([dt_div_rules], scroll=ft.ScrollMode.ADAPTIVE),
                ft.Divider(height=15),
                ft.Text("Live In-Season Realignment Projection (Based on Current Ranks)", size=17, weight=ft.FontWeight.BOLD, color=COLOR_GREEN),
                ft.Text("Updates live through the season based on current league standings (Syncs automatically once Yahoo is connected):", italic=True),
                ft.Row(
                    [
                        ft.Column([
                            ft.Text("DIVISION 1: THE BAD (Sum of Ranks = 36)", size=15, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER),
                            dt_the_bad,
                        ], spacing=6),
                        ft.Column([
                            ft.Text("DIVISION 2: THE UGLY (Sum of Ranks = 42)", size=15, weight=ft.FontWeight.BOLD, color=COLOR_GREEN),
                            dt_the_ugly,
                        ], spacing=6),
                    ],
                    wrap=True,
                    spacing=20,
                ),
            ],
        },
        {
            "category": "Setup",
            "title": "Roster Slots & Lineup Requirements (24 Total)",
            "keywords": "setup roster composition starters bench ir slots flex position lineup 15 starters 9 bench 2 ir",
            "controls": [
                ft.Text("• Total Active Roster: 24 players."),
                ft.Text("• 15 Starters: 1 QB, 2 WR, 2 RB, 1 TE, 1 W/R/T (Offensive Flex), 1 K, 1 D (Defensive Flex), 2 LB, 1 DT, 1 DE, 1 CB, 1 S.", weight=ft.FontWeight.BOLD),
                ft.Text("• 9 Bench Spots: Max 6 per side of ball (Offense, Defense, Special Teams)."),
                ft.Text("• 2 IR Slots: Eligible for Yahoo-designated IR players and postponed games (players can be added directly from waivers/FA)."),
            ],
        },
        {
            "category": "Setup",
            "title": "Waivers & Free Agency System (FAAB)",
            "keywords": "setup waivers faab fab bidding budget claims rolling continuous schedule tuesday claim period",
            "controls": [
                ft.Text("• System: FAAB (FAB with continual rolling list tiebreak)."),
                ft.Text("• Weekly Schedule: Game Time through Tuesday morning."),
                ft.Text("• Waiver Claim Window: 2 days (Follows standard waiver rules post-draft)."),
                ft.Text("• Transaction Limits: No seasonal or weekly maximum caps on acquisitions or trades."),
            ],
        },
        {
            "category": "Setup",
            "title": "Playoff Structure & Seeding System",
            "keywords": "setup playoffs postseason seeds byes reseeding tiebreaker consolation weeks 15 16 17",
            "controls": [
                ft.Text("• Playoff Teams: 6 teams qualify for the Championship Bracket."),
                ft.Text("• Postseason Schedule: Weeks 15, 16, and 17."),
                ft.Text("• Seeding: Division winners receive top playoff seeds (#1 and #2 with first-round byes)."),
                ft.Text("• Reseeding: Active each round."),
                ft.Text("• Tie-Breaker: Best regular-season record vs. opponent wins."),
                ft.Text("• Consolation Tournament: 6 non-playoff teams compete for the #1 draft pick choice privilege."),
            ],
        },

        # --- 2. POSITION SCORING (INDIVIDUAL POSITIONS FIRST) ---
        {
            "category": "Scoring",
            "title": "Quarterback (QB) Scoring",
            "keywords": "scoring qb quarterback passing yards touchdowns interceptions pick six rush rushing bonus 200 300 400",
            "controls": [
                ft.Text("• Passing Yards: 20 yards per point (0.05 pts/yd)."),
                ft.Text("• Passing Milestones: +1 pt bonus at 200 yds, +1 pt at 300 yds, +1 pt at 400 yds.", color=ACCENT_AMBER),
                ft.Text("• Passing Touchdowns: 4 pts."),
                ft.Text("• 40+ Yard Passing Bonuses: +0.5 pt for 40+ completion; +1 pt for 40+ passing TD."),
                ft.Text("• Interceptions: -1 pt (-2 pts if returned for Pick-Six)."),
                ft.Text("• Rushing Yards: 10 yards per point (0.1 pts/yd; +1 bonus at 80, 100, 150 yds)."),
                ft.Text("• Rushing Touchdowns: 6 pts (+0.5 pt bonus for 40+ run; +1 pt for 40+ rush TD)."),
                ft.Text("• Turnovers: -0.5 pt for fumble; -2 pts for fumble lost."),
            ],
        },
        {
            "category": "Scoring",
            "title": "Running Back (RB) Scoring",
            "keywords": "scoring rb running back rushing ppr receptions receiving return yards touchdowns 40 yard bonus",
            "controls": [
                ft.Text("• Receptions: 1.0 point per reception (Full PPR).", weight=ft.FontWeight.BOLD, color=COLOR_GREEN),
                ft.Text("• Rushing Yards: 10 yards per point (0.1 pts/yd; +1 bonus at 80, 100, 150 yds)."),
                ft.Text("• Rushing Touchdowns: 6 pts (+0.5 pt bonus for 40+ run; +1 pt for 40+ rush TD)."),
                ft.Text("• Receiving Yards: 10 yards per point (0.1 pts/yd; +1 bonus at 100, 150, 200 yds)."),
                ft.Text("• Receiving Touchdowns: 6 pts (+0.5 pt bonus for 40+ catch; +1 pt for 40+ rec TD)."),
                ft.Text("• Return Yards: 15 yards per point (+1 bonus at 50, 75, 125 yds; 6 pts per return TD)."),
                ft.Text("• Fumbles: -0.5 pt for fumble; -2 pts for fumble lost."),
            ],
        },
        {
            "category": "Scoring",
            "title": "Wide Receiver (WR) Scoring",
            "keywords": "scoring wr wide receiver receptions ppr receiving return yards touchdowns 40 yard bonus",
            "controls": [
                ft.Text("• Receptions: 1.0 point per reception (Full PPR).", weight=ft.FontWeight.BOLD, color=COLOR_GREEN),
                ft.Text("• Receiving Yards: 10 yards per point (0.1 pts/yd; +1 bonus at 100, 150, 200 yds)."),
                ft.Text("• Receiving Touchdowns: 6 pts (+0.5 pt bonus for 40+ catch; +1 pt for 40+ rec TD)."),
                ft.Text("• Rushing: 10 yds/pt (+1 bonus at 80, 100, 150 yds; 6 pts per rush TD)."),
                ft.Text("• Return Yards: 15 yards per point (+1 bonus at 50, 75, 125 yds; 6 pts per return TD)."),
                ft.Text("• 2-Point Conversions: 2 pts."),
                ft.Text("• Fumbles: -0.5 pt for fumble; -2 pts for fumble lost."),
            ],
        },
        {
            "category": "Scoring",
            "title": "Tight End (TE) Scoring",
            "keywords": "scoring te tight end receptions ppr receiving touchdowns 40 yard bonus",
            "controls": [
                ft.Text("• Receptions: 1.0 point per reception (Full PPR).", weight=ft.FontWeight.BOLD, color=COLOR_GREEN),
                ft.Text("• Receiving Yards: 10 yards per point (0.1 pts/yd; +1 bonus at 100, 150, 200 yds)."),
                ft.Text("• Receiving Touchdowns: 6 pts (+0.5 pt bonus for 40+ catch; +1 pt for 40+ rec TD)."),
                ft.Text("• Rushing & 2-Pt Conversions: 10 yds/pt; 6 pts per rush TD; 2 pts per 2-PT conversion."),
                ft.Text("• Fumbles: -0.5 pt for fumble; -2 pts for fumble lost."),
            ],
        },
        {
            "category": "Scoring",
            "title": "Kicker (K) Scoring",
            "keywords": "scoring k kicker field goal pat point after missed extra point 40 50 fg",
            "controls": [
                ft.Text("• Field Goals Made:"),
                ft.Text("   - 0–39 Yards: 3 pts"),
                ft.Text("   - 40–49 Yards: 4 pts"),
                ft.Text("   - 50+ Yards: 5 pts"),
                ft.Text("• Field Goals Missed: -1 pt (0–19 yds); -0.5 pts (20–29 yds); 0 pts (30+ yds)."),
                ft.Text("• Extra Points (PAT): 1 pt made; -1 pt missed."),
            ],
        },
        {
            "category": "Scoring",
            "title": "Defensive Line (DE & DT) Scoring",
            "keywords": "scoring de dt defensive end defensive tackle sacks tackles tfl fumbles safety blocked kick idp",
            "controls": [
                ft.Text("• Solo Tackle: 1.5 pts | Assisted Tackle: 0.75 pts."),
                ft.Text("• Sacks & TFL: 1.0 pt per Sack; 1.0 pt per Tackle for Loss (TFL)."),
                ft.Text("• Big Plays: Forced Fumble (2 pts), Fumble Recovery (1 pt), Blocked Kick (2 pts), Safety (2 pts)."),
                ft.Text("• Touchdowns & Returns: Defensive TD (6 pts); Turnover Return Yards (15 yds/pt); Extra Point Returned (2 pts)."),
            ],
        },
        {
            "category": "Scoring",
            "title": "Linebacker (LB) Scoring",
            "keywords": "scoring lb linebacker solo tackle assist sack interception pass defended tfl idp",
            "controls": [
                ft.Text("• Solo Tackle: 1.5 pts | Assisted Tackle: 0.75 pts."),
                ft.Text("• Sacks & TFL: 1.0 pt per Sack; 1.0 pt per Tackle for Loss (TFL)."),
                ft.Text("• Coverage: Interception (3 pts); Pass Defended (2 pts)."),
                ft.Text("• Big Plays: Forced Fumble (2 pts); Recovery (1 pt); Defensive TD (6 pts); Safety (2 pts)."),
                ft.Text("• Turnover Return Yards: 15 yards per point."),
            ],
        },
        {
            "category": "Scoring",
            "title": "Secondary (CB & S) Scoring",
            "keywords": "scoring cb s corner cornerback safety defensive back interception pass defended tackle idp",
            "controls": [
                ft.Text("• Interceptions: 3 pts | Passes Defended: 2 pts."),
                ft.Text("• Solo Tackle: 1.5 pts | Assisted Tackle: 0.75 pts."),
                ft.Text("• Sacks & TFL: 1.0 pt per Sack; 1.0 pt per Tackle for Loss (TFL)."),
                ft.Text("• Big Plays: Forced Fumble (2 pts); Recovery (1 pt); Blocked Kick / Safety (2 pts each)."),
                ft.Text("• Touchdowns: Defensive TD (6 pts); Extra Point Returned (2 pts); Turnover Return (15 yds/pt)."),
            ],
        },

        # --- 2B. CUMULATIVE & STACKING SCORING (DIRECTLY AFTER INDIVIDUAL POSITIONS) ---
        {
            "category": "Scoring",
            "title": "Cumulative & Stacking Points (Sacks, Big Plays & 40+ Bonuses)",
            "keywords": "scoring cumulative stacking stack sack sacks tfl tackle for loss solo tackle bonus 40 yard pick-six strip sack add on add-on",
            "controls": [
                ft.Text("How Cumulative (Add-On) Scoring Works in NPK", size=17, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER),
                ft.Text("In Yahoo Fantasy IDP and NPK rules, statistical events on a single play stack cumulatively. A sack is not an isolated event; it is officially recorded as an unassisted tackle of a quarterback behind the line of scrimmage."),
                ft.Divider(height=10),
                ft.Text("The Solo Sack Breakdown (3.5 Points Total):", weight=ft.FontWeight.BOLD),
                ft.Text("• Solo Tackle: +1.5 pts (bringing down the ball carrier)"),
                ft.Text("• Tackle for Loss (TFL): +1.0 pt (tackle made behind the line of scrimmage)"),
                ft.Text("• Sack: +1.0 pt (tackle made on the QB attempting to pass)"),
                ft.Text("➡️ Cumulative Total for 1 Solo Sack = 3.5 Fantasy Points!", color=COLOR_GREEN, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),
                ft.Text("Assisted (Half) Sack: Tackle Assist (+0.75) + Half Sack (+0.50) = 1.25 pts (or 1.75 pts if half TFL credited)."),
                ft.Text("Strip-Sack & Recovery: Solo Sack (3.5) + Forced Fumble (+2.0) + Fumble Recovery (+1.0) = 6.5 pts (+6.0 pts if returned for TD)."),
                ft.Divider(height=10),
                ft.Text("Offensive Stacking Examples:", weight=ft.FontWeight.BOLD),
                ft.Text("• 40+ Yard Passing TD (45 yds): Yards (2.25) + Pass TD (4.0) + 40+ Completion (+0.5) + 40+ Pass TD (+1.0) = 7.75 pts."),
                ft.Text("• 40+ Yard Rushing TD (45 yds): Yards (4.5) + Rush TD (6.0) + 40+ Run (+0.5) + 40+ Rush TD (+1.0) = 12.0 pts."),
                ft.Text("• 40+ Yard Receiving TD (45 yds): Full PPR (1.0) + Yards (4.5) + Rec TD (6.0) + 40+ Rec (+0.5) + 40+ Rec TD (+1.0) = 13.0 pts."),
                ft.Text("• Pick-Six Thrown: Interception (-1.0) + Pick-Six (-2.0) = -3.0 pts total."),
                ft.Text("• Fumbles Lost: Fumble (-0.5) + Fumble Lost (-2.0) = -2.5 pts total."),
            ],
        },

        # --- 3. KEEPERS & RECREATED TABLES ---
        {
            "category": "Keepers",
            "title": "Official Offense Keeper Table (8-Year Progression)",
            "keywords": "keeper offense table chart progression multi-year rounds initial draft 2nd 3rd 4th 5th 6th 7th 8th",
            "controls": [
                ft.Text("OFFENSE KEEPER TABLE", size=18, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER),
                ft.Text("(2nd row is years on roster, 2nd year = 1st time as keeper)", italic=True),
                ft.Row([dt_offense], scroll=ft.ScrollMode.ADAPTIVE),
            ],
        },
        {
            "category": "Keepers",
            "title": "Official Defense Keeper Table (11-Year Progression)",
            "keywords": "keeper defense table chart progression multi-year rounds initial draft 11 years idp",
            "controls": [
                ft.Text("DEFENSE KEEPER TABLE", size=18, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER),
                ft.Text("(2nd row is years on roster, 2nd year = 1st time as keeper)", italic=True),
                ft.Row([dt_defense], scroll=ft.ScrollMode.ADAPTIVE),
            ],
        },
        {
            "category": "Keepers",
            "title": "Keeper Allocation Limits & Rounds 1–4 Cap",
            "keywords": "keepers amount max 4 allocation rounds 1-4 first four rounds limit",
            "controls": [
                ft.Text("• Maximum Keepers: Teams may keep up to 4 players (0, 1, 2, 3, or 4)."),
                ft.Text("• Positional Allocation Caps:"),
                ft.Text("   - 1 Keeper: Choose from Offense, Defense, or Special Teams."),
                ft.Text("   - 2 Keepers: Maximum of 1 from Offense, Defense, or Special Teams."),
                ft.Text("   - 3 or 4 Keepers: Maximum of 2 from Offense, Defense, or Special Teams."),
                ft.Text("• Rounds 1–4 Rule: A manager may keep only ONE player who costs a Round 1–4 draft pick.", color=ACCENT_AMBER, weight=ft.FontWeight.BOLD),
                ft.Text("• Traded / Dropped Player Reset: If a player is traded and kept, or dropped and claimed by a new team, that player resets to Year 2 (kept where drafted previous season).", color=COLOR_GREEN),
            ],
        },
        {
            "category": "Keepers",
            "title": "Keeper Draft Pick Cost Calculations & Undrafted Formulas",
            "keywords": "keepers cost undrafted 13th 20th 12th 19th reset traded dropped free agent math calculation year",
            "controls": [
                ft.Text("• 1st Year Kept (2nd Year on Team): Costs round drafted previous season."),
                ft.Text("• Undrafted Free Agents:"),
                ft.Text("   - Offense: 13th round (1st kept), 12th round (2nd kept)."),
                ft.Text("   - Defense: 20th round (1st kept), 19th round (2nd kept)."),
                ft.Text("• 2nd Year as Keeper (3rd Year on Team):"),
                ft.Text("   - Offense: (Prior Round / 2) - 1 (if prior 1-14) or - 2 (if prior 15-24). Round down."),
                ft.Text("   - Defense: Prior Round - (Prior / 4) - 1 (if prior 1-13) or - 2 (if prior 14-24). Round down."),
                ft.Text("• 3rd+ Time Kept (4th+ Year on Team): Subtract 2 from prior round (Floor = Round 1)."),
            ],
        },

        # --- 4. FINANCES & DRAFT ---
        {
            "category": "Finances",
            "title": "Entry Fees, Deadlines & Guarantee Policy",
            "keywords": "finances money buy in buy-in fee deadline august freeze replace cost cash 100",
            "controls": [
                ft.Text("• Buy-In: $100 per team."),
                ft.Text("• Due Date: Entry fee deadlines are communicated via email or posted on the league tab (typically around August 1)."),
                ft.Text("• Payment Arrangements: Special payment arrangements are only valid with commissioner approval. The commissioner is solely responsible for guaranteeing league funds."),
                ft.Text("• Non-Payment Penalty: If fee or arrangement is not received by the deadline, the team is frozen for 3 days, after which the franchise may be reassigned to a replacement owner.", color=COLOR_RED),
            ],
        },
        {
            "category": "Draft",
            "title": "Draft Guidelines, Schedule & Slot Selection",
            "keywords": "draft snake consolation order tournament pick time date schedule rounds 24",
            "controls": [
                ft.Text("• Draft Format: Snake style draft (24 rounds)."),
                ft.Text("• Annual Schedule: Draft times and dates are set each season by the commissioner, published directly inside the app, and texted to all team managers."),
                ft.Text("• Consolation Champion Privilege: The Winner of the Consolation Tournament receives the choice of their draft position (deadline to select is typically one week prior to the draft). Defaults to #1 overall pick.", color=ACCENT_AMBER, weight=ft.FontWeight.BOLD),
                ft.Text("• Consolation Ranks (Picks 2–6): The remaining 5 consolation tournament participants fill the next highest available draft positions based on rank."),
                ft.Text("• Championship Finishers (Picks 7–12): Championship bracket participants draft in the lowest 6 slots based on final playoff finish (12th: Super Bowl Winner; 11th: Runner-Up; 9th/10th: 3rd place game; 7th/8th: 5th place game)."),
            ],
        },
        {
            "category": "Draft",
            "title": "Draft Position Builder & Standings Shift Simulator",
            "keywords": "draft position builder shift consolation champ choice 1-12 simulator standings order board pick 1",
            "controls": [
                ft.Text("Official Draft Position Determination Table", size=17, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER),
                ft.Text("The 7th-Place Consolation Champion can choose ANY position from 1 to 12 (Defaults to #1). All other teams shift into the remaining slots in strict order:", italic=True),
                ft.Row([dt_draft_reference], scroll=ft.ScrollMode.ADAPTIVE),
                ft.Divider(height=15),
                ft.Text("Interactive Draft Order Simulator", size=17, weight=ft.FontWeight.BOLD, color=COLOR_GREEN),
                ft.Text("Select which slot the Consolation Champ picks (Defaults to #1; only changes if alternate slot is chosen):"),
                dd_champ_choice,
                draft_board_column,
            ],
        },

        # --- 5. BENCH & IR ---
        {
            "category": "Bench & IR",
            "title": "Bench Capacity & Positional Limit (Max 6 Per Side)",
            "keywords": "bench limit max 6 offense defense special teams position roster illegal violation",
            "controls": [
                ft.Text("• Total Bench Spots: 9 bench positions."),
                ft.Text("• Maximum Per Side: A team may use a maximum of 6 bench positions for Offense, Defense, or Special Teams.", color=ACCENT_AMBER, weight=ft.FontWeight.BOLD),
                ft.Text("• Manager Responsibility: Every team manager is strictly responsible for monitoring their roster's bench balance between sides of the ball."),
            ],
        },
        {
            "category": "Bench & IR",
            "title": "Bench Enforcement & Commissioner Drop Penalties",
            "keywords": "bench drop penalty violation projected points 48 hours 24 hours email warning repeat infraction",
            "controls": [
                ft.Text("1. Notification: The commissioner will email the offending manager upon noticing an infraction."),
                ft.Text("2. 48-Hour Grace Period: Once 48 hours pass from the infraction without a fix, the commissioner will drop the player that caused the roster violation."),
                ft.Text("3. 24-Hour Kickoff Emergency Drop: If any player on the offending team is within 24 hours of kickoff, the commissioner has the right and will drop the bench player who has the highest projected points for the current week on that side of the ball.", color=COLOR_RED, weight=ft.FontWeight.BOLD),
                ft.Text("4. Repeat Offenders: Rule 3 applies immediately to repeat offenders, even if no game is within 24 hours."),
                ft.Text("5. Effective Date: Enforced beginning Week 1 once final NFL rosters and official IR designations are set."),
            ],
        },
        {
            "category": "Bench & IR",
            "title": "Injured Reserve (IR) Slots",
            "keywords": "ir injured reserve covid postponed slots 2 waivers fa",
            "controls": [
                ft.Text("• 2 total IR spots available once Yahoo designates a player as IR."),
                ft.Text("• Eligible for Yahoo-designated IR players and NFL postponed games."),
                ft.Text("• Players may be added directly into IR from waivers or free agency."),
            ],
        },

        # --- 6. TRADES ---
        {
            "category": "Trades",
            "title": "Draft Pick Trading & Offseason Rules",
            "keywords": "trades draft picks max 2 offseason trade keeper deadline manual commissioner",
            "controls": [
                ft.Text("• Draft Pick Trades: A team may hold a maximum of two picks in any given round."),
                ft.Text("• Offseason Trades:"),
                ft.Text("   - Any player acquired in an offseason trade MUST be kept by the receiving team.", color=ACCENT_AMBER, weight=ft.FontWeight.BOLD),
                ft.Text("   - Must contact the commissioner directly since Yahoo offseason trades are disabled until after the draft."),
                ft.Text("   - Pre-Keeper Deadline: Final regular-season roster carries over; all players can be traded for picks or potential keepers."),
                ft.Text("   - Post-Keeper Deadline: Rosters cleared of all non-keepers. Only designated keepers and draft picks may be traded."),
            ],
        },
        {
            "category": "Trades",
            "title": "Commissioner Trade Review & Collusion Policy",
            "keywords": "trades collusion veto review fairness cheating protest commissioner standard",
            "controls": [
                ft.Text("• Standard for Veto: The commissioner evaluates trades solely for collusion or cheating, not subjective fairness. Owners are trusted to evaluate their own team needs."),
                ft.Text("• Collusion Review: If a trade appears lopsided or involves an eliminated manager gaining nothing while helping a contender, the commissioner reserves the right to request strategic rationale before ruling."),
                ft.Text("• Respectful Discourse: Respectful discussion is welcomed; personal attacks or disrespectful conduct can lead to franchise replacement."),
            ],
        },

        # --- 7. POSTSEASON ---
        {
            "category": "Postseason",
            "title": "Top-Scorer Playoff Exception",
            "keywords": "postseason playoff exception top scorer most points 6th seed consolation bracket bad luck",
            "controls": [
                ft.Text("• Automatic 6th Seed: If the team with the most points scored during the regular season misses the playoffs due to bad luck, they automatically receive the 6th seed in the Championship Bracket.", weight=ft.FontWeight.BOLD, color=ACCENT_AMBER),
                ft.Text("• Seed Adjustment: The team that originally placed 6th is moved to the #1 seed in the Consolation Tournament."),
            ],
        },
        {
            "category": "Postseason",
            "title": "Commissioner Expectations & League Integrity",
            "keywords": "postseason commissioner statement expectations active abandoned polls feedback reserve list",
            "controls": [
                ft.Text("• Active Management: All managers pay entry fees and are expected to keep lineups active all season to preserve competitive fairness."),
                ft.Text("• Feedback & Polls: Managers are expected to participate in annual league polls, votes, and rule discussions."),
                ft.Text("• Re-Invitation Rights: Quitting, abandoning rosters, or failing to participate in discussions can result in franchise forfeiture to the reserve waiting list for the following season."),
            ],
        },

        # --- 8. PAYOUTS & PRIZE DISTRIBUTION ---
        {
            "category": "Payouts",
            "title": "Official League Payout Ledger & Prize Distribution",
            "keywords": "payouts prize winnings pot money cash thursday stat corrections 1200 excel first second third 1st 2nd 3rd champion super bowl bonus",
            "controls": [
                ft.Text("VI. Winnings and Payout Schedule", size=18, weight=ft.FontWeight.BOLD, color=ACCENT_AMBER),
                ft.Text("• Buy-In & Pot: 12 Players × $100 = $1,200.00 Total Pot.", weight=ft.FontWeight.BOLD),
                ft.Text("• Disbursement Timing: All winnings are paid following the last week of the season (at the earliest the Thursday following the Championship game to finalize all official NFL stat corrections)."),
                ft.Text("• Regular Season Rules: Season Point Leader, Top Offense, Top Defense, Top Special Teams, & Weekly Highest Points are for Regular Season play only.", color=COLOR_GREEN),
                ft.Text("• Playoff Bonus Rules: Playoff Round Bonuses are rewarded by clinching that round.", color=COLOR_GREEN),
                ft.Divider(height=10),
                ft.Row([dt_official_payout], scroll=ft.ScrollMode.ADAPTIVE),
                *excel_live_display,
            ],
        },
    ]

    # 6. SEARCH & CHIP FILTERING
    filtered_list = ft.Column(spacing=10)
    current_category = ["All"]

    def refresh_help_articles(query=""):
        filtered_list.controls.clear()
        q = query.strip().lower()
        cat = current_category[0]

        matched = []
        for art in articles:
            if cat != "All" and art["category"] != cat:
                continue
            if q:
                match_text = (art["title"] + " " + art["keywords"] + " " + art["category"]).lower()
                if q not in match_text:
                    continue
            matched.append(art)

        if not matched:
            filtered_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        f"No rules or articles matched '{query}'. Try searching 'bad', 'ugly', 'draft', 'sack', 'payout', or 'keeper'.",
                        italic=True,
                        size=15,
                    ),
                    padding=15,
                )
            )
        else:
            for art in matched:
                tile = ft.ExpansionTile(
                    title=ft.Text(art["title"], size=16, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f"Category: {art['category']}", size=12, color=ACCENT_AMBER),
                    controls=[
                        ft.Container(
                            padding=15,
                            content=ft.Column(art["controls"], spacing=8),
                            bgcolor=BG_SURFACE_LIGHT,
                            border_radius=8,
                        )
                    ],
                )
                filtered_list.controls.append(tile)

        page.update()

    txt_search = ft.TextField(
        label="Search rules, scoring, divisions, draft order, keepers, payouts...",
        hint_text="e.g. 'bad', 'ugly', 'draft position', 'sack', 'payout', 'offense table', 'PPR'",
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
        on_change=lambda e: refresh_help_articles(txt_search.value),
    )

    def set_cat(cat_name):
        current_category[0] = cat_name
        refresh_help_articles(txt_search.value)

    category_chips = ft.Row(
        controls=[
            ft.Button("All", on_click=lambda e: set_cat("All")),
            ft.Button("⚙️ Setup", on_click=lambda e: set_cat("Setup")),
            ft.Button("🎯 Scoring", on_click=lambda e: set_cat("Scoring")),
            ft.Button("📜 Keepers", on_click=lambda e: set_cat("Keepers")),
            ft.Button("🏈 Draft", on_click=lambda e: set_cat("Draft")),
            ft.Button("💵 Finances", on_click=lambda e: set_cat("Finances")),
            ft.Button("🛡️ Bench & IR", on_click=lambda e: set_cat("Bench & IR")),
            ft.Button("🤝 Trades", on_click=lambda e: set_cat("Trades")),
            ft.Button("🏆 Postseason", on_click=lambda e: set_cat("Postseason")),
            ft.Button("💰 Payouts", on_click=lambda e: set_cat("Payouts")),
        ],
        scroll=ft.ScrollMode.ADAPTIVE,
        spacing=8,
    )

    help_controls_column = ft.Column(
        controls=[
            txt_search,
            category_chips,
        ],
        spacing=8,
        visible=True,
    )

    btn_toggle_help_controls = ft.TextButton(
        "▲ Hide Search / Fullscreen",
        icon=ft.Icons.KEYBOARD_ARROW_UP,
    )

    def toggle_help_controls(e):
        help_controls_column.visible = not help_controls_column.visible
        if help_controls_column.visible:
            btn_toggle_help_controls.text = "▲ Hide Search / Fullscreen"
            btn_toggle_help_controls.icon = ft.Icons.KEYBOARD_ARROW_UP
        else:
            btn_toggle_help_controls.text = "▼ Show Search & Categories"
            btn_toggle_help_controls.icon = ft.Icons.KEYBOARD_ARROW_DOWN
        page.update()

    btn_toggle_help_controls.on_click = toggle_help_controls

    refresh_help_articles()

    fixed_top_header = ft.Column(
        controls=[
            ft.Row(
                [
                    ft.Text("NPK Rules, Scoring & Help Center", size=20, weight=ft.FontWeight.BOLD),
                    btn_toggle_help_controls,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            help_controls_column,
            ft.Divider(height=10),
        ],
        spacing=4,
    )

    scrollable_viewer = ft.Column(
        controls=[filtered_list],
        scroll=ft.ScrollMode.ADAPTIVE,
        expand=True,
    )

    return ft.Column(
        controls=[fixed_top_header, scrollable_viewer],
        expand=True,
        spacing=5,
    )


# ---------------------------------------------------------
# MAIN APP ENTRY POINT (WITH MASTER HEADER COLLAPSE TOGGLE)
# ---------------------------------------------------------
def main(page: ft.Page):
    page.title = "NPK Fantasy Football League Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 8

    views = [
        build_weekly_tab(page),
        build_history_tab(page),
        build_keeper_tab(page),
        build_help_center_tab(page),
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
            ft.Button("Rules & Help Center", on_click=lambda e: switch_tab(3)),
        ],
        scroll=ft.ScrollMode.ADAPTIVE,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    header_content = ft.Column(
        controls=[
            nav_row,
            ft.Divider(height=8),
        ],
        spacing=4,
        visible=True,
    )

    btn_toggle_master_header = ft.IconButton(
        icon=ft.Icons.UNFOLD_LESS,
        tooltip="Toggle Main Nav Bar",
    )

    def toggle_master_header(e):
        header_content.visible = not header_content.visible
        btn_toggle_master_header.icon = ft.Icons.UNFOLD_MORE if not header_content.visible else ft.Icons.UNFOLD_LESS
        page.update()

    btn_toggle_master_header.on_click = toggle_master_header

    top_bar = ft.Row(
        controls=[
            ft.Text("🏈 NPK FF League", weight=ft.FontWeight.BOLD, size=15, color=ACCENT_AMBER),
            btn_toggle_master_header,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    page.add(
        ft.Column(
            controls=[
                top_bar,
                header_content,
                body,
            ],
            expand=True,
            spacing=3,
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