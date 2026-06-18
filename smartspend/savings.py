"""Simulated savings goal operations for SmartSpend V2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from smartspend.database import DEFAULT_DB_PATH, connect, ensure_demo_database

SIMULATED_SAVINGS_NOTICE = (
    "Simulated SmartSpend savings movement. This is not a real money transfer."
)


@dataclass(frozen=True)
class SavingsGoal:
    """One simulated SmartSpend savings goal."""

    id: str
    name: str
    target_amount_huf: int
    current_amount_huf: int
    monthly_contribution_huf: int
    priority: int


@dataclass(frozen=True)
class SimulatedSavingsMovement:
    """A simulated movement into a savings goal."""

    id: int
    goal_id: str
    goal_name: str
    amount_huf: int
    new_goal_balance_huf: int
    label: str
    simulated_notice: str


def list_savings_goals(
    db_path: Path | str = DEFAULT_DB_PATH,
) -> list[SavingsGoal]:
    """Return simulated savings goals."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, name, target_amount_huf, current_amount_huf,
                   monthly_contribution_huf, priority
            FROM savings_goals
            ORDER BY priority
            """
        ).fetchall()

    return [
        SavingsGoal(
            id=row["id"],
            name=row["name"],
            target_amount_huf=row["target_amount_huf"],
            current_amount_huf=row["current_amount_huf"],
            monthly_contribution_huf=row["monthly_contribution_huf"],
            priority=row["priority"],
        )
        for row in rows
    ]


def simulate_save_difference_to_goal(
    goal_id: str,
    savings_amount_huf: int,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> SimulatedSavingsMovement:
    """Simulate saving positive SmartSpend savings into a selected goal."""

    if savings_amount_huf <= 0:
        raise ValueError("Savings amount must be positive to simulate a movement.")

    ensure_demo_database(db_path)
    created_at = datetime.now(UTC).isoformat(timespec="seconds")

    with connect(db_path) as connection:
        goal = connection.execute(
            """
            SELECT id, name, current_amount_huf
            FROM savings_goals
            WHERE id = ?
            """,
            (goal_id,),
        ).fetchone()
        if goal is None:
            raise ValueError(f"No savings goal found with id '{goal_id}'.")

        new_balance = goal["current_amount_huf"] + savings_amount_huf
        connection.execute(
            """
            UPDATE savings_goals
            SET current_amount_huf = ?
            WHERE id = ?
            """,
            (new_balance, goal_id),
        )
        cursor = connection.execute(
            """
            INSERT INTO savings_movements (
                goal_id, amount_huf, created_at, label, simulated_notice
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                goal_id,
                savings_amount_huf,
                created_at,
                "Simulated saving the SmartSpend difference",
                SIMULATED_SAVINGS_NOTICE,
            ),
        )
        movement_id = cursor.lastrowid

    return SimulatedSavingsMovement(
        id=movement_id,
        goal_id=goal_id,
        goal_name=goal["name"],
        amount_huf=savings_amount_huf,
        new_goal_balance_huf=new_balance,
        label="Simulated saving the SmartSpend difference",
        simulated_notice=SIMULATED_SAVINGS_NOTICE,
    )
