#!/usr/bin/env python3
"""
Script to add inline text post layout to the Bluesky social app.
Text-only posts (no embeds) will display in a compact inline format:
- Avatar on the left
- Handle + text inline
- Action icons (reply, like, menu) on the right
"""
import os

# File paths
COMPONENTS_POST_DIR = 'src/components/Post'
INLINE_TEXT_POST_FILE = os.path.join(COMPONENTS_POST_DIR, 'InlineTextPost.tsx')
INLINE_POST_CONTROLS_FILE = os.path.join(COMPONENTS_POST_DIR, 'InlinePostControls.tsx')
POST_FEED_ITEM_FILE = 'src/view/com/posts/PostFeedItem.tsx'
THREAD_ITEM_POST_FILE = 'src/screens/PostThread/components/ThreadItemPost.tsx'
POST_FILE = 'src/view/com/post/Post.tsx'

# Component source code
INLINE_TEXT_POST_CODE = '''import {memo, useCallback, useState} from 'react'
import {View} from 'react-native'
import {
  type AppBskyFeedDefs,
  type AppBskyFeedPost,
  AtUri,
  type ModerationDecision,
  type RichText as RichTextAPI,
} from '@atproto/api'
import {useQueryClient} from '@tanstack/react-query'

import {makeProfileLink} from '#/lib/routes/links'
import {sanitizeHandle} from '#/lib/strings/handles'
import {type Shadow} from '#/state/cache/types'
import {precacheProfile} from '#/state/queries/profile'
import {atoms as a, useTheme} from '#/alf'
import {RichText} from '#/components/RichText'
import {SubtleHover} from '#/components/SubtleHover'
import {Text} from '#/components/Typography'
import {Link} from '#/view/com/util/Link'
import {PreviewableUserAvatar} from '#/view/com/util/UserAvatar'
import {InlinePostControls} from './InlinePostControls'

const AVATAR_SIZE = 24

export interface InlineTextPostProps {
  post: Shadow<AppBskyFeedDefs.PostView>
  record: AppBskyFeedPost.Record
  richText: RichTextAPI
  moderation: ModerationDecision
  onPressReply?: () => void
  onBeforePress?: () => void
  hideTopBorder?: boolean
}

let InlineTextPost = ({
  post,
  record,
  richText,
  moderation,
  onPressReply,
  onBeforePress: outerOnBeforePress,
  hideTopBorder,
}: InlineTextPostProps): React.ReactNode => {
  const t = useTheme()
  const queryClient = useQueryClient()
  const [hover, setHover] = useState(false)

  const itemUrip = new AtUri(post.uri)
  const itemHref = makeProfileLink(post.author, 'post', itemUrip.rkey)
  const handle = sanitizeHandle(post.author.handle, '@')

  const onBeforePress = useCallback(() => {
    precacheProfile(queryClient, post.author)
    outerOnBeforePress?.()
  }, [queryClient, post.author, outerOnBeforePress])

  return (
    <Link
      href={itemHref}
      style={[
        a.py_xs,
        a.px_sm,
        !hideTopBorder && {
          borderTopWidth: 1,
          borderTopColor: t.atoms.border_contrast_low.borderColor,
        },
      ]}
      onBeforePress={onBeforePress}
      onPointerEnter={() => setHover(true)}
      onPointerLeave={() => setHover(false)}>
      <SubtleHover hover={hover} />
      <View style={[a.flex_row, a.align_center, a.gap_sm]}>
        {/* Avatar */}
        <View>
          <PreviewableUserAvatar
            size={AVATAR_SIZE}
            profile={post.author}
            moderation={moderation.ui('avatar')}
            type={post.author.associated?.labeler ? 'labeler' : 'user'}
          />
        </View>

        {/* Handle + Text */}
        <View style={[a.flex_1, a.flex_row, a.flex_wrap, a.align_center]}>
          <Text
            style={[
              a.text_sm,
              t.atoms.text_contrast_medium,
              a.mr_xs,
              {flexShrink: 0},
            ]}>
            {handle}
          </Text>
          <View style={[a.flex_1, a.flex_shrink]}>
            <RichText
              enableTags
              testID="inlinePostText"
              value={richText}
              style={[a.text_sm, a.flex_1]}
              authorHandle={post.author.handle}
              shouldProxyLinks={true}
            />
          </View>
        </View>

        {/* Action Icons */}
        <InlinePostControls
          post={post}
          record={record}
          richText={richText}
          onPressReply={onPressReply}
        />
      </View>
    </Link>
  )
}

InlineTextPost = memo(InlineTextPost)
export {InlineTextPost}
'''

