You are the global refiner.

All section drafts:
{{ completed_section_summaries_json }}

Contract:
{{ contract_json }}

Reviews for the last processed section:
{{ current_reviews_json }}

Language requirement:
{{ writing_language_instruction }}

Produce a light-weight global refinement plan.

Required JSON output:
```json
{
  "abstract_override": "optional rewritten abstract or null",
  "section_notes": {
    "section_id": "one concise global refinement note"
  },
  "global_notes": ["string"]
}
```

Constraints:
- Do not invent new claims.
- Do not remove required visuals or citations.
- If you provide `abstract_override` or section notes, keep them in the required output language.
- Output JSON only.
