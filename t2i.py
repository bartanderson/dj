import os
import torch
import warnings
from pathlib import Path
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from diffusers.utils import logging as diffusers_logging

# ===== CRITICAL SETUP =====
# Suppress noisy warnings
warnings.filterwarnings("ignore")
diffusers_logging.set_verbosity_error()  # Silence diffusers logs
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow warnings

# Set cache directory
cache_dir = Path.home() / ".hf_cache"
os.environ["HF_HOME"] = str(cache_dir)
cache_dir.mkdir(exist_ok=True)

# ===== MODEL LOADING =====
def load_pipeline(model_path: Path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if device == "cuda" else torch.float32
    
    print(f"Loading model: {model_path.name}")
    print(f"Device: {device} | Precision: {torch_dtype}")
    
    # Load pipeline with custom settings
    pipe = StableDiffusionPipeline.from_single_file(
        pretrained_model_link_or_path=str(model_path),
        torch_dtype=torch_dtype,
        safety_checker=None,
        requires_safety_checker=False,
        load_safety_checker=False,
        cache_dir=str(cache_dir)
        )
    
    # Optimizations
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(
        pipe.scheduler.config, 
        use_karras_sigmas=True  # Better quality
    )
    pipe = pipe.to(device)
    
    if device == "cuda":
        pipe.enable_xformers_memory_efficient_attention()
        pipe.enable_model_cpu_offload()  # Reduce VRAM usage
    else:
        pipe.enable_attention_slicing()  # For CPU/low VRAM
    
    return pipe

# ===== IMAGE GENERATION =====
def generate_image(pipe, prompt: str, output_path: Path, width=768, height=768):
    print(f"Generating: '{prompt}'")
    
    # Generate with quality parameters
    result = pipe(
        prompt=prompt,
        negative_prompt="blurry, deformed, ugly, text, signature, watermark",
        width=width,  # Higher resolution for realisticVision
        height=height,
        num_inference_steps=30,  # More steps for detail
        guidance_scale=7.5,
        generator=torch.Generator(device=pipe.device).manual_seed(42)
        )
    
    result.images[0].save(output_path)
    print(f"Saved to: {output_path}")
    return output_path

# ===== MAIN EXECUTION =====
if __name__ == "__main__":
    # Model selection
    model_dir = Path.home() / ".sdkit" / "models" / "stable-diffusion"
    model_path = model_dir / "realisticVisionV60B1_v51VAE.safetensors"
    
    # Verify model
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        exit(1)
        
    # Load once and reuse
    pipeline = load_pipeline(model_path)
    
    # Generate multiple images
    prompts = [
        #"A photorealistic portrait of a scientist in a lab, intricate details, 8k",
        #"Futuristic cityscape at sunset, cinematic lighting, ultra detailed",
        #"Close-up of a mechanical watch, steampunk style, sharp focus"
        "rubble, close up of 4 rocks"
    ]
    
    for i, prompt in enumerate(prompts):
        output_path = Path.cwd() / f"output_{i}.jpg"
        generate_image(pipeline, prompt, output_path) # divisible by 8
    
    print("\n✨ All generations complete!")