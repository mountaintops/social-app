#!/usr/bin/env python3
"""
Script to add reply overlay UI to posts.
Reply media thumbnails will appear as overlays on the main post.
"""
import os

POST_FEED_ITEM_FILE = 'src/view/com/posts/PostFeedItem.tsx'
REPLY_OVERLAY_FILE = 'src/components/ReplyOverlay.tsx'
REPLY_MEDIA_QUERY_FILE = 'src/state/queries/reply-media.ts'


def check_files_exist():
    """Check if required files exist."""
    files = [REPLY_OVERLAY_FILE, REPLY_MEDIA_QUERY_FILE]
    for f in files:
        if not os.path.exists(f):
            print(f"Error: {f} not found.")
            return False
    return True


def modify_post_feed_item():
    """Add ReplyOverlay to PostFeedItem."""
    if not os.path.exists(POST_FEED_ITEM_FILE):
        print(f"Error: File not found: {POST_FEED_ITEM_FILE}")
        return False

    print(f"Reading {POST_FEED_ITEM_FILE}...")
    with open(POST_FEED_ITEM_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already modified with full implementation
    if 'useReplyMediaQuery' in content:
        print(f"{POST_FEED_ITEM_FILE} already modified with reply overlay.")
        return True

    # First, remove any partial modifications from earlier runs
    # (the commented out version)
    if '{/* <ReplyOverlay' in content:
        # Need to completely redo
        print("Found partial modification, rebuilding...")
    
    # Add imports
    if 'ReplyOverlay' not in content:
        import_marker = "import {RichText} from '#/components/RichText'"
        new_import = """import {RichText} from '#/components/RichText'
import {ReplyOverlay} from '#/components/ReplyOverlay'
import {useReplyMediaQuery} from '#/state/queries/reply-media'"""
        
        if import_marker not in content:
            print("Error: Could not find import marker in PostFeedItem.tsx")
            return False

        content = content.replace(import_marker, new_import)
    else:
        # Just add the query import if ReplyOverlay is already imported
        if 'useReplyMediaQuery' not in content:
            import_marker = "import {ReplyOverlay} from '#/components/ReplyOverlay'"
            new_import = """import {ReplyOverlay} from '#/components/ReplyOverlay'
import {useReplyMediaQuery} from '#/state/queries/reply-media'"""
            content = content.replace(import_marker, new_import)

    # Add query hook usage inside FeedItemInner component
    # Find the component and add the query call
    hook_marker = "const onOpenAuthor = useCallback"
    hook_addition = """const {data: replyMedia = []} = useReplyMediaQuery(post.uri)

  const onOpenAuthor = useCallback"""
    
    if 'useReplyMediaQuery(post.uri)' not in content:
        content = content.replace(hook_marker, hook_addition)

    # Find PostContent and add overlay after it
    # Handle both the original and potentially modified versions
    
    # Check for the View wrapper that our previous script added
    if "style={{position: 'relative'}}" in content:
        # Need to enable the ReplyOverlay that was commented out
        old_overlay = '{/* <ReplyOverlay replies={[]} /> */}'
        new_overlay = '<ReplyOverlay replies={replyMedia} />'
        content = content.replace(old_overlay, new_overlay)
    else:
        # Original structure - wrap PostContent
        old_code = '''<PostContent
            moderation={moderation}
            richText={richText}
            postEmbed={post.embed}
            postAuthor={post.author}
            onOpenEmbed={onOpenEmbed}
            post={post}
            threadgateRecord={threadgateRecord}
          />'''

        new_code = '''<View style={{position: 'relative'}}>
            <PostContent
              moderation={moderation}
              richText={richText}
              postEmbed={post.embed}
              postAuthor={post.author}
              onOpenEmbed={onOpenEmbed}
              post={post}
              threadgateRecord={threadgateRecord}
            />
            <ReplyOverlay replies={replyMedia} />
          </View>'''

        if old_code in content:
            content = content.replace(old_code, new_code)

    with open(POST_FEED_ITEM_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Successfully modified {POST_FEED_ITEM_FILE}")
    return True


def main():
    print("Adding Reply Overlay UI to posts...")
    print("=" * 60)

    if not check_files_exist():
        print("Please ensure all required files exist first.")
        return

    success = modify_post_feed_item()

    print("=" * 60)
    if success:
        print("✅ Reply Overlay enabled!")
        print("")
        print("Features:")
        print("  - Reply media shows as thumbnails in bottom-right")
        print("  - Max 9 thumbnails")
        print("  - 1-3 replies: vertical stack")
        print("  - 4+ replies: grid layout")
        print("  - Clicking thumbnail goes to that reply")
        print("")
        print("Rebuild the app to see changes.")
    else:
        print("⚠️  Modification failed. Check error messages above.")


if __name__ == "__main__":
    main()