INLINE_POST_CONTROLS_CODE = '''import {memo, useState} from 'react'
import {View} from 'react-native'
import {
  type AppBskyFeedDefs,
  type AppBskyFeedPost,
  type RichText as RichTextAPI,
} from '@atproto/api'
import {msg} from '@lingui/macro'
import {useLingui} from '@lingui/react'

import {AnimatedLikeIcon} from '#/lib/custom-animations/LikeIcon'
import {useHaptics} from '#/lib/haptics'
import {type Shadow} from '#/state/cache/types'
import {useFeedFeedbackContext} from '#/state/feed-feedback'
import {usePostLikeMutationQueue} from '#/state/queries/post'
import {useRequireAuth} from '#/state/session'
import {
  ProgressGuideAction,
  useProgressGuideControls,
} from '#/state/shell/progress-guide'
import * as Toast from '#/view/com/util/Toast'
import {atoms as a} from '#/alf'
import {Button, ButtonIcon} from '#/components/Button'
import {Reply as Bubble} from '#/components/icons/Reply'
import {PostMenuButton} from '#/components/PostControls/PostMenu'

export interface InlinePostControlsProps {
  post: Shadow<AppBskyFeedDefs.PostView>
  record: AppBskyFeedPost.Record
  richText: RichTextAPI
  onPressReply?: () => void
}

let InlinePostControls = ({
  post,
  record,
  richText,
  onPressReply,
}: InlinePostControlsProps): React.ReactNode => {
  const {_} = useLingui()
  const requireAuth = useRequireAuth()
  const {feedDescriptor} = useFeedFeedbackContext()
  const [queueLike, queueUnlike] = usePostLikeMutationQueue(
    post,
    undefined,
    feedDescriptor,
    'FeedItem',
  )
  const {sendInteraction} = useFeedFeedbackContext()
  const {captureAction} = useProgressGuideControls()
  const playHaptic = useHaptics()
  const [hasLikeIconBeenToggled, setHasLikeIconBeenToggled] = useState(false)

  const isBlocked = Boolean(
    post.author.viewer?.blocking ||
      post.author.viewer?.blockedBy ||
      post.author.viewer?.blockingByList,
  )

  const onPressToggleLike = async () => {
    if (isBlocked) {
      Toast.show(
        _(msg`Cannot interact with a blocked user`),
        'exclamation-circle',
      )
      return
    }

    try {
      setHasLikeIconBeenToggled(true)
      if (!post.viewer?.like) {
        playHaptic('Light')
        sendInteraction({
          item: post.uri,
          event: 'app.bsky.feed.defs#interactionLike',
        })
        captureAction(ProgressGuideAction.Like)
        await queueLike()
      } else {
        await queueUnlike()
      }
    } catch (e: any) {
      if (e?.name !== 'AbortError') {
        throw e
      }
    }
  }

  const onReplyPress = () => {
    if (isBlocked) {
      Toast.show(
        _(msg`Cannot interact with a blocked user`),
        'exclamation-circle',
      )
      return
    }
    onPressReply?.()
  }

  return (
    <View style={[a.flex_row, a.align_center, a.gap_xs]}>
      {/* Reply */}
      <Button
        label={_(msg`Reply`)}
        size="tiny"
        variant="ghost"
        color="secondary"
        shape="round"
        onPress={() => requireAuth(onReplyPress)}>
        <ButtonIcon icon={Bubble} size="sm" />
      </Button>

      {/* Like */}
      <Button
        label={post.viewer?.like ? _(msg`Unlike`) : _(msg`Like`)}
        size="tiny"
        variant="ghost"
        color="secondary"
        shape="round"
        onPress={() => requireAuth(() => onPressToggleLike())}>
        <AnimatedLikeIcon
          isLiked={Boolean(post.viewer?.like)}
          big={false}
          hasBeenToggled={hasLikeIconBeenToggled}
        />
      </Button>

      {/* Menu */}
      <PostMenuButton
        testID="inlinePostMenuBtn"
        post={post}
        record={record}
        richText={richText}
        timestamp={post.indexedAt}
        logContext="FeedItem"
      />
    </View>
  )
}

InlinePostControls = memo(InlinePostControls)
export {InlinePostControls}
'''


