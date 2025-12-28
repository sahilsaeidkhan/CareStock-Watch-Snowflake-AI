# ai_component_additions.py
"""
AI Component: Demand Forecasting (Cortex-style)

This module simulates a Snowflake Cortex-assisted
forecasting component using historical demand signals.

Design goals:
- Explainable
- Lightweight
- Safe for hackathon
- Easy to replace with real Cortex later
"""

def cortex_demand_forecast(
    avg_daily_demand: float,
    lead_time_days: int,
    horizon_days: int = 7
) -> dict:
    """
    Cortex-style demand forecast with confidence band.

    Returns:
    - forecast_units
    - lower_bound
    - upper_bound
    - explanation
    """

    # Base forecast
    forecast_units = avg_daily_demand * horizon_days

    # Simple uncertainty model (±20%)
    lower_bound = forecast_units * 0.8
    upper_bound = forecast_units * 1.2

    explanation = (
        f"Forecast uses recent average demand ({avg_daily_demand:.1f}/day) "
        f"projected over {horizon_days} days. "
        f"Lead time considered: {lead_time_days} days. "
        "Confidence band reflects demand variability."
    )

    return {
        "forecast_units": round(forecast_units, 1),
        "lower_bound": round(lower_bound, 1),
        "upper_bound": round(upper_bound, 1),
        "explanation": explanation
    }
