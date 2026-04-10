"""Validate inference.py meets OpenEnv hackathon spec requirements."""

def main():
    with open("inference.py", "r") as f:
        code = f.read()
    
    checks = {
        "os.getenv with default API_BASE_URL": 'os.getenv("API_BASE_URL",' in code,
        "os.getenv with default MODEL_NAME": 'os.getenv("MODEL_NAME",' in code,
        "HF_TOKEN via os.getenv": 'os.getenv("HF_TOKEN")' in code,
        "raise ValueError for HF_TOKEN": "raise ValueError" in code,
        "No dotenv import": "dotenv" not in code,
        "No asyncio import": "asyncio" not in code,
        "No duplicate openai import": code.count("from openai import OpenAI") == 1,
        "[START] format present": "[START] task=" in code,
        "[STEP] format present": "[STEP] step=" in code,
        "[END] format present": "[END] success=" in code,
        "[END] has NO score= field": "score=" not in code.split("log_end")[1].split("def ")[0] if "log_end" in code else False,
        "Uses OpenAI client": "from openai import OpenAI" in code,
        "Synchronous main()": "def main()" in code,
    }
    
    all_pass = True
    for name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}] {name}")
    
    print()
    if all_pass:
        print("All checks PASSED! Your inference.py is spec-compliant.")
    else:
        print("Some checks FAILED. Fix the issues above before resubmitting.")

if __name__ == "__main__":
    main()
