
import json
import logging
import random
from pathlib import Path
from typing import List, Tuple, Dict, Any

logger = logging.getLogger("data_utils")

SYSTEM_PROMPT = 

BOS = "<bos>"
EOS = "<eos>"
START_OF_TURN = "<start_of_turn>"
END_OF_TURN   = "<end_of_turn>"

def format_conversation(messages: List[Dict[str, str]], add_system: bool = True) -> str:
    
    formatted = BOS

    first_user_done = False

    for msg in messages:
        role    = msg.get("role", "").lower()
        content = msg.get("content", "").strip()

        if not content:
            continue

        if role in ("user", "human"):
            gemma_role = "user"
            if not first_user_done and add_system:
                content         = f"{SYSTEM_PROMPT}\n\n{content}"
                first_user_done = True
        elif role in ("assistant", "model", "bot"):
            gemma_role = "model"
        else:

            continue

        formatted += f"{START_OF_TURN}{gemma_role}\n{content}{END_OF_TURN}\n"

    formatted += EOS
    return formatted

def parse_jsonl_record(record: Dict[str, Any]) -> List[Dict[str, str]] | None:
    
    if "messages" in record and isinstance(record["messages"], list):
        msgs = record["messages"]

        return [m for m in msgs if m.get("role") in ("user", "assistant", "human", "model")]

    if "prompt" in record and "response" in record:
        return [
            {"role": "user",      "content": record["prompt"]},
            {"role": "assistant", "content": record["response"]},
        ]

    if "conversation" in record and isinstance(record["conversation"], list):
        return record["conversation"]

    if "input" in record and "output" in record:
        return [
            {"role": "user",      "content": record["input"]},
            {"role": "assistant", "content": record["output"]},
        ]

    logger.warning(f"Unrecognized JSONL schema: {list(record.keys())}")
    return None

def load_dataset(path: str, max_examples: int | None = None) -> List[str]:
    
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at: {dataset_path.resolve()}")

    formatted_examples = []
    skipped = 0

    logger.info(f"Loading dataset from {dataset_path}...")

    with open(dataset_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
                messages = parse_jsonl_record(record)

                if not messages or len(messages) < 2:
                    skipped += 1
                    continue

                has_user = any(m.get("role") in ("user", "human") for m in messages)
                has_asst = any(m.get("role") in ("assistant", "model") for m in messages)

                if not (has_user and has_asst):
                    skipped += 1
                    continue

                formatted = format_conversation(messages)
                formatted_examples.append(formatted)

                if max_examples and len(formatted_examples) >= max_examples:
                    break

            except json.JSONDecodeError:
                logger.warning(f"  Line {line_num}: Invalid JSON — skipping")
                skipped += 1

    logger.info(f"✅ Loaded {len(formatted_examples)} examples ({skipped} skipped)")
    return formatted_examples

def split_dataset(
    examples: List[str],
    train_ratio: float = 0.9,
    seed: int = 42,
) -> Tuple[List[str], List[str]]:
    
    random.seed(seed)
    shuffled = examples.copy()
    random.shuffle(shuffled)

    split_idx     = int(len(shuffled) * train_ratio)
    train_examples = shuffled[:split_idx]
    eval_examples  = shuffled[split_idx:]

    logger.info(f"Dataset split — train: {len(train_examples)}, eval: {len(eval_examples)}")
    return train_examples, eval_examples

def get_token_stats(examples: List[str], tokenizer) -> Dict[str, float]:
    
    lengths = [len(tokenizer.encode(ex)) for ex in examples[:500]]
    if not lengths:
        return {}
    return {
        "min":    min(lengths),
        "max":    max(lengths),
        "mean":   sum(lengths) / len(lengths),
        "p95":    sorted(lengths)[int(0.95 * len(lengths))],
    }