def create_component_files():
    """Create the InlineTextPost and InlinePostControls component files."""
    os.makedirs(COMPONENTS_POST_DIR, exist_ok=True)
    
    # Create InlineTextPost.tsx
    print(f"Creating {INLINE_TEXT_POST_FILE}...")
    with open(INLINE_TEXT_POST_FILE, 'w', encoding='utf-8') as f:
        f.write(INLINE_TEXT_POST_CODE)
    print(f"  ✓ Created {INLINE_TEXT_POST_FILE}")
    
    # Create InlinePostControls.tsx
    print(f"Creating {INLINE_POST_CONTROLS_FILE}...")
    with open(INLINE_POST_CONTROLS_FILE, 'w', encoding='utf-8') as f:
        f.write(INLINE_POST_CONTROLS_CODE)
    print(f"  ✓ Created {INLINE_POST_CONTROLS_FILE}")
    
    return True


def modify_post_feed_item():
    """Modify PostFeedItem.tsx to use InlineTextPost for text-only posts."""
    if not os.path.exists(POST_FEED_ITEM_FILE):
        print(f"Error: File not found: {POST_FEED_ITEM_FILE}")
        return False
    
    print(f"Modifying {POST_FEED_ITEM_FILE}...")
    with open(POST_FEED_ITEM_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already modified
    if 'InlineTextPost' in content:
        print(f"  {POST_FEED_ITEM_FILE} already modified.")
        return True
    
    # 1. Add import for InlineTextPost
    import_marker = "import * as bsky from '#/types/bsky'"
    if import_marker not in content:
        print(f"  Error: Could not find import marker in {POST_FEED_ITEM_FILE}")
        return False
    
    new_import = import_marker + "\nimport {InlineTextPost} from '#/components/Post/InlineTextPost'"
    content = content.replace(import_marker, new_import)
    
    # 2. Add isTextOnlyPost calculation in PostFeedItem function (BEFORE the if richText check)
    old_tombstone = '''  if (postShadowed === POST_TOMBSTONE) {
    return null
  }
  if (richText && moderation) {'''
    
    new_tombstone = '''  if (postShadowed === POST_TOMBSTONE) {
    return null
  }

  // Determine if this is a text-only post (no embeds, has text)
  const isTextOnlyPost = !post.embed && Boolean(record.text)

  // Use inline layout for text-only posts
  if (isTextOnlyPost && richText && moderation) {
    return (
      <InlineTextPost
        post={postShadowed}
        record={record}
        richText={richText}
        moderation={moderation}
        hideTopBorder={hideTopBorder}
      />
    )
  }

  if (richText && moderation) {'''
    
    if old_tombstone not in content:
        print(f"  Error: Could not find tombstone check in {POST_FEED_ITEM_FILE}")
        return False
    
    content = content.replace(old_tombstone, new_tombstone)
    
    with open(POST_FEED_ITEM_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✓ Modified {POST_FEED_ITEM_FILE}")
    return True


def modify_thread_item_post():
    """Modify ThreadItemPost.tsx to use InlineTextPost for text-only posts."""
    if not os.path.exists(THREAD_ITEM_POST_FILE):
        print(f"Error: File not found: {THREAD_ITEM_POST_FILE}")
        return False
    
    print(f"Modifying {THREAD_ITEM_POST_FILE}...")
    with open(THREAD_ITEM_POST_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already modified
    if 'InlineTextPost' in content:
        print(f"  {THREAD_ITEM_POST_FILE} already modified.")
        return True
    
    # Add import for InlineTextPost
    import_marker = "import {Text} from '#/components/Typography'"
    if import_marker not in content:
        print(f"  Error: Could not find import marker in {THREAD_ITEM_POST_FILE}")
        return False
    
    new_import = import_marker + "\nimport {InlineTextPost} from '#/components/Post/InlineTextPost'"
    content = content.replace(import_marker, new_import)
    
    # Add conditional rendering for InlineTextPost
    old_return = '''  const {isActive: live} = useActorStatus(post.author)

  return (
    <SubtleHoverWrapper>'''
    
    new_return = '''  const {isActive: live} = useActorStatus(post.author)

  // Determine if this is a text-only post (no embeds)
  const isTextOnlyPost = !post.embed && Boolean(richText?.text)

  // For text-only posts, use inline layout
  if (isTextOnlyPost) {
    return (
      <ThreadItemPostOuterWrapper item={item} overrides={overrides}>
        <InlineTextPost
          post={postShadow}
          record={record}
          richText={richText}
          moderation={moderation}
          onPressReply={onPressReply}
        />
      </ThreadItemPostOuterWrapper>
    )
  }

  return (
    <SubtleHoverWrapper>'''
    
    if old_return not in content:
        print(f"  Error: Could not find return statement in {THREAD_ITEM_POST_FILE}")
        return False
    
    content = content.replace(old_return, new_return)
    
    with open(THREAD_ITEM_POST_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✓ Modified {THREAD_ITEM_POST_FILE}")
    return True


def modify_post():
    """Modify Post.tsx to use InlineTextPost for text-only posts."""
    if not os.path.exists(POST_FILE):
        print(f"Error: File not found: {POST_FILE}")
        return False
    
    print(f"Modifying {POST_FILE}...")
    with open(POST_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already modified
    if 'InlineTextPost' in content:
        print(f"  {POST_FILE} already modified.")
        return True
    
    # Add import for InlineTextPost
    import_marker = "import * as bsky from '#/types/bsky'"
    if import_marker not in content:
        print(f"  Error: Could not find import marker in {POST_FILE}")
        return False
    
    new_import = import_marker + "\nimport {InlineTextPost} from '#/components/Post/InlineTextPost'"
    content = content.replace(import_marker, new_import)
    
    # Add conditional rendering for InlineTextPost
    old_return = '''  const [hover, setHover] = useState(false)
  return (
    <Link
      href={itemHref}'''
    
    new_return = '''  const [hover, setHover] = useState(false)

  // Determine if this is a text-only post (no embeds)
  const isTextOnlyPost = !post.embed && Boolean(richText?.text)

  // Use inline layout for text-only posts
  if (isTextOnlyPost) {
    return (
      <InlineTextPost
        post={post}
        record={record}
        richText={richText}
        moderation={moderation}
        onPressReply={onPressReply}
        onBeforePress={onBeforePress}
        hideTopBorder={hideTopBorder}
      />
    )
  }

  return (
    <Link
      href={itemHref}'''
    
    if old_return not in content:
        print(f"  Error: Could not find return statement in {POST_FILE}")
        return False
    
    content = content.replace(old_return, new_return)
    
    with open(POST_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✓ Modified {POST_FILE}")
    return True


def main():
    print("=" * 60)
    print("Inline Text Post Layout Setup")
    print("=" * 60)
    print()
    print("This script adds a compact inline layout for text-only posts:")
    print("  • Avatar on the left")
    print("  • Handle + text inline on the same row")
    print("  • Action icons (reply, like, menu) on the right")
    print()
    print("-" * 60)
    
    # Step 1: Create component files
    print("\n[1/4] Creating component files...")
    if not create_component_files():
        print("\n❌ Failed to create component files")
        return
    
    # Step 2: Modify PostFeedItem.tsx
    print("\n[2/4] Modifying PostFeedItem.tsx...")
    if not modify_post_feed_item():
        print("\n⚠️  Could not modify PostFeedItem.tsx (may already be modified or file structure changed)")
    
    # Step 3: Modify ThreadItemPost.tsx  
    print("\n[3/4] Modifying ThreadItemPost.tsx...")
    if not modify_thread_item_post():
        print("\n⚠️  Could not modify ThreadItemPost.tsx (may already be modified or file structure changed)")
    
    # Step 4: Modify Post.tsx
    print("\n[4/4] Modifying Post.tsx...")
    if not modify_post():
        print("\n⚠️  Could not modify Post.tsx (may already be modified or file structure changed)")
    
    print("\n" + "=" * 60)
    print("✅ Inline text post layout setup complete!")
    print("=" * 60)
    print()
    print("Text-only posts will now display in a compact inline format.")
    print("Restart your development server to see the changes.")


if __name__ == "__main__":
    main()
