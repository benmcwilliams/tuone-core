from openai_client import openai_client

response = openai_client.responses.create(
    model="gpt-5",
    tools=[{"type": "web_search_preview"}],
    input="What is the planned manufacturing capacity of the Elinor Batteries battery manufacturing facility in Norway?",
)

print(response.output_text)