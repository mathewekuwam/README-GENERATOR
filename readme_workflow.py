"""
Complete README Generation Workflow
Automatically analyzes project and generates README with minimal user input.
"""

import sys
import subprocess
from pathlib import Path

def run_workflow():
    """Run the complete README generation workflow."""
    
    print("\n" + "=" * 80)
    print("🚀 COMPLETE README GENERATION WORKFLOW".center(80))
    print("=" * 80)
    print("\nThis workflow will:")
    print("  1️⃣  Auto-analyze your project (auto_readme_info.py)")
    print("  2️⃣  Generate a professional README (readme_generator.py)")
    print("\n" + "-" * 80)
    
    # Get project path
    project_path = input("\n📂 Enter your project folder path: ").strip().strip('"\'')
    
    if not project_path:
        print("❌ No path provided. Exiting.")
        return
    
    project_path = Path(project_path)
    if not project_path.exists():
        print(f"❌ Path does not exist: {project_path}")
        return
    
    print("\n" + "=" * 80)
    print("STEP 1: AUTO-ANALYZING PROJECT".center(80))
    print("=" * 80)
    
    # Check if auto_readme_info.py exists
    auto_script = Path(__file__).parent / 'auto_readme_info.py'
    
    if auto_script.exists():
        # Run auto-analysis
        try:
            result = subprocess.run(
                [sys.executable, str(auto_script)],
                input=f"{project_path}\ny\n",
                capture_output=False,
                text=True
            )
        except Exception as e:
            print(f"⚠️  Could not run auto-analysis: {e}")
            print("   Continuing with manual input...")
    else:
        print("⚠️  auto_readme_info.py not found")
        print("   Continuing with manual input...")
    
    print("\n" + "=" * 80)
    print("STEP 2: GENERATING README".center(80))
    print("=" * 80)
    
    # Check if readme_generator.py exists
    readme_script = Path(__file__).parent / 'readme_generator.py'
    
    if readme_script.exists():
        print("\n🎯 Running README generator...\n")
        try:
            subprocess.run([sys.executable, str(readme_script)])
        except Exception as e:
            print(f"❌ Error running README generator: {e}")
    else:
        print("❌ readme_generator.py not found in the same directory")
        print("   Please ensure both scripts are in the same folder.")
    
    print("\n" + "=" * 80)
    print("✅ WORKFLOW COMPLETE!".center(80))
    print("=" * 80)
    print("\nYour README.md should now be ready!")
    print("Check your project folder for the generated README.\n")


if __name__ == "__main__":
    run_workflow()