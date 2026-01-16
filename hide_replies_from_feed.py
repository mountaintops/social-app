#!/usr/bin/env python3
"""
Hide Replies from Feeds Script (v3)

This script modifies the feed display to limit how many posts in a reply chain 
can be shown in a feed to just ONE (the main/root post).

The full reply chain will still be visible when a user clicks on the post 
to view the thread.

What this script does:
1. Modifies PostFeed.tsx to only show a single item per slice
2. Handles BOTH regular slices AND incomplete thread slices
3. Forces FeedTuner.removeReplies for all feed types (optional)
4. The user can still click on any post to see the full thread
"""

import os
import re


def modify_post_feed():
    """
    Modify PostFeed.tsx to only show one post per slice in feeds,
    hiding all reply chain posts from the feed view.
    """
    file_path = 'src/view/com/posts/PostFeed.tsx'
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Store original content for comparison
    original_content = content
    
    # =========================================================================
    # MODIFICATION 1: Handle the "incomplete thread" case (3+ items)
    # Original code shows: first post + "view full thread" + 2nd-to-last + last
    # We want to show: ONLY the last post (the actual new content)
    # =========================================================================
    
    # Pattern for incomplete thread handling
    incomplete_thread_old = '''} else if (slice.isIncompleteThread && slice.items.length >= 3) {
                const beforeLast = slice.items.length - 2
                const last = slice.items.length - 1
                arr.push(
                  sliceItem({
                    type: 'sliceItem',
                    key: slice.items[0]._reactKey,
                    slice: slice,
                    indexInSlice: 0,
                    showReplyTo: false,
                  }),
                )
                arr.push({
                  type: 'sliceViewFullThread',
                  key: slice._reactKey + '-viewFullThread',
                  uri: slice.items[0].uri,
                })
                arr.push(
                  sliceItem({
                    type: 'sliceItem',
                    key: slice.items[beforeLast]._reactKey,
                    slice: slice,
                    indexInSlice: beforeLast,
                    showReplyTo:
                      slice.items[beforeLast].parentAuthor?.did !==
                      slice.items[beforeLast].post.author.did,
                  }),
                )
                arr.push(
                  sliceItem({
                    type: 'sliceItem',
                    key: slice.items[last]._reactKey,
                    slice: slice,
                    indexInSlice: last,
                    showReplyTo: false,
                  }),
                )
              }'''
    
    incomplete_thread_new = '''} else if (slice.isIncompleteThread && slice.items.length >= 3) {
                // MODIFIED: Only show the last item in incomplete threads
                // Full thread chain visible when user clicks on the post
                const last = slice.items.length - 1
                arr.push(
                  sliceItem({
                    type: 'sliceItem',
                    key: slice.items[last]._reactKey,
                    slice: slice,
                    indexInSlice: last,
                    showReplyTo: false,
                  }),
                )
              }'''
    
    if incomplete_thread_old in content:
        content = content.replace(incomplete_thread_old, incomplete_thread_new)
        print("  ✓ Modified incomplete thread handling")
    else:
        # Check if already modified
        if '// MODIFIED: Only show the last item in incomplete threads' in content:
            print("  ✓ Incomplete thread handling already modified")
        else:
            print("  ⚠ Incomplete thread code not found")
    
    # =========================================================================
    # MODIFICATION 2: Handle slices with 2 items (parent + reply)
    # Also handles slices with 1 item (just show it)
    # =========================================================================
    
    # Check if the else block has already been modified
    if '// MODIFIED: Only show the root post in feed, hide replies' in content:
        print("  ✓ Regular slice handling already modified")
    else:
        # Pattern for regular slice handling (not incomplete thread)
        regular_slice_old = '''} else {
                for (let i = 0; i < slice.items.length; i++) {
                  arr.push(
                    sliceItem({
                      type: 'sliceItem',
                      key: slice.items[i]._reactKey,
                      slice: slice,
                      indexInSlice: i,
                      showReplyTo: i === 0,
                    }),
                  )
                }
              }'''
        
        regular_slice_new = '''} else {
                // MODIFIED: Only show the root post in feed, hide replies
                // Full reply chain is visible when user clicks on the post
                arr.push(
                  sliceItem({
                    type: 'sliceItem',
                    key: slice.items[0]._reactKey,
                    slice: slice,
                    indexInSlice: 0,
                    showReplyTo: false,
                  }),
                )
              }'''
        
        if regular_slice_old in content:
            content = content.replace(regular_slice_old, regular_slice_new)
            print("  ✓ Modified regular slice handling")
        else:
            print("  ⚠ Regular slice code not found")
    
    # =========================================================================
    # Write the modified content
    # =========================================================================
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  → Updated {file_path}")
        return True
    else:
        print(f"  → No changes needed to {file_path}")
        return False


