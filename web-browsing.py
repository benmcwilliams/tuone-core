from openai_client import openai_client

response = openai_client.responses.create(
    model="gpt-5",
    tools=[{"type": "web_search_preview"}],
    input="What is the production capacity of electric vehicles for Stellantis at its Mullhouse plant in France?",
)

print(response.output_text)