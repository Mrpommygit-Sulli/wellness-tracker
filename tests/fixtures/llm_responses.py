WHOOP_BRIEF_SUCCESS_RESPONSE = """
{
  "strain_target": 14.2,
  "confidence": 0.96,
  "notes": null
}
"""

WHOOP_BRIEF_NO_TARGET_RESPONSE = """
{
  "strain_target": null,
  "confidence": 0.0,
  "notes": "No strain target found in input"
}
"""

WHOOP_BRIEF_MALFORMED_RESPONSE = """
Here is the extracted data: strain target is 14.2
"""
