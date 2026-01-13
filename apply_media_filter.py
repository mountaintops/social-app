import os
import re

TARGET_FILE = 'src/view/com/posts/PostFeed.tsx'

FILTER_LOGIC = """              if (
                feedKind === 'following' ||
                feedKind === 'discover' ||
                feedKind === 'profile'
              ) {
                let videoCount = 0
                let imageCount = 0
                for (const item of slice.items) {
                  if (AppBskyEmbedVideo.isView(item.post.embed)) {
                    videoCount++
                  } else if (AppBskyEmbedImages.isView(item.post.embed)) {
                    imageCount++
                  } else if (
                    AppBskyEmbedRecordWithMedia.isView(item.post.embed)
                  ) {
                    if (AppBskyEmbedVideo.isView(item.post.embed.media)) {
                      videoCount++
                    } else if (
                      AppBskyEmbedImages.isView(item.post.embed.media)
                    ) {
                      imageCount++
                    }
                  }
                }
                if (videoCount < 1 || imageCount < 1) {
                  continue
                }
              }
"""

def process_imports(content):
    # Regex to find the @atproto/api import block
    # It might be multi-line.
    # Pattern looks for: import { ... } from '@atproto/api'
    pattern = r'(import\s*\{[^}]+\}\s*from\s*\'@atproto/api\')'
    
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print("Error: Could not find @atproto/api imports.")
        return content

    import_block = match.group(0)
    
    required_imports = [
        'AppBskyEmbedImages',
        'AppBskyEmbedRecordWithMedia',
        'AppBskyEmbedVideo'
    ]
    
    new_import_block = import_block
    for imp in required_imports:
        if imp not in new_import_block:
            # Add to the list. We assume the list ends with '}'
            # We'll insert before the last '}'
            new_import_block = new_import_block.rsplit('}', 1)
            new_import_block = f"{new_import_block[0]}, {imp}\n}}"
            # Clean up potential double commas or awkward spacing if we cared, 
            # but Typescript is forgiving.
            # Let's make it slightly nicer by ensuring a comma before.
            # Actually, standardizing is hard without a parser. 
            # Simple append is checking if ',' exists?
            # Let's just rely on the fact that we are injecting into a { ... } block.
            # A safer way: replace "}" with ", imp, }"
            # But the existing block might look like:
            # {
            #   Foo,
            #   Bar,
            # }
            # Replacing } with , New } works.
    
    # Let's try a simpler approach for imports:
    # Just look for the closing '}' in the match and insert our imports before it.
    
    replacements = []
    
    # Check what is missing
    missing = [req for req in required_imports if req not in import_block]
    
    if not missing:
        print("Imports already present.")
        return content

    print(f"Adding missing imports: {missing}")
    
    # Construct new imports string
    to_add = ",\n  ".join(missing)
    
    # We want to insert `to_add` before the closing `}` of the import block.
    # The import block is `import_block`.
    # Find the last `}` in `import_block`
    last_brace_idx = import_block.rfind('}')
    if last_brace_idx == -1:
        return content # Should not happen given regex
    
    prefix = import_block[:last_brace_idx]
    suffix = import_block[last_brace_idx:]
    
    # Check if the last encoded character was a comma
    if prefix.rstrip().endswith(','):
        connector = "\n  "
    else:
        connector = ",\n  "

    updated_import_block = prefix + connector + to_add + "\n" + suffix
    
    return content.replace(import_block, updated_import_block)

def process_logic(content):
    # Target: inside the loop `for (const slice of page.slices) {`
    # BUT only the one inside `for (const page of data?.pages) {` (which is the main feed, not video feed).
    
    # We will look for the sequence.
    # context line: "for (const page of data?.pages) {"
    # target line: "for (const slice of page.slices) {"
    
    if FILTER_LOGIC.strip() in content:
        print("Filter logic already applied.")
        return content

    lines = content.split('\n')
    new_lines = []
    
    # Simple state machine
    # 0 = searching for outer loop
    # 1 = searching for inner loop
    state = 0
    
    for line in lines:
        new_lines.append(line)
        
        if state == 0:
            if "for (const page of data?.pages) {" in line:
                state = 1
        elif state == 1:
            if "for (const slice of page.slices) {" in line:
                print("Found target loop for logic injection.")
                new_lines.append(FILTER_LOGIC)
                state = 0 # specific injection done, return to search or finish if we only expect one.
                # If we expect only one, we could set state = 2.
                # But allowing state 0 is fine if there were multiple blocks (there aren't).
            
    return '\n'.join(new_lines)


def main():
    if not os.path.exists(TARGET_FILE):
        print(f"File not found: {TARGET_FILE}")
        return

    with open(TARGET_FILE, 'r') as f:
        content = f.read()

    new_content = process_imports(content)
    new_content = process_logic(new_content)

    if content != new_content:
        with open(TARGET_FILE, 'w') as f:
            f.write(new_content)
        print(f"Successfully modified {TARGET_FILE}")
    else:
        print("No changes needed.")

if __name__ == "__main__":
    main()
