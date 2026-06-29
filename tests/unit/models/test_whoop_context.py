import pytest
from pydantic import ValidationError

from wellness_tracker.models.envelope import WhoopDayContext


class TestWhoopDayContext:
    def test_strain_target_above_max_rejected(self) -> None:
        with pytest.raises(ValidationError, match="strain_target"):
            WhoopDayContext(strain_target=21.1)

    def test_valid_strain_target_accepted(self) -> None:
        context = WhoopDayContext(strain_target=14.2)
        assert context.strain_target == 14.2
        assert context.strain_accumulated == 0.0
