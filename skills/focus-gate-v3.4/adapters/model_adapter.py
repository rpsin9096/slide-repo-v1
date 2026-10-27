"""Hexagonal Model Adapters for FocusGate v2.8.

Provides typed interfaces and concrete adapters for distilled Student router models,
LoRA adapters, safetensors parameter auditing, and Invariant Action Envelope routing.
Maintains 100% Python standard library compatibility with zero mandatory external dependencies.
"""

from abc import ABC, abstractmethod
import os
import sys
import json
import hashlib
import math
import re
from typing import Dict, Any, List, Optional, Tuple


class ModelPort(ABC):
    """Abstract port for Student model and router adapter operations."""

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if model weights and configurations are present on disk."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Returns metadata summary of the model/adapter."""
        pass

    @abstractmethod
    def verify_integrity(self) -> Dict[str, Any]:
        """Performs cryptographic and structural verification of model artifacts."""
        pass

    @abstractmethod
    def route(self, query: str, context: Optional[str] = None, force_fast_path: bool = False) -> Dict[str, Any]:
        """Routes a task query to an execution pipeline and Action Envelope."""
        pass

    @abstractmethod
    def parse_action_envelope(self, output_text: str) -> Dict[str, Any]:
        """Parses a generated raw text completion into structured Action Envelope fields."""
        pass