def modify_feed_tuners():
    """
    Modify feed-tuners.tsx to always include FeedTuner.removeReplies
    for all feed types, ensuring replies are not shown.
    """
    file_path = 'src/state/preferences/feed-tuners.tsx'
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # =========================================================================
    # Add FeedTuner.removeReplies for feedgen feeds
    # =========================================================================
    
    feedgen_old = '''if (feedDesc.startsWith('feedgen')) {
      return [
        FeedTuner.preferredLangOnly(langPrefs.contentLanguages),
        FeedTuner.removeMutedThreads,
      ]
    }'''
    
    feedgen_new = '''if (feedDesc.startsWith('feedgen')) {
      // MODIFIED: Always remove replies from feedgen feeds
      return [
        FeedTuner.preferredLangOnly(langPrefs.contentLanguages),
        FeedTuner.removeMutedThreads,
        FeedTuner.removeReplies, // Hide replies
      ]
    }'''
    
    if feedgen_old in content:
        content = content.replace(feedgen_old, feedgen_new)
        print("  ✓ Added removeReplies to feedgen feeds")
    elif '// MODIFIED: Always remove replies from feedgen feeds' in content:
        print("  ✓ Feedgen modification already applied")
    else:
        print("  ⚠ Feedgen code not found")
    
    # =========================================================================
    # Make sure removeReplies is always added regardless of preference
    # =========================================================================
    
    # Replace the conditional hideReplies check with always adding removeReplies
    hide_replies_old = '''if (preferences?.feedViewPrefs.hideReplies) {
        feedTuners.push(FeedTuner.removeReplies)
      } else {
        feedTuners.push(
          FeedTuner.followedRepliesOnly({
            userDid: currentAccount?.did || '',
          }),
        )
      }'''
    
    hide_replies_new = '''// MODIFIED: Always hide replies from feed
      feedTuners.push(FeedTuner.removeReplies)'''
    
    if hide_replies_old in content:
        content = content.replace(hide_replies_old, hide_replies_new)
        print("  ✓ Modified to always remove replies from following/list feeds")
    elif '// MODIFIED: Always hide replies from feed' in content:
        print("  ✓ Always-hide-replies modification already applied")
    else:
        print("  ⚠ hideReplies conditional code not found")
    
    # =========================================================================
    # Write the modified content
    # =========================================================================
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  → Updated {file_path}")
        return True
    else:
        print(f"  → No changes needed to {file_path}")
        return False


def hide_replies_from_feed():
    """Main function to apply all modifications."""
    print("Modifying PostFeed.tsx...")
    post_feed_changed = modify_post_feed()
    
    print("\nModifying feed-tuners.tsx...")
    feed_tuners_changed = modify_feed_tuners()
    
    if post_feed_changed or feed_tuners_changed:
        print("\n" + "=" * 50)
        print("✅ Changes applied successfully!")
        print("=" * 50)
        print("\nWhat was changed:")
        print("  1. PostFeed.tsx: Single post per feed item")
        print("  2. feed-tuners.tsx: FeedTuner.removeReplies added")
        print("\nTo test: Rebuild and run the app")
        print("To revert: python3 hide_replies_from_feed.py --revert")
        return True
    else:
        print("\n✅ All changes already applied!")
        return True


def revert_changes():
    """
    Revert the changes made by hide_replies_from_feed().
    """
    print("Reverting PostFeed.tsx...")
    revert_post_feed()
    
    print("\nReverting feed-tuners.tsx...")
    revert_feed_tuners()
    
    print("\n✅ Reverted successfully!")


