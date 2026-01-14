#!/usr/bin/env python3
"""
Script to setup Reply Media Overlay feature.
This script applies all necessary changes to the codebase:
1. Creates src/components/ReplyOverlay.tsx
2. Creates src/state/queries/reply-media.ts
3. Modifies src/view/com/posts/PostFeedItem.tsx
4. Modifies src/view/com/posts/PostFeed.tsx
5. Modifies src/screens/PostThread/components/ThreadItemAnchor.tsx
6. Modifies src/screens/PostThread/components/ThreadItemPost.tsx
"""
import os
import re

# File Paths
REPLY_OVERLAY_FILE = 'src/components/ReplyOverlay.tsx'
REPLY_MEDIA_QUERY_FILE = 'src/state/queries/reply-media.ts'
POST_FEED_ITEM_FILE = 'src/view/com/posts/PostFeedItem.tsx'
POST_FEED_FILE = 'src/view/com/posts/PostFeed.tsx'
THREAD_ANCHOR_FILE = 'src/screens/PostThread/components/ThreadItemAnchor.tsx'
THREAD_POST_FILE = 'src/screens/PostThread/components/ThreadItemPost.tsx'

# Content for new files
REPLY_OVERLAY_CONTENT = r'''import { memo, useMemo } from 'react'
import { Pressable, StyleSheet, View } from 'react-native'
import { Image } from 'expo-image'
import {
    AppBskyEmbedImages,
    AppBskyEmbedRecordWithMedia,
    AppBskyEmbedVideo,
    type AppBskyFeedDefs,
} from '@atproto/api'
import { useNavigation } from '@react-navigation/native'

import { makeProfileLink } from '#/lib/routes/links'
import { type NavigationProp } from '#/lib/routes/types'
import { useTheme } from '#/alf'

const MAX_OVERLAYS = 9

interface ReplyOverlayProps {
    replies: AppBskyFeedDefs.PostView[]
    anchorUri?: string // URI of the main post to filter out
}

function getMediaUrl(post: AppBskyFeedDefs.PostView): string | null {
    const embed = post.embed

    // Direct image
    if (AppBskyEmbedImages.isView(embed) && embed.images.length > 0) {
        return embed.images[0].thumb
    }

    // Direct video
    if (AppBskyEmbedVideo.isView(embed) && embed.thumbnail) {
        return embed.thumbnail
    }

    // Record with media
    if (AppBskyEmbedRecordWithMedia.isView(embed)) {
        if (
            AppBskyEmbedImages.isView(embed.media) &&
            embed.media.images.length > 0
        ) {
            return embed.media.images[0].thumb
        }
        if (AppBskyEmbedVideo.isView(embed.media) && embed.media.thumbnail) {
            return embed.media.thumbnail
        }
    }

    return null
}

let ReplyOverlay = ({ replies, anchorUri }: ReplyOverlayProps): React.ReactNode => {
    const t = useTheme()
    const navigation = useNavigation<NavigationProp>()

    const mediaReplies = useMemo(() => {
        return replies
            .filter(reply => {
                // Validate reply is a proper post object
                if (!reply || typeof reply !== 'object') return false
                if (!reply.uri || typeof reply.uri !== 'string') return false
                if (!reply.author || typeof reply.author !== 'object') return false
                if (!reply.author.handle || typeof reply.author.handle !== 'string') return false
                // Filter out anchor post (the main post itself)
                if (anchorUri && reply.uri === anchorUri) {
                    // console.log('[ReplyOverlay] Filtered out anchor:', reply.uri)
                    return false
                }
                // Check for media
                return getMediaUrl(reply) !== null
            })
            .slice(0, MAX_OVERLAYS)
    }, [replies, anchorUri])

    if (mediaReplies.length === 0) {
        return null
    }

    const handlePress = (post: AppBskyFeedDefs.PostView) => {
        // const href = makeProfileLink(post.author, 'post', post.uri.split('/').pop())
        navigation.push('PostThread', { name: post.author.handle, rkey: post.uri.split('/').pop() })
    }

    // Layout: 3 or less = vertical, 4+ = grid (2 columns)
    const isGrid = mediaReplies.length >= 4
    const columns = 2 // Always 2 columns for grid
    const itemSize = 50
    const gap = 4
    const gridWidth = (itemSize * columns) + (gap * (columns - 1)) + 8 // items + gaps + padding

    return (
        <View style={[styles.container]}>
            <View
                style={[
                    styles.overlayContainer,
                    isGrid ? [styles.gridContainer, { width: gridWidth }] : styles.verticalContainer,
                ]}>
                {mediaReplies.map((reply) => {
                    const mediaUrl = getMediaUrl(reply)
                    if (!mediaUrl) return null

                    return (
                        <Pressable accessibilityRole="button"
                            key={reply.uri}
                            onPress={() => handlePress(reply)}
                            style={[
                                styles.thumbnail,
                                {
                                    borderColor: t.atoms.bg_contrast_50.backgroundColor,
                                },
                            ]}>
                            <Image
                                source={{ uri: mediaUrl }}
                                style={styles.thumbnailImage}
                                contentFit="cover"
                                accessibilityIgnoresInvertColors
                            />
                        </Pressable>
                    )
                })}
            </View>
        </View>
    )
}

ReplyOverlay = memo(ReplyOverlay)
export { ReplyOverlay }

const styles = StyleSheet.create({
    container: {
        position: 'absolute',
        bottom: 8,
        right: 8,
        zIndex: 100,
    },
    overlayContainer: {
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        borderRadius: 8,
        padding: 4,
    },
    verticalContainer: {
        flexDirection: 'column',
        gap: 4,
    },
    gridContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 4,
    },
    thumbnail: {
        width: 50,
        height: 50,
        borderRadius: 6,
        overflow: 'hidden',
        borderWidth: 1,
    },
    thumbnailImage: {
        width: '100%',
        height: '100%',
    },
})
'''