class LoRAModelAdapter(ModelPort):
    """Hexagonal adapter for fine-tuned LoRA router models (Qwen2.5/Llama-3 student routers).
    
    Operates in two modes:
    1. Neural Execution: If torch and peft/transformers are present in Python runtime.
    2. Pure Python Stdlib Fast-Path: 100% zero-dependency inspection, parameter auditing,
       cryptographic verification, and deterministic synthesis fallback.
    """

    DEFAULT_RELATIVE_DIRS = [
        os.path.join("models", "router_adapter"),
        os.path.join("dist", "focus-gate-v2.8", "models", "lora_adapter"),
        os.path.join(".focusgate", "models", "router_adapter"),
        # Removed in v3.2 Loop 64: "/Users/raul/Downloads/focusgate_v28_router_adapter".
        # A literal home-directory path cannot resolve on any other machine, so
        # it was dead code outside the author's laptop, and it published the
        # author's home directory into the source. Pass `adapter_dir=` explicitly,
        # or set FOCUSGATE_ROUTER_ADAPTER, to point at a local export.
    ]
    ENV_ADAPTER_DIR = "FOCUSGATE_ROUTER_ADAPTER"

    def __init__(self, adapter_dir: Optional[str] = None, repo_root: Optional[str] = None):
        self.repo_root = repo_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.adapter_dir = self._resolve_adapter_dir(adapter_dir)
        self._cached_verification: Optional[Dict[str, Any]] = None

    def _resolve_adapter_dir(self, explicit_dir: Optional[str]) -> Optional[str]:
        if explicit_dir and os.path.isdir(explicit_dir):
            return os.path.abspath(explicit_dir)

        # Replaces the hardcoded absolute path removed above: a machine-local
        # export directory, named by the environment rather than baked in.
        env_dir = os.environ.get(self.ENV_ADAPTER_DIR)
        if env_dir and os.path.isdir(env_dir):
            full = os.path.join(self.repo_root, env_dir) \
                if not os.path.isabs(env_dir) else env_dir
            if os.path.isdir(full):
                return os.path.abspath(full)

        for candidate in self.DEFAULT_RELATIVE_DIRS:
            full_path = candidate if os.path.isabs(candidate) else os.path.join(self.repo_root, candidate)
            if os.path.isdir(full_path):
                config_file = os.path.join(full_path, "adapter_config.json")
                weights_file = os.path.join(full_path, "adapter_model.safetensors")
                if os.path.exists(config_file) or os.path.exists(weights_file):
                    return os.path.abspath(full_path)

        if explicit_dir:
            return os.path.abspath(explicit_dir)
        return None

    def is_available(self) -> bool:
        if not self.adapter_dir or not os.path.isdir(self.adapter_dir):
            return False
        config_path = os.path.join(self.adapter_dir, "adapter_config.json")
        weights_path = os.path.join(self.adapter_dir, "adapter_model.safetensors")
        return os.path.exists(config_path) and os.path.exists(weights_path)

    def read_safetensors_header(self) -> Tuple[Dict[str, Any], int]:
        """Reads safetensors metadata and tensor shapes using pure standard library."""
        if not self.is_available():
            raise FileNotFoundError(f"Adapter not available at: {self.adapter_dir}")
        weights_path = os.path.join(self.adapter_dir, "adapter_model.safetensors")
        with open(weights_path, "rb") as f:
            header_size = int.from_bytes(f.read(8), "little")
            header_json = f.read(header_size).decode("utf-8")
            header = json.loads(header_json)

        tensors = {k: v for k, v in header.items() if k != "__metadata__"}
        total_params = sum(math.prod(v["shape"]) for v in tensors.values())
        return tensors, total_params

    def calculate_checksum(self) -> str:
        """Computes streaming SHA-256 of adapter weights."""
        if not self.is_available():
            return ""
        weights_path = os.path.join(self.adapter_dir, "adapter_model.safetensors")
        h = hashlib.sha256()
        with open(weights_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def verify_integrity(self) -> Dict[str, Any]:
        """Performs full structural, parameter, and cryptographic verification."""
        if self._cached_verification:
            return dict(self._cached_verification)

        if not self.is_available():
            res = {
                "valid": False,
                "adapter_dir": self.adapter_dir,
                "errors": [f"Missing adapter directory or required weight files at: {self.adapter_dir}"]
            }
            return res

        errors = []
        config_path = os.path.join(self.adapter_dir, "adapter_config.json")
        weights_path = os.path.join(self.adapter_dir, "adapter_model.safetensors")
        tokenizer_config_path = os.path.join(self.adapter_dir, "tokenizer_config.json")

        cfg = {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            errors.append(f"Failed parsing adapter_config.json: {e}")

        base_model = cfg.get("base_model_name_or_path", "unknown")
        peft_type = cfg.get("peft_type", "unknown")
        rank = cfg.get("r", 0)
        lora_alpha = cfg.get("lora_alpha", 0)
        target_modules = cfg.get("target_modules", [])

        if peft_type.upper() != "LORA":
            errors.append(f"Expected peft_type 'LORA', got '{peft_type}'")

        try:
            tensors, total_params = self.read_safetensors_header()
            tensor_count = len(tensors)
        except Exception as e:
            errors.append(f"Failed parsing safetensors header: {e}")
            tensor_count = 0
            total_params = 0

        checksum = self.calculate_checksum()
        weights_size_bytes = os.path.getsize(weights_path) if os.path.exists(weights_path) else 0

        has_tokenizer = os.path.exists(tokenizer_config_path)
        neural_runtime_available = False
        try:
            import torch  # noqa: F401
            import peft   # noqa: F401
            import transformers  # noqa: F401
            neural_runtime_available = True
        except ImportError:
            neural_runtime_available = False

        res = {
            "valid": len(errors) == 0,
            "adapter_dir": self.adapter_dir,
            "base_model": base_model,
            "peft_type": peft_type,
            "r": rank,
            "lora_alpha": lora_alpha,
            "target_modules": target_modules,
            "tensor_count": tensor_count,
            "trainable_parameters": total_params,
            "weights_size_bytes": weights_size_bytes,
            "checksum": checksum,
            "has_tokenizer": has_tokenizer,
            "neural_runtime_available": neural_runtime_available,
            "errors": errors
        }
        self._cached_verification = res
        return res

    def get_metadata(self) -> Dict[str, Any]:
        info = self.verify_integrity()
        if not info["valid"]:
            return {
                "adapter_id": "unavailable",
                "status": "MISSING",
                "errors": info.get("errors", [])
            }
        return {
            "adapter_id": "focusgate_v28_router_adapter",
            "status": "VERIFIED",
            "base_model": info["base_model"],
            "peft_type": info["peft_type"],
            "rank": info["r"],
            "alpha": info["lora_alpha"],
            "trainable_parameters": info["trainable_parameters"],
            "tensor_count": info["tensor_count"],
            "checksum": info["checksum"],
            "checksum_short": info["checksum"][:12] if info["checksum"] else "",
            "weights_size_mb": round(info["weights_size_bytes"] / (1024 * 1024), 2)
        }

    def route(self, query: str, context: Optional[str] = None, force_fast_path: bool = False) -> Dict[str, Any]:
        """Routes task description via neural student or deterministic synthesis."""
        integrity = self.verify_integrity()

        # Attempt neural inference if available and not forced to fast-path
        if integrity.get("neural_runtime_available") and not force_fast_path:
            neural_res = self._execute_neural_inference(query, context)
            if neural_res:
                return neural_res

        # Pure Python deterministic fast-path
        return self._execute_fast_path(query, context, integrity)

    def _execute_fast_path(self, query: str, context: Optional[str], integrity: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from scripts.compiler.dspy_signatures import compile_pipeline_plan
            plan = compile_pipeline_plan(query)
        except Exception:
            try:
                # Lazy import from engine
                import importlib.util
                engine_path = os.path.join(self.repo_root, "scripts", "focus-gate.py")
                spec = importlib.util.spec_from_file_location("focus_gate_cli", engine_path)
                fg = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(fg)
                plan = fg.PipelineSynthesizer.synthesize(query)
            except Exception:
                plan = {
                    "archetype": "ATOMIC",
                    "pipeline": "Atomic Sprint",
                    "stages": [{"facet": "unlazy", "description": "Execute atomic micro-step"}],
                    "est_minutes": 10,
                    "seed_step": {
                        "action": f"Execute atomic step for: {query}",
                        "check": "git status",
                        "expect": "On branch"
                    }
                }

        envelope = self.format_action_envelope(query, plan)
        return {
            "query": query,
            "archetype": plan.get("archetype", "ATOMIC"),
            "pipeline": plan.get("pipeline", "Atomic Sprint"),
            "stages": plan.get("stages", []),
            "est_minutes": plan.get("est_minutes", 10),
            "seed_step": plan.get("seed_step", {}),
            "action_envelope": envelope,
            "routed_by": "LoRAModelAdapter (FastPath-Stdlib)",
            "adapter_verified": integrity.get("valid", False),
            "adapter_checksum": integrity.get("checksum", ""),
            "inference_mode": "fast_path_stdlib"
        }

    def _execute_neural_inference(self, query: str, context: Optional[str]) -> Optional[Dict[str, Any]]:
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
            from peft import PeftModel

            config_path = os.path.join(self.adapter_dir, "adapter_config.json")
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            base_model_id = cfg.get("base_model_name_or_path", "Qwen/Qwen2.5-1.5B-Instruct")

            tokenizer = AutoTokenizer.from_pretrained(self.adapter_dir, trust_remote_code=True)
            device = "cuda" if torch.cuda.is_available() else ("mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else "cpu")

            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                torch_dtype=torch.float16 if device in ("cuda", "mps") else torch.float32,
                device_map="auto" if device == "cuda" else None,
                trust_remote_code=True
            )
            model = PeftModel.from_pretrained(base_model, self.adapter_dir)
            model.eval()

            system_prompt = (
                "You are FocusGate v2.8, an ultra-compact, deterministic agent orchestration router. "
                "Classify user tasks, select canonical pipelines (P1-P11), and format outputs in the Invariant Action Envelope."
            )
            user_content = query
            if context:
                user_content += f"\n\nContext:\n{context}"

            prompt = (
                f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
                f"<|im_start|>user\n{user_content}<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )

            inputs = tokenizer(prompt, return_tensors="pt").to(device)
            with torch.no_grad():
                out = model.generate(
                    **inputs,
                    max_new_tokens=220,
                    do_sample=False,
                    temperature=0.0,
                    pad_token_id=tokenizer.eos_token_id
                )
            generated_text = tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

            parsed = self.parse_action_envelope(generated_text)
            parsed["query"] = query
            parsed["action_envelope"] = generated_text
            parsed["routed_by"] = "LoRAModelAdapter (Neural)"
            parsed["adapter_verified"] = True
            parsed["adapter_checksum"] = self.calculate_checksum()
            parsed["inference_mode"] = "neural"
            return parsed
        except Exception:
            return None

    def format_action_envelope(self, query: str, plan: Dict[str, Any]) -> str:
        pipeline = plan.get("pipeline", "Atomic Sprint")
        stages = plan.get("stages", [])
        est_min = plan.get("est_minutes", 10)
        seed = plan.get("seed_step", {})

        action = seed.get("action", f"Execute atomic step for: {query}")
        check = seed.get("check", "git status")
        expect = seed.get("expect", "On branch")

        total_stages = max(len(stages), 1)
        first_stage_name = stages[0]["facet"] if stages else "unlazy"

        lines = [
            f"▶ NEXT ACTION: {action}",
            f"State: [Pipeline: {pipeline} (Stage 1/{total_stages}: {first_stage_name})] [Active Gate: gate-1-active] [Queue: 1 active, {max(total_stages-1, 0)} buffered] [Est: {est_min} min] [Depth: L1]",
            "",
            f"■ ACTIVE FOCUS: Execute initial stage gate for '{query}'.",
        ]
        for idx, s in enumerate(stages[:3], 1):
            lines.append(f"{idx}. [{s['facet']}] {s['description']}")
        lines.append(f"CHECK: {check}")
        lines.append(f"EXPECT: {expect}")

        return "\n".join(lines)

    def parse_action_envelope(self, output_text: str) -> Dict[str, Any]:
        """Extracts structured fields from raw Action Envelope string."""
        next_action_m = re.search(r"▶ NEXT ACTION:\s*(.+)", output_text)
        state_m = re.search(r"State:\s*\[Pipeline:\s*([^\]]+)\]\s*\[Active Gate:\s*([^\]]+)\]\s*\[Queue:\s*([^\]]+)\]\s*\[Est:\s*(\d+)\s*min\]\s*\[Depth:\s*([^\]]+)\]", output_text)
        focus_m = re.search(r"■ ACTIVE FOCUS:\s*(.+)", output_text)

        pipeline = state_m.group(1).strip() if state_m else "Atomic Sprint"
        active_gate = state_m.group(2).strip() if state_m else "gate-1-active"
        est_min = int(state_m.group(4)) if state_m else 10
        next_action = next_action_m.group(1).strip() if next_action_m else "git status"
        active_focus = focus_m.group(1).strip() if focus_m else "Active task execution"

        return {
            "pipeline": pipeline,
            "active_gate": active_gate,
            "est_minutes": est_min,
            "next_action": next_action,
            "active_focus": active_focus,
            "seed_step": {
                "action": next_action,
                "check": "git status",
                "expect": "On branch"
            }
        }
