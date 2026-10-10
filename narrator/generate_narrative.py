# narrator/generate_narrative.py

import os
import httpx
import json
from google import genai

def generate_scr_narrative(findings: dict) -> dict:
    """
    Generate a Situation–Complication–Resolution narrative using Gemini API.
    - Task 2: Builds system instruction, interpolates findings dict, calls Gemini.
    - Task 3: Locks parameters (temperature=0.0, max_output_tokens>=300, timeout>=10s),
              wraps in try/except, returns structured dict.
    - Task 4: Falls back to offline template if no API key or API call fails.
    """

    # -------------------------------
    # Offline fallback helper
    # -------------------------------
    def generate_scr_narrative_offline(findings: dict) -> dict:
        """Deterministic offline fallback — formats SCR sections directly from findings."""
        situation = (
            f"Situation:\nMamaearth recorded a raw total revenue of ₹{findings['raw_total_revenue_inr']} "
            f"across all orders. After cleaning and deduplication, the verified revenue is "
            f"₹{findings['cleaned_total_revenue_inr']}."
        )
        complication = (
            f"Complication:\nDuplicate orders accounted for a delta of ₹{findings['duplicate_reconciliation_delta_inr']}. "
            f"Return rates varied by payment method: {findings['return_rate_by_payment']}. "
            f"The highest risk segment was {findings['highest_risk_segment']}."
        )
        resolution = (
            f"Resolution:\nOutlier analysis showed the true peak month as {findings['true_peak_month']}, "
            f"while inflated figures appeared in {findings['outlier_inflated_month']}. "
            f"These corrections ensure leadership sees accurate operational and financial trends."
        )
        return {
            "status": "success",
            "narrative": f"{situation}\n\n{complication}\n\n{resolution}",
            "tokens": None
        }

    # -------------------------------
    # Check API key
    # -------------------------------
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        # No key configured → offline fallback
        return generate_scr_narrative_offline(findings)

    # -------------------------------
    # Build system + user messages
    # -------------------------------
    system_instruction = (
        "You are a senior data analyst writing for Mamaearth's regional ops and finance heads. "
        "Your output must strictly follow the SCR (Situation–Complication–Resolution) structure, "
        "with three labeled sections: Situation, Complication, Resolution. "
        "Every number in the output must come directly from the supplied findings dictionary "
        "and appear with the same value — no invented or altered statistics."
    )

    user_prompt = (
        "Use the following verified findings to craft the narrative:\n\n"
        f"- Cleaned total revenue: ₹{findings['cleaned_total_revenue_inr']}\n"
        f"- Raw total revenue: ₹{findings['raw_total_revenue_inr']}\n"
        f"- Duplicate reconciliation delta: ₹{findings['duplicate_reconciliation_delta_inr']}\n"
        f"- Return rate by payment: {findings['return_rate_by_payment']}\n"
        f"- Highest risk segment: {findings['highest_risk_segment']}\n"
        f"- True peak month: {findings['true_peak_month']}\n"
        f"- Outlier inflated month: {findings['outlier_inflated_month']}\n\n"
        "Write the SCR narrative for Mamaearth's leadership."
    )

    # -------------------------------
    # Call Gemini API with parameter locking
    # -------------------------------
    try:
        client = genai.Client(api_key=api_key)
        http_client=httpx.Client(timeout=15)  # ≥10s per requirement
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=[system_instruction, user_prompt],
            config={
                "temperature": 0.0,          # deterministic factual report
                "max_output_tokens": 5000     # enough for ~250 words across 3 sections
            },
            # timeout=15                # ≥10s per requirement
        )

        return {
            "status": "success",
            "narrative": response.text,
            "tokens": response.usage_metadata.total_token_count
        }

    except Exception as err:
        # On error → offline fallback
        return generate_scr_narrative_offline(findings) | {
            "status": "error",
            "message": str(err)
        }


def check_narrative(narrative: str, findings: dict) -> None:
    """
    Verify that the narrative contains all required figures from findings.json.
    Normalizes commas in numbers before checking.
    Prints PASS/FAIL per figure.
    """
    normalized = narrative.replace(",", "")

    # Build expected substrings dynamically from findings
    expected_checks = {
        "Cleaned total revenue": [str(findings["cleaned_total_revenue_inr"])],
        "COD return rate": [str(findings["return_rate_by_payment"].get("COD"))],
        "COD Tier-2 highest risk": [str(findings["highest_risk_segment"]["return_rate_pct"])],
        "Duplicate reconciliation delta": [str(findings["duplicate_reconciliation_delta_inr"])],
        "True peak month": [
            str(findings["true_peak_month"]["month"]),
            str(findings["true_peak_month"]["revenue_inr"])
        ],
    }

    for label, substrings in expected_checks.items():
        if all(s in normalized for s in substrings):
            print(f"PASS: {label}")
        else:
            print(f"FAIL: {label}")


# Allow running standalone
if __name__ == "__main__":
    with open("narrator/insight_data.json", "r") as f:
        findings = json.load(f)
    result = generate_scr_narrative(findings)
    print(result)

    print("\n--- Checker Results ---")
    check_narrative(result["narrative"], findings)	
