#!/usr/bin/env python3
"""
Script to modify the Bluesky client to remove handle suffixes from display
(e.g., .bsky.social). This modifies the sanitizeHandle function.

Configure the DEFAULT_SUFFIX variable below to match your domain.
"""
import os
import re

# CONFIGURATION: Set your default handle suffix here
DEFAULT_SUFFIX = '.bsky.social'

HANDLES_FILE = 'src/lib/strings/handles.ts'


def modify_handles_file():
    """Modify sanitizeHandle to strip suffix for display."""
    if not os.path.exists(HANDLES_FILE):
        print(f"Error: File not found: {HANDLES_FILE}")
        return False

    print(f"Reading {HANDLES_FILE}...")
    with open(HANDLES_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already modified
    if 'stripHandleSuffix' in content:
        print(f"{HANDLES_FILE} already modified.")
        return True

    # Add the stripHandleSuffix helper function after the imports
    helper_function = f'''
// Strip handle suffix for cleaner display
export function stripHandleSuffix(handle: string): string {{
  const parts = handle.split('.')
  return parts[0]
}}

// Add default suffix to a handle if it doesn't have one
export function ensureHandleSuffix(handle: string): string {{
  if (!handle.includes('.')) {{
    return handle + '{DEFAULT_SUFFIX}'
  }}
  return handle
}}
'''

    # Insert after imports (after the forceLTR import line)
    import_line = "import {forceLTR} from '#/lib/strings/bidi'"
    if import_line not in content:
        print("Error: Could not find import line to insert after.")
        return False

    content = content.replace(import_line, import_line + '\n' + helper_function)

    # Modify sanitizeHandle to use stripHandleSuffix
    old_sanitize = "const lowercasedWithPrefix = `${prefix}${handle.toLocaleLowerCase()}`"
    new_sanitize = "const lowercasedWithPrefix = `${prefix}${stripHandleSuffix(handle).toLocaleLowerCase()}`"

    if old_sanitize not in content:
        # Maybe already modified differently?
        if 'stripHandleSuffix' in content:
            print(f"{HANDLES_FILE} already uses stripHandleSuffix.")
        else:
            print("Error: Could not find sanitizeHandle code to modify.")
            return False
    else:
        content = content.replace(old_sanitize, new_sanitize)

    with open(HANDLES_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Successfully modified {HANDLES_FILE}")
    return True


DRAWER_FILE = 'src/view/shell/Drawer.tsx'
LEFTNAV_FILE = 'src/view/shell/desktop/LeftNav.tsx'

def modify_sidebar_files():
    """Fix raw handle usage in sidebar components."""
    modified = False
    
    # Fix Drawer.tsx - line 95: {profile?.displayName || account.handle}
    if os.path.exists(DRAWER_FILE):
        print(f"Reading {DRAWER_FILE}...")
        with open(DRAWER_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already modified
        if 'stripHandleSuffix(account.handle)' not in content:
            # Add import if not present
            if 'stripHandleSuffix' not in content:
                old_import = "import {sanitizeHandle} from '#/lib/strings/handles'"
                new_import = "import {sanitizeHandle, stripHandleSuffix} from '#/lib/strings/handles'"
                content = content.replace(old_import, new_import)
            
            # Fix the fallback display name
            old_code = '{profile?.displayName || account.handle}'
            new_code = '{profile?.displayName || stripHandleSuffix(account.handle)}'
            content = content.replace(old_code, new_code)
            
            with open(DRAWER_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Modified {DRAWER_FILE}")
            modified = True
        else:
            print(f"{DRAWER_FILE} already modified.")
    
    # Fix LeftNav.tsx - line 167: profile.displayName || profile.handle
    if os.path.exists(LEFTNAV_FILE):
        print(f"Reading {LEFTNAV_FILE}...")
        with open(LEFTNAV_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already modified
        if 'stripHandleSuffix(profile.handle)' not in content:
            # Add import if not present
            if 'stripHandleSuffix' not in content:
                old_import = "import {isInvalidHandle, sanitizeHandle} from '#/lib/strings/handles'"
                new_import = "import {isInvalidHandle, sanitizeHandle, stripHandleSuffix} from '#/lib/strings/handles'"
                content = content.replace(old_import, new_import)
            
            # Fix the fallback display name
            old_code = 'profile.displayName || profile.handle'
            new_code = 'profile.displayName || stripHandleSuffix(profile.handle)'
            content = content.replace(old_code, new_code)
            
            with open(LEFTNAV_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Modified {LEFTNAV_FILE}")
            modified = True
        else:
            print(f"{LEFTNAV_FILE} already modified.")
    
    return modified


RESOLVE_URI_FILE = 'src/state/queries/resolve-uri.ts'

def modify_resolve_uri():
    """Add default suffix to handles without one when resolving."""
    if not os.path.exists(RESOLVE_URI_FILE):
        print(f"Error: File not found: {RESOLVE_URI_FILE}")
        return False

    print(f"Reading {RESOLVE_URI_FILE}...")
    with open(RESOLVE_URI_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already modified
    if 'ensureHandleSuffix' in content:
        print(f"{RESOLVE_URI_FILE} already modified.")
        return True

    # Add import
    old_import = "import {STALE} from '#/state/queries'"
    new_import = """import {STALE} from '#/state/queries'
import {ensureHandleSuffix} from '#/lib/strings/handles'"""
    
    if old_import not in content:
        print("Error: Could not find import line in resolve-uri.ts")
        return False

    content = content.replace(old_import, new_import)

    # Modify the queryFn to add suffix before resolving
    old_code = '''if (!didOrHandle) return ''
      // Just return the did if it's already one
      if (didOrHandle.startsWith('did:')) return didOrHandle

      const res = await agent.resolveHandle({handle: didOrHandle})'''

    new_code = '''if (!didOrHandle) return ''
      // Just return the did if it's already one
      if (didOrHandle.startsWith('did:')) return didOrHandle

      // Add default suffix if handle has no dot
      const handleToResolve = ensureHandleSuffix(didOrHandle)
      const res = await agent.resolveHandle({handle: handleToResolve})'''

    if old_code not in content:
        print("Error: Could not find queryFn code in resolve-uri.ts")
        return False

    content = content.replace(old_code, new_code)

    with open(RESOLVE_URI_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Successfully modified {RESOLVE_URI_FILE}")
    return True

def main():
    print(f"Configuring handle suffix system with default: {DEFAULT_SUFFIX}")
    print("=" * 60)

    success1 = modify_handles_file()
    success2 = modify_sidebar_files()
    success3 = modify_resolve_uri()

    print("=" * 60)
    if success1:
        print("✅ Handle suffix removal configured successfully!")
        print(f"   - Display: 'user{DEFAULT_SUFFIX}' → '@user'")
        print(f"   - URLs: '/profile/user' → resolves to 'user{DEFAULT_SUFFIX}'")
    else:
        print("⚠️  Some modifications failed. Check error messages above.")


if __name__ == "__main__":
    main()
