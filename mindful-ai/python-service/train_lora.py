
import argparse
import logging
import os
import sys
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer

sys.path.insert(0, str(Path(__file__).parent))
from config import get_model_config, get_lora_config, get_training_config
from data_utils import load_dataset, split_dataset, get_token_stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("train_lora")

def train(args):
    model_cfg    = get_model_config()
    lora_cfg     = get_lora_config()
    training_cfg = get_training_config()

    if args.model:       model_cfg.base_model_id         = args.model
    if args.dataset:     training_cfg.dataset_path       = args.dataset
    if args.output:      training_cfg.output_dir         = args.output
    if args.epochs:      training_cfg.num_train_epochs   = args.epochs
    if args.max_examples: pass

    logger.info("=" * 60)
    logger.info("MindfulAI — Gemma QLoRA Fine-Tuning")
    logger.info("=" * 60)
    logger.info(f"  Base model   : {model_cfg.base_model_id}")
    logger.info(f"  Dataset      : {training_cfg.dataset_path}")
    logger.info(f"  Output dir   : {training_cfg.output_dir}")
    logger.info(f"  LoRA rank    : {lora_cfg.r}")
    logger.info(f"  Epochs       : {training_cfg.num_train_epochs}")
    logger.info(f"  Batch size   : {training_cfg.per_device_train_batch_size} × {training_cfg.gradient_accumulation_steps} accumulation steps")
    logger.info(f"  CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"  GPU           : {torch.cuda.get_device_name(0)}")
        logger.info(f"  VRAM          : {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    logger.info("=" * 60)

    logger.info("Loading dataset...")
    raw_examples = load_dataset(
        training_cfg.dataset_path,
        max_examples=args.max_examples or None,
    )

    if len(raw_examples) < 10:
        raise ValueError(f"Dataset too small ({len(raw_examples)} examples). Check the dataset path.")

    train_texts, eval_texts = split_dataset(
        raw_examples,
        train_ratio=training_cfg.train_split,
        seed=training_cfg.seed,
    )

    train_dataset = Dataset.from_dict({"text": train_texts})
    eval_dataset  = Dataset.from_dict({"text": eval_texts})

    logger.info(f"  Train: {len(train_dataset)} examples")
    logger.info(f"  Eval : {len(eval_dataset)}  examples")

    logger.info(f"Loading tokenizer from {model_cfg.base_model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_cfg.base_model_id,
        trust_remote_code=True,
    )
    tokenizer.pad_token        = tokenizer.eos_token
    tokenizer.padding_side     = "right"

    if args.verbose:
        stats = get_token_stats(train_texts, tokenizer)
        logger.info(f"  Token stats: {stats}")

    logger.info("Configuring 4-bit quantization (QLoRA)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit              = model_cfg.load_in_4bit,
        bnb_4bit_quant_type       = model_cfg.bnb_4bit_quant_type,
        bnb_4bit_compute_dtype    = torch.bfloat16,
        bnb_4bit_use_double_quant = model_cfg.bnb_4bit_use_double_quant,
    )

    logger.info(f"Loading model {model_cfg.base_model_id}...")
    logger.info("  (This may take a few minutes on first download ~8GB)")

    model = AutoModelForCausalLM.from_pretrained(
        model_cfg.base_model_id,
        quantization_config          = bnb_config,
        device_map                   = "auto",
        trust_remote_code            = True,
        torch_dtype                  = torch.bfloat16,
        attn_implementation          = "eager",
    )
    model.config.use_cache = False

    logger.info("Preparing model for QLoRA training...")
    model = prepare_model_for_kbit_training(
        model,
        use_gradient_checkpointing=training_cfg.gradient_checkpointing,
    )

    logger.info(f"Applying LoRA — r={lora_cfg.r}, alpha={lora_cfg.lora_alpha}, targets: {lora_cfg.target_modules}")
    peft_config = LoraConfig(
        task_type      = TaskType.CAUSAL_LM,
        r              = lora_cfg.r,
        lora_alpha     = lora_cfg.lora_alpha,
        lora_dropout   = lora_cfg.lora_dropout,
        bias           = lora_cfg.bias,
        target_modules = lora_cfg.target_modules,
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    logger.info("Setting up training arguments...")
    training_args = TrainingArguments(
        output_dir                  = training_cfg.output_dir,
        num_train_epochs            = training_cfg.num_train_epochs,
        per_device_train_batch_size = training_cfg.per_device_train_batch_size,
        per_device_eval_batch_size  = training_cfg.per_device_eval_batch_size,
        gradient_accumulation_steps = training_cfg.gradient_accumulation_steps,
        gradient_checkpointing      = training_cfg.gradient_checkpointing,
        optim                       = training_cfg.optim,
        learning_rate               = training_cfg.learning_rate,
        lr_scheduler_type           = training_cfg.lr_scheduler_type,
        warmup_ratio                = training_cfg.warmup_ratio,
        weight_decay                = training_cfg.weight_decay,
        bf16                        = training_cfg.bf16,
        fp16                        = training_cfg.fp16,
        logging_dir                 = training_cfg.logging_dir,
        logging_steps               = training_cfg.logging_steps,
        eval_strategy               = "steps",
        eval_steps                  = training_cfg.eval_steps,
        save_steps                  = training_cfg.save_steps,
        save_total_limit            = training_cfg.save_total_limit,
        load_best_model_at_end      = training_cfg.load_best_model_at_end,
        metric_for_best_model       = training_cfg.metric_for_best_model,
        report_to                   = training_cfg.report_to,
        dataloader_num_workers      = training_cfg.dataloader_num_workers,
        remove_unused_columns       = training_cfg.remove_unused_columns,
        group_by_length             = training_cfg.group_by_length,
        seed                        = training_cfg.seed,
    )

    logger.info("Initializing SFTTrainer...")
    trainer = SFTTrainer(
        model           = model,
        args            = training_args,
        train_dataset   = train_dataset,
        eval_dataset    = eval_dataset,
        tokenizer       = tokenizer,
        dataset_text_field = "text",
        max_seq_length  = training_cfg.max_seq_length,
        packing         = False,
    )

    logger.info("🚀 Starting training...")
    logger.info(f"  Effective batch size: {training_cfg.per_device_train_batch_size * training_cfg.gradient_accumulation_steps}")

    train_result = trainer.train()

    logger.info("✅ Training complete!")
    logger.info(f"  Loss:     {train_result.training_loss:.4f}")
    logger.info(f"  Steps:    {train_result.global_step}")
    logger.info(f"  Runtime:  {train_result.metrics.get('train_runtime', 0):.0f}s")

    logger.info(f"Saving LoRA adapter weights to {training_cfg.output_dir}...")
    trainer.save_model(training_cfg.output_dir)
    tokenizer.save_pretrained(training_cfg.output_dir)

    logger.info(f"✅ Adapter saved to: {Path(training_cfg.output_dir).resolve()}")
    logger.info("To run inference: python inference.py")

    return train_result

def parse_args():
    parser = argparse.ArgumentParser(
        description="MindfulAI — Gemma QLoRA Fine-Tuning",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model",        type=str,   default=None,
                        help="HuggingFace model ID (overrides config)")
    parser.add_argument("--dataset",      type=str,   default=None,
                        help="Path to .jsonl dataset file")
    parser.add_argument("--output",       type=str,   default=None,
                        help="Output directory for LoRA adapter")
    parser.add_argument("--epochs",       type=int,   default=None,
                        help="Number of training epochs")
    parser.add_argument("--max_examples", type=int,   default=None,
                        help="Max training examples (for quick tests)")
    parser.add_argument("--verbose",      action="store_true",
                        help="Print extra dataset statistics")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    train(args)
