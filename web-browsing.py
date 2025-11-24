from openai_client import openai_client

response = openai_client.responses.create(
    model="gpt-5",
    tools=[{"type": "web_search_preview"}],
    input="What is the current status of the CALB battery manufacturing facility in Sines, Portugal. Have they reached FID? / began construction?",
)

print(response.output_text)