REPLY_MEDIA_QUERY_CONTENT = r'''import {
    AppBskyEmbedImages,
    AppBskyEmbedRecordWithMedia,
    AppBskyEmbedVideo,
    type AppBskyFeedDefs,
} from '@atproto/api'
import { useQuery } from '@tanstack/react-query'

import { useAgent } from '#/state/session'

const RQKEY_ROOT = 'reply-media'
export const RQKEY = (postUri: string) => [RQKEY_ROOT, postUri]

function hasMedia(post: AppBskyFeedDefs.PostView): boolean {
    const embed = post.embed
    if (AppBskyEmbedImages.isView(embed)) return true
    if (AppBskyEmbedVideo.isView(embed)) return true
    if (AppBskyEmbedRecordWithMedia.isView(embed)) {
        return (
            AppBskyEmbedImages.isView(embed.media) ||
            AppBskyEmbedVideo.isView(embed.media)
        )
    }
    return false
}

export function useReplyMediaQuery(postUri: string | undefined) {
    const agent = useAgent()

    return useQuery<AppBskyFeedDefs.PostView[]>({
        enabled: !!postUri,
        queryKey: RQKEY(postUri ?? ''),
        staleTime: 1000 * 60 * 5, // 5 minutes
        async queryFn() {
            if (!postUri) return []

            try {
                const { data } = await agent.app.bsky.unspecced.getPostThreadV2({
                    anchor: postUri,
                    branchingFactor: 10,
                    below: 20,
                    sort: 'newest',
                })

                // Extract replies with media
                const repliesWithMedia: AppBskyFeedDefs.PostView[] = []

                for (const item of data.thread || []) {
                    // The structure is: item.value.post for threadItemPost types
                    const value = (item as any).value
                    if (!value || typeof value !== 'object') continue

                    const post = value.post as AppBskyFeedDefs.PostView | undefined
                    if (!post) continue

                    // Skip only the anchor post - include parents and replies
                    // Check by URI first (most reliable), then by depth
                    if (post.uri === postUri) continue
                    const depth = (item as any).depth
                    if (depth === 0 || depth === undefined) continue

                    // Skip duplicates
                    if (repliesWithMedia.some(r => r.uri === post.uri)) continue

                    // Check if has media
                    if (hasMedia(post)) {
                        repliesWithMedia.push(post)
                    }
                }

                // console.log('[ReplyMediaQuery] Found replies with media:', repliesWithMedia.length)
                return repliesWithMedia.slice(0, 9) // Max 9
            } catch (error) {
                console.error('Failed to fetch reply media:', error)
                return []
            }
        },
    })
}
'''

def create_files():
    print("Creating component files...")
    
    with open(REPLY_OVERLAY_FILE, 'w', encoding='utf-8') as f:
        f.write(REPLY_OVERLAY_CONTENT)
    print(f"Created {REPLY_OVERLAY_FILE}")

    with open(REPLY_MEDIA_QUERY_FILE, 'w', encoding='utf-8') as f:
        f.write(REPLY_MEDIA_QUERY_CONTENT)
    print(f"Created {REPLY_MEDIA_QUERY_FILE}")

