from openai_client import openai_client

response = openai_client.responses.create(
    model="gpt-5",
    tools=[{"type": "web_search_preview"}],
    input="What is the manufacturing capacity of the Verkor gigafactory in Dunkirk, France for battery modules (not just cells) particularly?",
)

print(response.output_text)