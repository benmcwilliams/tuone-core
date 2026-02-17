from openai_client import openai_client

SYSTEM_PROMPT_JSON = """
You are an evidence extraction engine.

Your task is to extract ONLY factual claims from relevant articles and tie every claim explicitly to a single verifiable source.

STRICT RULES
1) Output MUST be ONLY valid JSON. No markdown, no commentary, no extra keys.
2) Every claim must be supported by near-verbatim text copied from the source article.
3) Do NOT invent, infer, or generalise. Use only what is stated in sources.
4) Each claim must be tied to EXACTLY ONE source (no multi-source claims).
5) Every source MUST include:
   - published_date in ISO format: "YYYY-MM-DD"
   - url as a full URL
6) If a source does not have a clear publication date, DO NOT use it.
7) Claims must be atomic (one fact per claim). Split multi-fact sentences into separate claims.
8) Do not duplicate claims.
9) If no valid dated sources are available, output exactly this JSON:
   {"claims":[]}

OUTPUT JSON SCHEMA (MANDATORY)
{
  "claims": [
    {
      "claim": "string",
      "evidence_verbatim": "string",
      "source": {
        "published_date": "YYYY-MM-DD",
        "url": "string",
        "title": "string (optional, if known)"
      },
    }
  ]
}

ADDITIONAL CONSTRAINTS
- evidence_verbatim should be as close as possible to the original wording and kept short (typically 1–3 sentences).
- claim must be a plain factual statement that is directly supported by evidence_verbatim.
- If publisher/title are not confidently available, omit them (do not guess).
"""

# USER_PROMPT = """ Summarise any solar cell manufacturing facilities currently operating or under construction in Europe: 
#                 - include investment amounts and manufacturing capacities were possible.
#                 - include the source URL and date of publication explicitly with every evidence claim
#                 """

USER_PROMPT = """Describe latest investment relevant news about the Giga PV solar manufacturing plant
 in Racibórz, Poland.  
                 - include investment amounts and manufacturing capacities were possible.
                - include the source URL and date of publication explicitly with every evidence claim"""

response = openai_client.responses.create(
    model="gpt-5",
    tools=[{"type": "web_search_preview",
            "search_context_size": "high"}],
    input=[
        #{"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT}
    ])

print(response.output_text)