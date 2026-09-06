# NPK Keeper Logic Engine

OFFENSE_YEAR2_TABLE = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3,
    9: 4, 10: 4, 11: 5, 12: 5, 13: 6, 14: 6, 15: 6, 16: 6,
    17: 7, 18: 7, 19: 8, 20: 8, 21: 9, 22: 9, 23: 10, 24: 10
}

DEFENSE_YEAR2_TABLE = {
    1: 1, 2: 1, 3: 1, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5,
    9: 6, 10: 7, 11: 7, 12: 8, 13: 9, 14: 9, 15: 9, 16: 10,
    17: 11, 18: 12, 19: 12, 20: 13, 21: 14, 22: 15, 23: 15, 24: 16
}

def calculate_keeper_cost(side: str, keeper_year: int, prior_round: int, is_undrafted: bool = False, undrafted_count: int = 1) -> int:
    """
    Calculates draft pick cost based on the official NPK rulebook.
    keeper_year:
      1 = 1st time kept (2nd year on roster)
      2 = 2nd time kept (3rd year on roster)
      3 = 3rd+ time kept (4th+ year on roster)
    """
    if keeper_year == 1:
        if is_undrafted:
            if side == "Offense":
                return 13 if undrafted_count == 1 else 12
            else:
                return 20 if undrafted_count == 1 else 19
        return max(1, prior_round)

    elif keeper_year == 2:
        table = OFFENSE_YEAR2_TABLE if side == "Offense" else DEFENSE_YEAR2_TABLE
        prior_round = max(1, min(24, prior_round))
        return table.get(prior_round, 1)

    else:
        # 3rd or more time as keeper: subtract 2 from prior round, min round 1
        return max(1, prior_round - 2)

def validate_keeper_selections(keepers: list) -> list[str]:
    """Validates roster compliance against NPK rules."""
    warnings = []
    if len(keepers) > 4:
        warnings.append("❌ Maximum 4 keepers allowed per team.")
        return warnings

    offense_count = sum(1 for k in keepers if k["side"] == "Offense")
    defense_count = sum(1 for k in keepers if k["side"] in ["Defense", "Special Teams"])

    # Split constraints
    if len(keepers) == 2:
        if offense_count > 1 or defense_count > 1:
            warnings.append("❌ If keeping 2 players, max 1 can be from Offense and max 1 from Defense/ST.")
    elif len(keepers) in [3, 4]:
        if offense_count > 2:
            warnings.append("❌ Maximum 2 Offense keepers allowed.")
        if defense_count > 2:
            warnings.append("❌ Maximum 2 Defense/Special Teams keepers allowed.")

    # Round 1-4 rule
    early_round_keepers = [k for k in keepers if k["cost_round"] <= 4]
    if len(early_round_keepers) > 1:
        names = ", ".join([k["name"] for k in early_round_keepers])
        warnings.append(f"❌ Only 1 player allowed in Rounds 1–4! Conflict between: {names}")

    return warnings