def revert_post_feed():
    """Revert PostFeed.tsx changes."""
    file_path = 'src/view/com/posts/PostFeed.tsx'
    
    if not os.path.exists(file_path):
        print(f"  Error: {file_path} not found.")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Revert incomplete thread modification
    incomplete_thread_modified = '''} else if (slice.isIncompleteThread && slice.items.length >= 3) {
                // MODIFIED: Only show the last item in incomplete threads
                // Full thread chain visible when user clicks on the post
                const last = slice.items.length - 1
                arr.push(
                  sliceItem({
                    type: 'sliceItem',
                    key: slice.items[last]._reactKey,
                    slice: slice,
                    indexInSlice: last,
                    showReplyTo: false,
                  }),
                )
              }'''
    
    incomplete_thread_original = '''} else if (slice.isIncompleteThread && slice.items.length >= 3) {
                const beforeLast = slice.items.length - 2
                const last = slice.items.length - 1
                arr.push(
                  sliceItem({
                    type: 'sliceItem',
                    key: slice.items[0]._reactKey,
                    slice: slice,
                    indexInSlice: 0,
                    showReplyTo: false,
                  }),
                )
                arr.push({
                  type: 'sliceViewFullThread',
                  key: slice._reactKey + '-viewFullThread',
                  uri: slice.items[0].uri,
                })
                arr.push(
                  sliceItem({
                    type: 'sliceItem',
                    key: slice.items[beforeLast]._reactKey,
                    slice: slice,
                    indexInSlice: beforeLast,
                    showReplyTo:
                      slice.items[beforeLast].parentAuthor?.did !==
                      slice.items[beforeLast].post.author.did,
                  }),
                )
                arr.push(
                  sliceItem({
                    type: 'sliceItem',
                    key: slice.items[last]._reactKey,
                    slice: slice,
                    indexInSlice: last,
                    showReplyTo: false,
                  }),
                )
              }'''
    
    if incomplete_thread_modified in content:
        content = content.replace(incomplete_thread_modified, incomplete_thread_original)
        print("  ✓ Reverted incomplete thread handling")
    
    # Revert regular slice modification
    regular_slice_modified = '''} else {
                // MODIFIED: Only show the root post in feed, hide replies
                // Full reply chain is visible when user clicks on the post
                arr.push(
                  sliceItem({
                    type: 'sliceItem',
                    key: slice.items[0]._reactKey,
                    slice: slice,
                    indexInSlice: 0,
                    showReplyTo: false,
                  }),
                )
              }'''
    
    regular_slice_original = '''} else {
                for (let i = 0; i < slice.items.length; i++) {
                  arr.push(
                    sliceItem({
                      type: 'sliceItem',
                      key: slice.items[i]._reactKey,
                      slice: slice,
                      indexInSlice: i,
                      showReplyTo: i === 0,
                    }),
                  )
                }
              }'''
    
    if regular_slice_modified in content:
        content = content.replace(regular_slice_modified, regular_slice_original)
        print("  ✓ Reverted regular slice handling")
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False


def revert_feed_tuners():
    """Revert feed-tuners.tsx changes."""
    file_path = 'src/state/preferences/feed-tuners.tsx'
    
    if not os.path.exists(file_path):
        print(f"  Error: {file_path} not found.")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Revert feedgen modification
    feedgen_modified = '''if (feedDesc.startsWith('feedgen')) {
      // MODIFIED: Always remove replies from feedgen feeds
      return [
        FeedTuner.preferredLangOnly(langPrefs.contentLanguages),
        FeedTuner.removeMutedThreads,
        FeedTuner.removeReplies, // Hide replies
      ]
    }'''
    
    feedgen_original = '''if (feedDesc.startsWith('feedgen')) {
      return [
        FeedTuner.preferredLangOnly(langPrefs.contentLanguages),
        FeedTuner.removeMutedThreads,
      ]
    }'''
    
    if feedgen_modified in content:
        content = content.replace(feedgen_modified, feedgen_original)
        print("  ✓ Reverted feedgen modification")
    
    # Revert always-remove-replies modification
    hide_replies_modified = '''// MODIFIED: Always hide replies from feed
      feedTuners.push(FeedTuner.removeReplies)'''
    
    hide_replies_original = '''if (preferences?.feedViewPrefs.hideReplies) {
        feedTuners.push(FeedTuner.removeReplies)
      } else {
        feedTuners.push(
          FeedTuner.followedRepliesOnly({
            userDid: currentAccount?.did || '',
          }),
        )
      }'''
    
    if hide_replies_modified in content:
        content = content.replace(hide_replies_modified, hide_replies_original)
        print("  ✓ Reverted always-hide-replies modification")
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--revert':
        print("Reverting all changes...\n")
        revert_changes()
    else:
        print("Hiding replies from feeds (v3)...\n")
        hide_replies_from_feed()
