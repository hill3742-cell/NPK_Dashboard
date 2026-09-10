import math

def calculate_keeper_cost(
    side: str,
    current_years_on_team: int,
    current_round: int,
    is_undrafted: bool = False,
    undrafted_count: int = 1,
) -> int:
    """
    Calculates NEXT year's draft pick cost based on the player's CURRENT year status:
    
    1. CURRENT YEAR 1 (Entering Year 2 / 1st Time Kept):
       - Costs the same round they were drafted this year.
       - If undrafted FA: Offense = Rd 13 (1st) / Rd 12 (2nd); Defense = Rd 20 (1st) / Rd 19 (2nd).
       
    2. CURRENT YEAR 2 (Entering Year 3 / 2nd Time Kept):
       - Offense (Rds 1-14):  Round - ((Round / 2) + 1)
       - Offense (Rds 15-24): Round - ((Round / 2) + 2)
       - Defense (Rds 1-13):  Round - ((Round / 4) + 1)
       - Defense (Rds 14-24): Round - ((Round / 4) + 2)
       * Decimals round to the later round (higher number).
       
    3. CURRENT YEAR 3+ (Entering Year 4+ / 3rd+ Time Kept):
       - Simply: Current Round - 2 (with a floor of Round 1).
    """
    current_round = max(1, min(24, int(current_round)))
    is_offense = side.lower() == "offense"

    # Moving to Year 2 (1st time kept)
    if current_years_on_team <= 1:
        if is_undrafted:
            if is_offense:
                return 13 if undrafted_count == 1 else 12
            else:
                return 20 if undrafted_count == 1 else 19
        return current_round

    # Moving to Year 3 (2nd time kept) -> Apply the Year 2-to-3 formula
    elif current_years_on_team == 2:
        if is_offense:
            if current_round <= 14:
                raw = current_round - ((current_round / 2) + 1)
            else:
                raw = current_round - ((current_round / 2) + 2)
        else:
            if current_round <= 13:
                raw = current_round - ((current_round / 4) + 1)
            else:
                raw = current_round - ((current_round / 4) + 2)
        return max(1, math.ceil(raw))

    # Moving to Year 4+ (3rd+ time kept) -> Current Round - 2
    else:
        return max(1, current_round - 2)


def calculate_traded_keeper_cost(draft_round: int) -> int:
    """If a player is traded and kept, they reset to Year 2 (costing their 2026 draft round)."""
    return max(1, min(24, int(draft_round)))


def validate_keeper_selections(selected_players: list) -> list:
    violations = []
    if len(selected_players) > 4:
        violations.append(f"Maximum 4 keepers allowed. You selected {len(selected_players)}.")

    offense_count = sum(1 for p in selected_players if p.get("side", "").lower() == "offense")
    defense_count = sum(1 for p in selected_players if p.get("side", "").lower() in ["defense", "special teams"])

    total = len(selected_players)
    if total == 2 and (offense_count > 1 or defense_count > 1):
        violations.append("When keeping 2 players, you can keep at most 1 from Offense and 1 from Defense/ST.")
    elif total >= 3 and (offense_count > 2 or defense_count > 2):
        violations.append(f"Maximum 2 per side of the ball. Selected: {offense_count} Offense, {defense_count} Defense/ST.")

    rounds_1_to_4 = [p for p in selected_players if p.get("cost_round", 24) <= 4]
    if len(rounds_1_to_4) > 1:
        names = ", ".join(f"{p['name']} (Rd {p['cost_round']})" for p in rounds_1_to_4)
        violations.append(f"Only ONE keeper from Rounds 1–4 is allowed. You have {len(rounds_1_to_4)}: {names}.")

    return violations