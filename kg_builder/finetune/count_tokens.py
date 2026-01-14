import json
import glob
from pathlib import Path
import tiktoken

# Correct tokenizer for GPT-4o / GPT-4.1 family
enc = tiktoken.get_encoding("cl100k_base")

# Conservative overhead estimate per message
TOKENS_PER_MESSAGE_OVERHEAD = 4
TOKENS_PER_EXAMPLE_OVERHEAD = 2

def count_tokens_for_example(messages):
    tokens = 0

    for msg in messages:
        tokens += TOKENS_PER_MESSAGE_OVERHEAD
        tokens += len(enc.encode(msg["role"]))
        tokens += len(enc.encode(msg["content"]))

    tokens += TOKENS_PER_EXAMPLE_OVERHEAD
    return tokens

def count_tokens_in_jsonl(pattern):
    total_tokens = 0
    total_examples = 0

    for path in glob.glob(pattern):
        with Path(path).open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if not line.strip():
                    continue

                obj = json.loads(line)
                messages = obj["messages"]

                total_tokens += count_tokens_for_example(messages)
                total_examples += 1

    return total_tokens, total_examples

if __name__ == "__main__":
    tokens, examples = count_tokens_in_jsonl("training_data/nodes.jsonl")

    print(f"Examples: {examples:,}")
    print(f"Total tokens: {tokens:,}")
    print(f"Million tokens: {tokens / 1_000_000:.2f}")