#!/usr/bin/env python3
"""
Script to hide post metadata (username, date) in the feed view.
Posts will only show their content/media. The metadata will still be
visible when clicking on the post (in thread view).
"""
import os
import re

POST_FEED_ITEM_FILE = 'src/view/com/posts/PostFeedItem.tsx'


def modify_post_feed_item():
    """Comment out PostMeta component in feed items."""
    if not os.path.exists(POST_FEED_ITEM_FILE):
        print(f"Error: File not found: {POST_FEED_ITEM_FILE}")
        return False

    print(f"Reading {POST_FEED_ITEM_FILE}...")
    with open(POST_FEED_ITEM_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already modified
    if '{/* <PostMeta' in content:
        print(f"{POST_FEED_ITEM_FILE} already modified.")
        return True

    # Comment out the PostMeta component
    old_code = '''<PostMeta
            author={post.author}
            moderation={moderation}
            timestamp={post.indexedAt}
            postHref={href}
            onOpenAuthor={onOpenAuthor}
          />'''

    new_code = '''{/* <PostMeta
            author={post.author}
            moderation={moderation}
            timestamp={post.indexedAt}
            postHref={href}
            onOpenAuthor={onOpenAuthor}
          /> */}'''

    if old_code not in content:
        print("Error: Could not find PostMeta code to comment out.")
        print("The file structure may have changed.")
        return False

    content = content.replace(old_code, new_code)

    with open(POST_FEED_ITEM_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Successfully modified {POST_FEED_ITEM_FILE}")
    return True


def main():
    print("Hiding post metadata in feed view...")
    print("=" * 60)

    success = modify_post_feed_item()

    print("=" * 60)
    if success:
        print("✅ Post metadata hidden successfully!")
        print("   Posts in feed will no longer show username/date")
        print("   Metadata is still visible when opening post thread")
    else:
        print("⚠️  Modification failed. Check error messages above.")


if __name__ == "__main__":
    main()
