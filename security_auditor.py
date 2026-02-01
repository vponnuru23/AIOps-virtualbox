import ollama
import os
import json
import re

def read_local_repo(directory="."):
    """Reads all Python files, skipping environments and git history."""
    code_bundle = ""
    excludes = {"myenv", ".git", "__pycache__", "venv"}
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in excludes]
        for file in files:
            if file.endswith(".py") and file != "security_auditor.py":
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code_bundle += f"\n--- FILE: {file_path} ---\n{f.read()}\n"
                except Exception as e:
                    print(f"?? Could not read {file_path}: {e}")
    return code_bundle

def run_security_audit():
    model_name = "qwen2.5-coder:1.5b"
    
    print(f"?? Reading local repository for {model_name}...")
    code_content = read_local_repo()
    
    if not code_content:
        print("? No code files found to scan.")
        return

    # UPDATED: Python-centric prompt for the 1.5B model
    security_prompt = f"""
You are a security auditor. Perform a thorough security review of this Python project.

**Checks to Perform**
1) Code-level: Input validation (path traversal), Command injection (subprocess), Deserialization (pickle/yaml), Insecure Crypto (hashlib/secrets).
2) Secrets: Hardcoded tokens, .env files, credentials in strings.
3) Infrastructure: Dockerfile best practices (non-root USER), requirements.txt vulnerabilities.

**Output Format**
- Provide a **Summary Table** of findings.
- For each finding: Title, Severity, CWE, and Recommendation.
- **IMPORTANT**: End your response with a valid SARIF v2.1.0 JSON block inside triple backticks (```json ... ```).

**CODE TO SCAN:**
{code_content}
"""

    print(f"?? Running Security Audit using {model_name}...")
    
    try:
        response = ollama.generate(
            model=model_name,
            prompt=security_prompt,
            stream=False,
            options={
                "num_ctx": 8192, 
                "temperature": 0 
            }
        )

        full_output = response['response']
        print(full_output)
        
        # 1. Save Human Report
        with open("security_audit_report.md", "w", encoding='utf-8') as f:
            f.write(full_output)
        print("\n? Human-readable report saved to 'security_audit_report.md'")

        # 2. ROBUST SARIF EXTRACTION (Uses Regex to find JSON block)
        json_match = re.search(r"```json\s*(.*?)\s*```", full_output, re.DOTALL)
        if not json_match:
            # Fallback for plain backticks without 'json' label
            json_match = re.search(r"```\s*(\{\s*\"\$schema\".*?)\s*```", full_output, re.DOTALL)

        if json_match:
            sarif_part = json_match.group(1).strip()
            try:
                # Test if it's valid JSON
                json.loads(sarif_part)
                with open("audit_results.sarif", "w", encoding='utf-8') as f:
                    f.write(sarif_part)
                print("?? SARIF results saved to 'audit_results.sarif'")
            except json.JSONDecodeError:
                print("?? SARIF JSON found but contains syntax errors.")
        else:
            print("?? SARIF JSON block not found in output.")

    except Exception as e:
        print(f"? Error during AI generation: {e}")

if __name__ == "__main__":
    run_security_audit()
