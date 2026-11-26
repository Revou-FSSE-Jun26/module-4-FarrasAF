"""Property 19: Analytics counts and completion rate are consistent and bounded.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6**
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from flask_app.analytics.service import DONE_COLUMN_NAME, compute_completion_rate

column_names = st.one_of(
    st.sampled_from([DONE_COLUMN_NAME, "To Do", "Doing", "done", "Done ", " Done", "DONE"]),
    st.text(max_size=20),
)
column_counts = st.lists(
    st.tuples(column_names, st.integers(min_value=0, max_value=1000)),
    max_size=15,
)


# Feature: task-management-app, Property 19: Analytics counts and completion rate are consistent and bounded  # noqa: E501
@settings(max_examples=200)
@given(columns=column_counts)
def test_completion_rate_matches_done_share_and_is_bounded(
    columns: list[tuple[str, int]],
) -> None:
    total = sum(count for _, count in columns)
    done = sum(count for name, count in columns if name == DONE_COLUMN_NAME)

    rate = compute_completion_rate(columns)

    assert 0.0 <= rate <= 1.0
    if total == 0 or done == 0:
        assert rate == 0.0
    else:
        assert rate == done / total


# Feature: task-management-app, Property 19: Analytics counts and completion rate are consistent and bounded  # noqa: E501
@settings(max_examples=100)
@given(columns=column_counts)
def test_completion_rate_without_done_column_is_zero(
    columns: list[tuple[str, int]],
) -> None:
    others = [(name, count) for name, count in columns if name != DONE_COLUMN_NAME]

    assert compute_completion_rate(others) == 0.0
