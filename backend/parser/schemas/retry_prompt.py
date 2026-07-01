def get_retry_prompt(failed_signals: dict, base_system_prompt: str) -> str:
    """
    Constructs a targeted retry prompt highlighting which validations failed,
    appended to the base system prompt instructions.
    """
    signal_descriptions = {
        "has_name": "No candidate name was found in the 'personal' info.",
        "has_email": "No email address was found in the 'personal' info.",
        "has_experience": "No work experience entries were extracted.",
        "dates_valid": "Work experience dates are invalid (start_date must be provided, and end_date must be >= start_date).",
        "name_in_source": "The candidate name extracted does not match or appear in the source resume text.",
        "has_skills": "No technical skills were extracted under the 'skills' field.",
        "links_preserved": "Some embedded links from the PDF annotation layer were lost or omitted from the parsed 'links' object.",
    }

    failed_details = []
    for signal, val in failed_signals.items():
        if not val:  # False means failed
            desc = signal_descriptions.get(
                signal, f"Validation signal '{signal}' failed."
            )
            failed_details.append(f"- {signal}: {desc}")

    failures_str = "\n".join(failed_details)

    retry_instruction = f"""

============================================================
CRITICAL WARNING: PREVIOUS EXTRACTION ATTEMPT FAILED VALIDATION
The following validation check(s) failed in your previous output:
{failures_str}

Please carefully re-evaluate the source resume text and link arrays.
Ensure that:
1. You fix all of the validation failures listed above.
2. You output ONLY valid JSON matching the schema exactly (no markdown fences, no wrapping, no explanations).
3. Do not omit any other previously extracted correct details.
============================================================
"""
    return base_system_prompt + retry_instruction
