from openai_client import openai_client

response = openai_client.responses.create(
    model="gpt-5",
    tools=[{"type": "web_search_preview"}],
    input="What is the production capacity of electric vehicles for Audi at its Ingolstadt plant in Germany?",
)

print(response.output_text)