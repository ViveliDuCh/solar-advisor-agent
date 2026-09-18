from __future__ import annotations

from collections.abc import Sequence


def _format_clock(value: object) -> str:
    return value.strftime("%I:%M %p").lstrip("0")


def explain_recommendations(
    recommendations: Sequence[dict[str, object]],
    maintenance: dict[str, object],
) -> str:
    if recommendations:
        first = recommendations[0]
        schedule_text = (
            f"Start with **{first['appliance']} at "
            f"{_format_clock(first['start'])}**. The model selected that window because expected "
            "solar surplus is high relative to the household's baseline load."
        )
    else:
        schedule_text = "No flexible appliance window was available with the current constraints."

    uncertainty = (
        "The shaded forecast range reflects weather and system-assumption uncertainty. "
        "Recommendations are advisory and require homeowner approval."
    )
    return f"{schedule_text}\n\n{maintenance['message']}\n\n{uncertainty}"
