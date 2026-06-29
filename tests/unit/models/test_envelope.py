from wellness_tracker.models.envelope import DailyEnvelope, WhoopDayContext


class TestDailyEnvelope:
    def test_defaults_applied(self) -> None:
        env = DailyEnvelope(
            date="2026-06-28", week_starting="2026-06-23", objectives_version="v1"
        )
        assert env.status == "in_progress"
        assert env.envelope_id.startswith("env_")
        assert env.date == "2026-06-28"
        assert env.week_starting == "2026-06-23"
        assert env.objectives_version == "v1"

    def test_envelope_id_includes_date(self) -> None:
        env = DailyEnvelope(
            date="2026-06-28", week_starting="2026-06-23", objectives_version="v1"
        )
        assert "2026-06-28" in env.envelope_id

    def test_explicit_envelope_id_preserved(self) -> None:
        env = DailyEnvelope(
            envelope_id="env_custom_id",
            date="2026-06-28",
            week_starting="2026-06-23",
            objectives_version="v1",
        )
        assert env.envelope_id == "env_custom_id"

    def test_accepts_whoop_day_context(self) -> None:
        env = DailyEnvelope(
            date="2026-06-28", week_starting="2026-06-23", objectives_version="v1"
        )
        assert env.whoop is None
        env.whoop = WhoopDayContext(strain_target=14.2)
        assert env.whoop.strain_target == 14.2
