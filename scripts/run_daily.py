#!/usr/bin/env python3
"""
AI Digest - Daily orchestrator
Runs the full pipeline: fetch → generate cards → generate article
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
VENV_PYTHON = SCRIPT_DIR.parent / ".venv" / "bin" / "python3"

def run_script(script_name, date_str=None):
    """Run a script with optional date argument."""
    script_path = SCRIPT_DIR / script_name
    cmd = [str(VENV_PYTHON), str(script_path)]
    if date_str:
        cmd.append(date_str)
    
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0

def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n🚀 AI Digest Pipeline - {date_str}")
    print(f"{'='*60}")
    
    # Step 1: Fetch all data
    if not run_script("fetch_all.py", date_str):
        print("❌ Fetch failed")
        sys.exit(1)
    
    # Step 2: Generate carousel cards
    if not run_script("generate_cards.py", date_str):
        print("❌ Card generation failed")
        sys.exit(1)
    
    # Step 3: Generate Substack article
    if not run_script("generate_substack.py", date_str):
        print("❌ Substack generation failed")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"✅ AI Digest pipeline complete for {date_str}")
    print(f"{'='*60}")
    
    # Summary
    output_dir = SCRIPT_DIR.parent / "output" / date_str
    print(f"\nOutputs:")
    print(f"  📁 {output_dir}")
    print(f"  📊 data.json")
    print(f"  🎨 carousel/ (PNG cards)")
    print(f"  📝 substack.md")

if __name__ == "__main__":
    main()
