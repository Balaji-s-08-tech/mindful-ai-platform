
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

import torch
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent))
from config import get_model_config, get_inference_config
from data_utils import format_conversation, SYSTEM_PROMPT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("gemma-inference")

_model     = None
_tokenizer = None
_model_loaded = False
_load_error   = None

def load_model():
    
    global _model, _tokenizer, _model_loaded, _load_error

    model_cfg   = get_model_config()
    infer_cfg   = get_inference_config()

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel

        logger.info(f"Loading tokenizer from {model_cfg.base_model_id}...")
        _tokenizer = AutoTokenizer.from_pretrained(
            model_cfg.base_model_id,
            trust_remote_code=True,
        )
        _tokenizer.pad_token    = _tokenizer.eos_token
        _tokenizer.padding_side = "left"

        load_kwargs = dict(
            trust_remote_code = True,
            torch_dtype       = torch.bfloat16,
            device_map        = "auto",
        )

        if model_cfg.load_in_4bit and torch.cuda.is_available():
            from transformers import BitsAndBytesConfig
            load_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit              = True,
                bnb_4bit_quant_type       = model_cfg.bnb_4bit_quant_type,
                bnb_4bit_compute_dtype    = torch.bfloat16,
                bnb_4bit_use_double_quant = model_cfg.bnb_4bit_use_double_quant,
            )

        logger.info(f"Loading base model {model_cfg.base_model_id}...")
        base_model = AutoModelForCausalLM.from_pretrained(
            model_cfg.base_model_id,
            **load_kwargs,
        )

        adapter_path = model_cfg.adapter_path
        if adapter_path and Path(adapter_path).exists():
            logger.info(f"Loading LoRA adapter from {adapter_path}...")
            _model = PeftModel.from_pretrained(base_model, adapter_path)
            _model = _model.merge_and_unload()
            logger.info("✅ LoRA adapter merged into base model")
        else:
            logger.info("No LoRA adapter found — using base model (run train_lora.py to fine-tune)")
            _model = base_model

        _model.eval()
        _model_loaded = True
        total_params  = sum(p.numel() for p in _model.parameters()) / 1e9

        logger.info(f"✅ Model loaded — {total_params:.1f}B parameters")
        if torch.cuda.is_available():
            vram_used = torch.cuda.memory_allocated() / 1e9
            logger.info(f"  VRAM used: {vram_used:.1f} GB")

    except Exception as e:
        _load_error   = str(e)
        _model_loaded = False
        logger.error(f"❌ Failed to load model: {e}", exc_info=True)
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Gemma inference service...")
    try:
        load_model()
    except Exception as e:
        logger.error(f"Model load failed: {e} — service will return 503 for /generate")
    yield
    logger.info("Shutting down inference service")

app = FastAPI(
    title       = "MindfulAI Gemma Inference",
    description = "Local Gemma 3 4B inference service with LoRA adapter",
    version     = "1.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = os.getenv("ALLOWED_ORIGINS", "http://localhost:5000").split(","),
    allow_methods  = ["GET", "POST"],
    allow_headers  = ["*"],
)

class MessageItem(BaseModel):
    role:    str
    content: str

class GenerateRequest(BaseModel):

    message:        str        = Field(..., description="User's message text")
    emotion:        str        = Field("neutral", description="Dominant detected emotion")
    confidence:     float      = Field(0.5, ge=0, le=1)
    input_type:     str        = Field("text", description="text or voice")
    system_prompt:  Optional[str] = Field(None, description="Full system prompt from promptBuilder")
    messages:       List[MessageItem] = Field([], description="Conversation history including current turn")

    max_new_tokens: Optional[int]   = None
    temperature:    Optional[float] = None

class GenerateResponse(BaseModel):
    content:    str
    model:      str
    tokens:     int
    latency_ms: float

@app.get("/health")
async def health():
    infer_cfg = get_inference_config()
    model_cfg = get_model_config()
    return {
        "status":         "ok" if _model_loaded else "degraded",
        "model_loaded":   _model_loaded,
        "base_model":     model_cfg.base_model_id,
        "adapter_path":   model_cfg.adapter_path,
        "load_error":     _load_error,
        "cuda_available": torch.cuda.is_available(),
        "timestamp":      time.time(),
        "port":           infer_cfg.port,
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    if not _model_loaded:
        raise HTTPException(
            status_code=503,
            detail=f"Model not loaded: {_load_error or 'Unknown error'}",
        )

    start      = time.time()
    infer_cfg  = get_inference_config()

    if request.messages:

        formatted_prompt = format_conversation(
            [{"role": m.role, "content": m.content} for m in request.messages],
            add_system=request.system_prompt is None,
        )
    else:

        formatted_prompt = format_conversation(
            [{"role": "user", "content": request.message}],
            add_system=True,
        )

    inputs = _tokenizer(
        formatted_prompt,
        return_tensors    = "pt",
        truncation        = True,
        max_length        = 4096,
        padding           = False,
    ).to(_model.device)

    input_length = inputs["input_ids"].shape[1]
    max_new      = request.max_new_tokens or infer_cfg.max_new_tokens
    temperature  = request.temperature    or infer_cfg.temperature

    with torch.no_grad():
        output_ids = _model.generate(
            **inputs,
            max_new_tokens      = max_new,
            temperature         = temperature,
            top_p               = infer_cfg.top_p,
            repetition_penalty  = infer_cfg.repetition_penalty,
            do_sample           = infer_cfg.do_sample,
            pad_token_id        = _tokenizer.eos_token_id,
            eos_token_id        = _tokenizer.eos_token_id,
        )

    new_tokens = output_ids[0][input_length:]
    response_text = _tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    latency_ms  = round((time.time() - start) * 1000, 1)
    tokens_used = len(new_tokens)

    model_cfg = get_model_config()
    adapter   = model_cfg.adapter_path
    model_id  = f"gemma-lora/{Path(adapter).name}" if (adapter and Path(adapter).exists()) else model_cfg.base_model_id

    logger.info(f"Generated {tokens_used} tokens in {latency_ms}ms — emotion: {request.emotion}")

    return GenerateResponse(
        content    = response_text,
        model      = model_id,
        tokens     = tokens_used,
        latency_ms = latency_ms,
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

if __name__ == "__main__":
    import uvicorn
    infer_cfg = get_inference_config()
    uvicorn.run(
        "inference:app",
        host      = infer_cfg.host,
        port      = infer_cfg.port,
        reload    = os.getenv("ENV", "development") == "development",
        log_level = "info",
    )
