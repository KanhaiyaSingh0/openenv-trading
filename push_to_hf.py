"""Push the trading environment to HuggingFace Spaces."""
import os
import sys

from huggingface_hub import HfApi, create_repo

REPO_ID = "kanhaiya1/openenv-trading"
SPACE_SDK = "docker"

# Files to upload (exclude venv, pycache, .env, egg-info, etc.)
EXCLUDE_DIRS = {"myvenv", "__pycache__", ".git", "openenv-trading", "openenv_trading.egg-info", ".gemini"}
EXCLUDE_FILES = {".env", "uv.lock"}

def main():
    api = HfApi()
    
    # Create the space repo (or update if it exists)
    try:
        create_repo(
            repo_id=REPO_ID,
            repo_type="space",
            space_sdk=SPACE_SDK,
            exist_ok=True,
        )
        print(f"Space repo '{REPO_ID}' created/confirmed.")
    except Exception as e:
        print(f"Repo creation: {e}")
    
    # Collect files to upload
    root = os.path.dirname(os.path.abspath(__file__))
    files_to_upload = []
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        for filename in filenames:
            if filename in EXCLUDE_FILES:
                continue
            if filename.endswith(('.pyc', '.pyo')):
                continue
                
            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, root)
            # Normalize path separators for HF
            relpath = relpath.replace("\\", "/")
            files_to_upload.append((filepath, relpath))
    
    print(f"\nUploading {len(files_to_upload)} files to {REPO_ID}...")
    for _, relpath in files_to_upload:
        print(f"  {relpath}")
    
    # Upload all files
    api.upload_folder(
        folder_path=root,
        repo_id=REPO_ID,
        repo_type="space",
        ignore_patterns=[
            "myvenv/**",
            "__pycache__/**",
            ".git/**",
            "openenv-trading/**",
            "openenv_trading.egg-info/**",
            ".gemini/**",
            ".env",
            "uv.lock",
            "*.pyc",
            "push_to_hf.py",
        ],
    )
    
    print(f"\nDone! Space: https://huggingface.co/spaces/{REPO_ID}")
    print("Wait for the Space to build and show 'Running' status before submitting.")


if __name__ == "__main__":
    main()
