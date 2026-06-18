from pathlib import Path

import pytest

from smartspend.database import reset_demo_data
from smartspend.savings import (
    SIMULATED_SAVINGS_NOTICE,
    list_savings_goals,
    simulate_save_difference_to_goal,
)
from smartspend.transactions import get_spent_so_far


def test_seeded_savings_goals_include_required_goals(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    goal_names = {goal.name for goal in list_savings_goals(db_path)}

    assert {"Emergency fund", "Holiday", "New laptop"}.issubset(goal_names)


def test_positive_savings_can_be_simulated_into_selected_goal(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    starting_spent = get_spent_so_far(db_path)
    goal = next(goal for goal in list_savings_goals(db_path) if goal.id == "holiday")

    movement = simulate_save_difference_to_goal(
        goal_id="holiday",
        savings_amount_huf=2500,
        db_path=db_path,
    )

    assert movement.goal_name == "Holiday"
    assert movement.amount_huf == 2500
    assert movement.new_goal_balance_huf == goal.current_amount_huf + 2500
    assert movement.label == "Simulated saving the SmartSpend difference"
    assert movement.simulated_notice == SIMULATED_SAVINGS_NOTICE
    assert "not a real money transfer" in movement.simulated_notice
    assert get_spent_so_far(db_path) == starting_spent


def test_non_positive_savings_are_rejected(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    with pytest.raises(ValueError, match="positive"):
        simulate_save_difference_to_goal("holiday", 0, db_path)


def test_unknown_savings_goal_is_rejected(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    with pytest.raises(ValueError, match="No savings goal"):
        simulate_save_difference_to_goal("missing", 1000, db_path)
