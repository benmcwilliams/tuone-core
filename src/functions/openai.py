import re

def query_model(client, model, system_prompt, user_prompt):

    completion = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f''' {user_prompt}'''},
    ],
    temperature=0)

    text = completion.choices[0].message.content
    return text

def describe_investment(client, company, location, country, factsheet, prompt):

    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": f''' 
        Please describe the investment of {company} in their facility in {location}, {country}.
        Here the text: {factsheet}
        '''},
    ],
    temperature=0)

    text_status = completion.choices[0].message.content
    return text_status

def return_specific_value(client, text, prompt, model="gpt-4o-mini"):
    """
    Calls the specified model (default is gpt-4o-mini) and returns the completion result.

    Args:
    client (object): OpenAI API client instance.
    text (str): The input text to be processed by the model.
    prompt (str): The system prompt that defines the task.
    model (str): The model to use, defaults to gpt-4o-mini if not specified.

    Returns:
    str: The completion result from the model.
    """
    completion = client.chat.completions.create(
        model=model,  # Use the model passed or the default
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f''' 
            {text}'''},
        ],
        temperature=0
    )

    status = completion.choices[0].message.content

    return status

def clean_model_output(output):
    """Clean the model output by removing markdown code blocks and extra whitespace."""
    # Remove ```json and ``` markers
    output = re.sub(r'```json\s*|\s*```', '', output)
    # Remove any leading/trailing whitespace
    output = output.strip()
    return output