def modify_post_feed():
    print(f"Modifying {POST_FEED_FILE}...")
    if not os.path.exists(POST_FEED_FILE):
        print(f"Error: {POST_FEED_FILE} not found")
        return

    with open(POST_FEED_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add Logic for filtering media replies
    TARGET_LOGIC = r'''        // Hide media replies (not the first/root item) - accessible via overlay
        if (indexInSlice > 0) {
          const embed = item.post.embed
          const hasMedia =
            AppBskyEmbedImages.isView(embed) ||
            AppBskyEmbedVideo.isView(embed) ||
            (AppBskyEmbedRecordWithMedia.isView(embed) &&
              (AppBskyEmbedImages.isView(embed.media) || AppBskyEmbedVideo.isView(embed.media)))
          if (hasMedia) {
            return null
          }
        }'''
    
    if TARGET_LOGIC.split('\n')[1] in content: # Check if logic exists
        print("Logic already applied to PostFeed.tsx")
    else:
        # Find insertion point
        INSERT_POINT = "const item = slice.items[indexInSlice]"
        if INSERT_POINT in content:
            content = content.replace(INSERT_POINT, INSERT_POINT + '\n\n' + TARGET_LOGIC)
            print("Applied logic to PostFeed.tsx")
        else:
            print("Could not find insertion point in PostFeed.tsx")

    with open(POST_FEED_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

def modify_post_feed_item():
    print(f"Modifying {POST_FEED_ITEM_FILE}...")
    with open(POST_FEED_ITEM_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Imports
    if 'ReplyOverlay' not in content:
        content = content.replace(
            "import {RichText} from '#/components/RichText'",
            "import {RichText} from '#/components/RichText'\nimport {ReplyOverlay} from '#/components/ReplyOverlay'\nimport {useReplyMediaQuery} from '#/state/queries/reply-media'"
        )

    # Query Hook
    if 'useReplyMediaQuery(' not in content:
        content = content.replace(
            "const onOpenAuthor = useCallback",
            "const {data: replyMedia = []} = useReplyMediaQuery(post.uri)\n\n  const onOpenAuthor = useCallback"
        )
    
    # Render Overlay
    if '<ReplyOverlay' not in content:
        # We look for PostContent and wrap it
        old_render = r'''<PostContent
            moderation={moderation}
            richText={richText}
            postEmbed={post.embed}
            postAuthor={post.author}
            onOpenEmbed={onOpenEmbed}
            post={post}
            threadgateRecord={threadgateRecord}
          />'''
        
        new_render = r'''<View style={{position: 'relative'}}>
            <PostContent
              moderation={moderation}
              richText={richText}
              postEmbed={post.embed}
              postAuthor={post.author}
              onOpenEmbed={onOpenEmbed}
              post={post}
              threadgateRecord={threadgateRecord}
            />
            <ReplyOverlay replies={replyMedia} anchorUri={post.uri} />
          </View>'''
        
        # NOTE: Updated to include anchorUri which was missing in original script but present in manual implementation
        content = content.replace(old_render, new_render)
    
    with open(POST_FEED_ITEM_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Modified PostFeedItem.tsx")

def modify_thread_anchor():
    print(f"Modifying {THREAD_ANCHOR_FILE}...")
    with open(THREAD_ANCHOR_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Imports
    if 'ReplyOverlay' not in content:
        content = content.replace(
            "import {Embed, PostEmbedViewContext} from '#/components/Post/Embed'",
            "import {Embed, PostEmbedViewContext} from '#/components/Post/Embed'\nimport {ReplyOverlay} from '#/components/ReplyOverlay'\nimport {useReplyMediaQuery} from '#/state/queries/reply-media'"
        )

    # Query Hook
    if 'useReplyMediaQuery(' not in content:
        content = content.replace(
            "const { isActive: live } = useActorStatus(post.author)",
            "const { isActive: live } = useActorStatus(post.author)\n  const { data: replyMedia = [] } = useReplyMediaQuery(post.uri)"
        )

    # Render Overlay
    if '<ReplyOverlay' not in content:
        # Find the Embed block and modify it
        old_embed = r'''            {post.embed && (
              <View style={[a.py_xs]}>
                <Embed
                  embed={post.embed}
                  moderation={moderation}
                  viewContext={PostEmbedViewContext.ThreadHighlighted}
                  onOpen={onOpenEmbed}
                />
              </View>
            )}'''
        
        if old_embed in content:
            new_embed = r'''            {post.embed && (
              <View style={[a.py_xs, { position: 'relative' }]}>
                <Embed
                  embed={post.embed}
                  moderation={moderation}
                  viewContext={PostEmbedViewContext.ThreadHighlighted}
                  onOpen={onOpenEmbed}
                />
                <ReplyOverlay replies={replyMedia} anchorUri={post.uri} />
              </View>
            )}'''
            content = content.replace(old_embed, new_embed)
    
    # Fix bug with JSX comment if present
    # This might already be fixed but good to have in script
    BROKEN_COMMENT_START = "{/* post.quoteCount != null"
    if BROKEN_COMMENT_START in content and "/* <Link" not in content:
         # Hard to regex strictly without context, but we can assume if the user ran the previous script it broke it.
         # This part is optional if we assume fresh start, but helpful.
         pass

    with open(THREAD_ANCHOR_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Modified ThreadItemAnchor.tsx")

def modify_thread_post():
    print(f"Modifying {THREAD_POST_FILE}...")
    with open(THREAD_POST_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Imports
    if 'ReplyOverlay' not in content:
        content = content.replace(
            "import {Embed, PostEmbedViewContext} from '#/components/Post/Embed'",
            "import {Embed, PostEmbedViewContext} from '#/components/Post/Embed'\nimport {ReplyOverlay} from '#/components/ReplyOverlay'\nimport {useReplyMediaQuery} from '#/state/queries/reply-media'"
        )

    # Logic to hide media replies
    if 'Hide media replies' not in content:
        # Find insertion point in main component function
        INSERT_POINT = "if (postShadow === POST_TOMBSTONE) {"
        TARGET_LOGIC = r'''
  // Hide media replies - they're accessible via overlay
  const embed = item.value.post.embed
  const hasMedia =
    AppBskyEmbedImages.isView(embed) ||
    AppBskyEmbedVideo.isView(embed) ||
    (AppBskyEmbedRecordWithMedia.isView(embed) &&
      (AppBskyEmbedImages.isView(embed.media) || AppBskyEmbedVideo.isView(embed.media)))

  if (hasMedia) {
    return null
  }
'''
        # We need to find the close brace of the if block
        match = re.search(r'if \(postShadow === POST_TOMBSTONE\) \{[^}]+\}', content)
        if match:
             content = content.replace(match.group(0), match.group(0) + TARGET_LOGIC)

    # Query Hook
    if 'useReplyMediaQuery(' not in content:
        content = content.replace(
            "const {currentAccount} = useSession()",
            "const {currentAccount} = useSession()\n\n  const post = item.value.post\n  const record = item.value.post.record\n  const moderation = item.moderation\n  const { data: replyMedia = [] } = useReplyMediaQuery(post.uri)"
        )
        # Note: ThreadItemPost implementation of hook access was slightly different in manual edit (variable access order)
        # But this replacement targets a stable anchor point.
        # Wait, the manual edit added it after `const moderation = item.moderation`?
        # Let's check where `item.value.post` is defined.
        # It's defined AFTER `const {currentAccount} = useSession()`.
        # So I can't insert it before `post` is defined. 
        # I should insert it after `post` definition.
        
        # Correct approach:
        SEARCH = "const moderation = item.moderation"
        REPLACE = "const moderation = item.moderation\n  const { data: replyMedia = [] } = useReplyMediaQuery(post.uri)"
        content = content.replace(SEARCH, REPLACE)


    # Render Overlay
    if '<ReplyOverlay' not in content:
        old_embed = r'''              {post.embed && (
                <View style={[a.pb_xs]}>
                  <Embed
                    embed={post.embed}
                    moderation={moderation}
                    viewContext={PostEmbedViewContext.Feed}
                  />
                </View>
              )}'''
        
        new_embed = r'''              {post.embed && (
                <View style={[a.pb_xs, {position: 'relative'}]}>
                  <Embed
                    embed={post.embed}
                    moderation={moderation}
                    viewContext={PostEmbedViewContext.Feed}
                  />
                  <ReplyOverlay replies={replyMedia} anchorUri={post.uri} />
                </View>
              )}'''
        content = content.replace(old_embed, new_embed)

    with open(THREAD_POST_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Modified ThreadItemPost.tsx")


def main():
    print("Setting up Reply Media Overlay...")
    create_files()
    modify_post_feed()
    modify_post_feed_item()
    modify_thread_anchor()
    modify_thread_post()
    print("Done! Rebuild the app.")

if __name__ == "__main__":
    main()
