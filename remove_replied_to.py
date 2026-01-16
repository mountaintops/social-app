import os

def remove_replied_to():
    file_path = 'src/components/Post/PostRepliedTo.tsx'
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    with open(file_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    found_function = False
    for line in lines:
        new_lines.append(line)
        if 'export function PostRepliedTo({' in line and not found_function:
            found_function = True
        
        if found_function and '}) {' in line:
            new_lines.append("  return null // Removed 'Replied to' text and icon\n")
            found_function = False # Only do it once

    with open(file_path, 'w') as f:
        f.writelines(new_lines)
    print(f"Successfully modified {file_path}")

if __name__ == "__main__":
    remove_replied_to()
