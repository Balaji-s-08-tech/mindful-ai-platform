
import os
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ModelConfig:

    base_model_id: str = "google/gemma-3-4b-it"

    adapter_path: Optional[str] = "./lora-adapter"

    load_in_4bit: bool = True
    bnb_4bit_compute_dtype: str = "bfloat16"
    bnb_4bit_use_double_quant: bool = True
    bnb_4bit_quant_type: str = "nf4"

@dataclass
class LoRAConfig:
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    bias: str = "none"
    task_type: str = "CAUSAL_LM"

    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ])

@dataclass
class TrainingConfig:

    dataset_path: str = "../dataset/cbt_humanistic_dataset.jsonl"
    train_split: float = 0.9
    max_seq_length: int = 2048

    output_dir: str = "./lora-adapter"
    logging_dir: str = "./logs"

    num_train_epochs: int = 3
    per_device_train_batch_size: int = 1
    per_device_eval_batch_size: int = 1
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.03
    lr_scheduler_type: str = "cosine"
    weight_decay: float = 0.001

    gradient_checkpointing: bool = True
    optim: str = "paged_adamw_8bit"
    fp16: bool = False
    bf16: bool = True

    logging_steps: int = 10
    eval_steps: int = 100
    save_steps: int = 200
    save_total_limit: int = 2
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "eval_loss"
    report_to: str = "none"

    dataloader_num_workers: int = 0
    remove_unused_columns: bool = False
    group_by_length: bool = True
    seed: int = 42

@dataclass
class InferenceConfig:
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", 8001))
    max_new_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.95
    repetition_penalty: float = 1.1
    do_sample: bool = True

_model_config    = ModelConfig()
_lora_config     = LoRAConfig()
_training_config = TrainingConfig()
_inference_config = InferenceConfig()

def get_model_config()     -> ModelConfig:     return _model_config
def get_lora_config()      -> LoRAConfig:      return _lora_config
def get_training_config()  -> TrainingConfig:  return _training_config
def get_inference_config() -> InferenceConfig: return _inference_config
