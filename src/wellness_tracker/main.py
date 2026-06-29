import argparse
import sys
from typing import Literal, cast

from wellness_tracker.models.objectives import (
    NutritionTargets,
    TrainingTarget,
    WeeklyObjectives,
    WeightGoal,
)
from wellness_tracker.orchestrator import Orchestrator
from wellness_tracker.storage.objectives import save_objectives


def _prompt_set_objectives() -> None:
    print("Set Weekly Objectives")
    print("---------------------")

    week_starting = input("Week starting (YYYY-MM-DD): ").strip()
    current_weight = float(input("Current weight (kg): ").strip())
    direction = cast(
        Literal["lose", "maintain", "gain"],
        input("Weight goal (lose/maintain/gain): ").strip(),
    )

    deficit: int | None = None
    if direction == "lose":
        deficit = int(input("Weekly calorie deficit target (kcal): ").strip())

    daily_calories = int(input("Daily calorie target: ").strip())
    daily_protein = int(input("Daily protein target (g): ").strip())

    training_targets: dict[str, TrainingTarget] = {}
    print("\nTraining targets (enter blank activity name to finish):")
    while True:
        activity = input("  Activity name: ").strip()
        if not activity:
            break
        sessions = int(input("  Sessions per week: ").strip())
        duration = int(input("  Min duration (minutes): ").strip())
        training_targets[activity] = TrainingTarget(
            sessions=sessions, min_duration_minutes=duration
        )

    constraints: list[str] = []
    print("\nConstraints (enter blank to finish):")
    while True:
        constraint = input("  Constraint: ").strip()
        if not constraint:
            break
        constraints.append(constraint)

    objectives = WeeklyObjectives(
        week_starting=week_starting,
        weight_goal=WeightGoal(
            direction=direction,
            target_weekly_deficit_kcal=deficit,
            current_weight_kg=current_weight,
        ),
        training_targets=training_targets,
        nutrition_targets=NutritionTargets(
            daily_calorie_target=daily_calories,
            daily_protein_target_g=daily_protein,
        ),
        constraints=constraints,
    )

    path, version = save_objectives(objectives)
    print(f"\nObjectives saved to {path} ({version})")


def _run_whoop(raw_text: str) -> None:
    try:
        result = Orchestrator().process("whoop_brief", raw_text)
    except FileNotFoundError:
        print("✗ No weekly objectives found")
        print("  Run --set-objectives before logging daily data")
        sys.exit(1)

    if result["status"] == "success":
        print("✓ Whoop brief logged")
        print(f"  Strain target: {result['output'].strain_target}")
        print(f"  Envelope saved: {result['path']}")
    else:
        print("⚠ Could not extract strain target from input")
        print("  Try again with clearer text e.g.")
        print('  "Whoop strain target 14.2 today"')


def main() -> None:
    parser = argparse.ArgumentParser(description="Wellness Tracker")
    parser.add_argument(
        "--set-objectives", action="store_true", help="Set weekly objectives"
    )
    parser.add_argument("--whoop", type=str, help="Log morning Whoop brief")
    args = parser.parse_args()

    if args.set_objectives:
        _prompt_set_objectives()
    elif args.whoop:
        _run_whoop(args.whoop)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
