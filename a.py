#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys

# Script mapping configuration
SCRIPT_MAP = {
    'A': {'file': 'apply_ai_changes.py', 'desc': 'Add AI creation dialog and components'},
    'B': {'file': 'apply_media_filter.py', 'desc': 'Apply media filter logic to feed'},
    'C': {'file': 'comment_out_ui.py', 'desc': 'Comment out UI elements'},
    'D': {'file': 'hide_post_meta.py', 'desc': 'Hide post metadata'},
    'E': {'file': 'hide_replies_from_feed.py', 'desc': 'Hide replies from feed'},
    'F': {'file': 'remove_handle_suffix.py', 'desc': 'Remove handle suffix'},
    'G': {'file': 'remove_replied_to.py', 'desc': 'Remove "replied to" indicator'},
    'H': {'file': 'setup_inline_text_post.py', 'desc': 'Setup inline layout for text posts'},
    'I': {'file': 'setup_reply_overlay.py', 'desc': 'Setup reply overlay system'},
    'J': {'file': 'process_feed_ui.py', 'desc': 'Process Feed UI (Hide elements / Text-only linking)'},
}

def print_menu():
    print("\nAvailable Scripts:")
    print("-" * 50)
    print("  1: Run ALL scripts (in alphabetical order)")
    for key, info in sorted(SCRIPT_MAP.items()):
        print(f"  {key}: {info['desc']} ({info['file']})")
    print("-" * 50)

def run_script(key):
    if key not in SCRIPT_MAP:
        print(f"Error: Unknown script key '{key}'")
        return False
    
    script_info = SCRIPT_MAP[key]
    script_file = script_info['file']
    
    if not os.path.exists(script_file):
        print(f"Error: Script file not found: {script_file}")
        return False
        
    print(f"\n[{key}] Running: {script_info['desc']}...")
    try:
        # Run the script and capture output
        result = subprocess.run([sys.executable, script_file], capture_output=True, text=True)
        
        # Print output regardless of success, indented slightly
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("stderr:", result.stderr)
            
        if result.returncode != 0:
            print(f"❌ Script {key} failed with exit code {result.returncode}")
            return False
            
        print(f"✅ Script {key} completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to run script {key}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run multiple social-app setup scripts in sequence.')
    parser.add_argument('scripts', nargs='?', help='String of script keys to run (e.g. "ABC") or "1" for all.')
    args = parser.parse_args()
    
    # If no arguments provided, show menu and interactive prompt
    if not args.scripts:
        print_menu()
        try:
            selection = input("\nEnter script keys to run (e.g. ABC) or 1 for ALL: ").strip().upper()
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(0)
    else:
        selection = args.scripts.strip().upper()
        
    if not selection:
        print("No scripts selected.")
        return

    # Handle "1" for all scripts
    if selection == '1':
        selection = "".join(sorted(SCRIPT_MAP.keys()))
        print("Selected ALL scripts.")

    # Validate inputs
    invalid_keys = [k for k in selection if k not in SCRIPT_MAP]
    if invalid_keys:
        print(f"Error: Invalid keys found: {', '.join(invalid_keys)}")
        print_menu()
        sys.exit(1)
        
    # Confirmation for multiple scripts
    if len(selection) > 1:
        print(f"\nWill run {len(selection)} scripts in this order: {', '.join(selection)}")
        # If running from arg, we proceed. If interactive, user just pressed enter.
        
    print(f"\nStarting execution of sequence: {selection}")
    
    success_count = 0
    fail_count = 0
    
    for key in selection:
        if run_script(key):
            success_count += 1
        else:
            fail_count += 1
            # Option: Stop on failure? For now, we continue.
            print(f"⚠️  Continuing to next script...")
            
    print("\n" + "=" * 50)
    print(f"Execution Summary: {success_count} succeeded, {fail_count} failed")
    print("=" * 50)

if __name__ == "__main__":
    main()
