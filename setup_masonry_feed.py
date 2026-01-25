
import os
import re

# Define paths
BASE_DIR = os.getcwd()
SRC_DIR = os.path.join(BASE_DIR, 'src')

FEED_MASONRY_ROW_PATH = os.path.join(SRC_DIR, 'components/feeds/FeedMasonryRow.tsx')
POST_FEED_PATH = os.path.join(SRC_DIR, 'view/com/posts/PostFeed.tsx')
POST_FEED_ITEM_PATH = os.path.join(SRC_DIR, 'view/com/posts/PostFeedItem.tsx')
EMBED_TYPES_PATH = os.path.join(SRC_DIR, 'components/Post/Embed/types.ts')
IMAGE_EMBED_PATH = os.path.join(SRC_DIR, 'components/Post/Embed/ImageEmbed.tsx')
VIDEO_EMBED_NATIVE_PATH = os.path.join(SRC_DIR, 'components/Post/Embed/VideoEmbed/index.tsx')
VIDEO_EMBED_WEB_PATH = os.path.join(SRC_DIR, 'components/Post/Embed/VideoEmbed/index.web.tsx')
POST_CONTROLS_PATH = os.path.join(SRC_DIR, 'components/PostControls/index.tsx')

def write_file_content(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {path}")

def read_file(path):
    if not os.path.exists(path):
        print(f"Warning: File not found {path}")
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def create_feed_masonry_row():
    content = """import React, { memo } from 'react'
import { View, StyleSheet } from 'react-native'

interface FeedMasonryRowProps {
  leftChild: React.ReactNode
  rightChild: React.ReactNode
}

/**
 * A masonry row component that displays two posts side-by-side with flexible heights.
 * Each column will auto-size based on content, allowing for intelligent stacking
 * of square, vertical, and horizontal media posts.
 */
export function FeedMasonryRow({ leftChild, rightChild }: FeedMasonryRowProps) {
  return (
    <View style={styles.row}>
      <View style={styles.column}>
        {leftChild}
      </View>
      <View style={styles.column}>
        {rightChild}
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    paddingHorizontal: 4,
    gap: 4,
  },
  column: {
    flex: 1,
    // alignItems: 'flex-start' is not needed because the child will determine its own height
  },
})

export default memo(FeedMasonryRow)
"""
    write_file_content(FEED_MASONRY_ROW_PATH, content)

def patch_post_feed():
    content = read_file(POST_FEED_PATH)
    if not content: return
    
    # 0. Add masonryRow to FeedRow type
    if "type: 'masonryRow'" not in content.split('getItemsForFeedback')[0]:
        content = content.replace(
            "  | {",
            "  | {\n    type: 'masonryRow'\n    key: string\n    leftItem: FeedRow | null\n    rightItem: FeedRow | null\n  }\n  | {",
            1
        )

    # 1. Ensure FeedMasonryRow is imported
    if "FeedMasonryRow" not in content:
        content = re.sub(
            r"import\s*\{\s*PostFeedItem\s*\}\s*from\s*'\./PostFeedItem'",
            r"import {PostFeedItem} from './PostFeedItem'\nimport {FeedMasonryRow} from '#/components/feeds/FeedMasonryRow'",
            content
        )

    # 2. Add renderMasonryItem helper
    if "const renderMasonryItem = useCallback" not in content:
        helper_code = """
  // Helper function to render individual items within masonry rows
  const renderMasonryItem = useCallback(
    (
      row: FeedRow,
      feedFeedbackCtx: typeof feedFeedback,
      onShowLess: (interaction: AppBskyFeedDefs.Interaction) => void,
    ) => {
      if (row.type !== 'sliceItem') return null

      const slice = row.slice
      const indexInSlice = row.indexInSlice
      const item = slice.items[indexInSlice]

      return (
        <PostFeedItem
          post={item.post}
          record={item.record}
          reason={indexInSlice === 0 ? slice.reason : undefined}
          feedContext={slice.feedContext}
          reqId={slice.reqId}
          moderation={item.moderation}
          parentAuthor={item.parentAuthor}
          showReplyTo={row.showReplyTo}
          isThreadParent={false}
          isThreadChild={false}
          isThreadLastChild={false}
          isParentBlocked={item.isParentBlocked}
          isParentNotFound={item.isParentNotFound}
          hideTopBorder={true}
          rootPost={slice.items[0].post}
          onShowLess={onShowLess}
          isMasonryItem={true}
        />
      )
    },
    [],
  )

  const renderItem"""
        content = content.replace("const renderItem", helper_code)

    # 3. Inject Masonry Grouping Logic
    if "const masonryArr: FeedRow[] = []" not in content:
        masonry_logic = """
    // Convert feed items to masonry layout (2 columns)
    const masonryArr: FeedRow[] = []
    let pendingSliceItem: FeedRow | null = null

    for (const item of arr) {
      if (item.type === 'sliceItem') {
        if (pendingSliceItem === null) {
          pendingSliceItem = item
        } else {
          // Pair two items into a masonry row
          masonryArr.push({
            type: 'masonryRow',
            key: 'masonry-' + pendingSliceItem.key + '-' + item.key,
            leftItem: pendingSliceItem,
            rightItem: item,
          })
          pendingSliceItem = null
        }
      } else {
        // Non-sliceItem: flush pending item first, then add full-width item
        if (pendingSliceItem !== null) {
          masonryArr.push({
            type: 'masonryRow',
            key: 'masonry-' + pendingSliceItem.key + '-solo',
            leftItem: pendingSliceItem,
            rightItem: null,
          })
          pendingSliceItem = null
        }
        masonryArr.push(item)
      }
    }

    // Flush any remaining pending item
    if (pendingSliceItem !== null) {
      masonryArr.push({
        type: 'masonryRow',
        key: 'masonry-' + pendingSliceItem.key + '-solo',
        leftItem: pendingSliceItem,
        rightItem: null,
      })
    }

    return masonryArr"""
        
        content = re.sub(
            r"return arr\s*\}\, \[",
            f"{masonry_logic}\n  }}, [",
            content
        )

    # 4. Handle rendering of masonryRow
    if "row.type === 'masonryRow'" not in content:
        render_logic = """} else if (row.type === 'masonryRow') {
        const leftItem = row.leftItem
        const rightItem = row.rightItem
        return (
          <FeedMasonryRow
            leftChild={leftItem ? renderMasonryItem(leftItem, feedFeedback, onPressShowLess) : null}
            rightChild={rightItem ? renderMasonryItem(rightItem, feedFeedback, onPressShowLess) : null}
          />
        )
      } else if (row.type === 'sliceItem') {"""
        
        content = content.replace("} else if (row.type === 'sliceItem') {", render_logic)
        
    write_file_content(POST_FEED_PATH, content)

def patch_post_feed_item():
    content = read_file(POST_FEED_ITEM_PATH)
    if not content: return

    # 1. Add isMasonryItem to FeedItemProps
    if "isMasonryItem?:" not in content:
        content = re.sub(
            r"(hideTopBorder\?: boolean)",
            r"\1\n  isMasonryItem?: boolean",
            content
        )

    # 2. Add isMasonryItem to destructured props in PostFeedItem
    if "isMasonryItem," not in content:
        content = re.sub(
            r"(onShowLess,)(\s*)\}: FeedItemProps & \{",
            r"\1\2  isMasonryItem,\2}: FeedItemProps & {",
            content,
            flags=re.DOTALL
        )

    # 3. Pass isMasonryItem to FeedItemInner
    if "isMasonryItem={isMasonryItem}" not in content:
        content = re.sub(
            r"(onShowLess=\{onShowLess\})(\s*/>)",
            r"\1\n        isMasonryItem={isMasonryItem}\2",
            content,
            flags=re.DOTALL
        )
    
    # 4. Add isMasonryItem to FeedItemInner props
    parts = content.split("let FeedItemInner =")
    if len(parts) > 1:
        inner_part = parts[1]
        if "isMasonryItem," not in inner_part.split("}: FeedItemProps")[0]:
            inner_part = re.sub(
                r"(onShowLess,)(\s*)\}: FeedItemProps & \{",
                r"\1\2  isMasonryItem,\2}: FeedItemProps & {",
                inner_part,
                count=1,
                flags=re.DOTALL
            )
            content = parts[0] + "let FeedItemInner =" + inner_part

    # 5. Handle outerStyles logic in FeedItemInner
    if "styles.masonryOuter" not in content:
        masonry_styles = """const outerStyles = isMasonryItem
    ? [
        styles.masonryOuter,
        {
          borderColor: pal.colors.border,
        },
      ]
    : [
        styles.outer,
        {
          borderColor: pal.colors.border,
          paddingBottom:
            isThreadLastChild || (!isThreadChild && !isThreadParent)
              ? 8
              : undefined,
          borderTopWidth:
            hideTopBorder || isThreadChild ? 0 : StyleSheet.hairlineWidth,
        },
      ]"""
        content = re.sub(
            r"const outerStyles = \[\s*styles\.outer,[\s\S]+?\]",
            masonry_styles,
            content
        )

    # 6. PostContent: Add isMasonryItem prop to function signature
    parts = content.split("let PostContent =")
    if len(parts) > 1:
        post_content_part = parts[1]
        
        if "isMasonryItem," not in post_content_part.split("}: {")[0]:
             post_content_part = re.sub(
                 r"(replyMedia\s*=\s*\[\],)(\s*)\}: \{",
                 r"\1\2  isMasonryItem,\2}: {",
                 post_content_part,
                 count=1,
                 flags=re.DOTALL
             )
        
        if "isMasonryItem?:" not in post_content_part:
            post_content_part = re.sub(
                r"(replyMedia\?:.*?\])(\s*)\}\):",
                r"\1\2  isMasonryItem?: boolean\2}):",
                post_content_part,
                count=1,
                flags=re.DOTALL
            )
            
        if "PostEmbedViewContext.Masonry" not in post_content_part:
            post_content_part = post_content_part.replace(
                "viewContext={PostEmbedViewContext.Feed}",
                "viewContext={isMasonryItem ? PostEmbedViewContext.Masonry : PostEmbedViewContext.Feed}"
            )
            
        content = parts[0] + "let PostContent =" + post_content_part

    # 7. Pass isMasonryItem from FeedItemInner to PostContent
    if "isMasonryItem={isMasonryItem}" not in content.split("let PostContent =")[0]:
         content = re.sub(
             r"(replyMedia=\{replyMedia\})(\s*/>)",
             r"\1\n              isMasonryItem={isMasonryItem}\2",
             content,
             count=1,
             flags=re.DOTALL
         )
         
    # 8. Ensure masonry styles are present
    if "masonryOuter:" not in content:
         content = re.sub(
             r"(const styles = StyleSheet.create\(\{)",
             r"""\1
  // Masonry compact styles
  masonryOuter: {
    paddingHorizontal: 4,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 4,
    overflow: 'hidden',
  },
  masonryContent: {
    padding: 8,
  },
""",
             content
         )

    write_file_content(POST_FEED_ITEM_PATH, content)

def patch_embed_types():
    content = read_file(EMBED_TYPES_PATH)
    if not content: return
    if "Masonry = 'Masonry'" not in content:
        content = content.replace(
            "FeedEmbedRecordWithMedia = 'FeedEmbedRecordWithMedia',",
            "FeedEmbedRecordWithMedia = 'FeedEmbedRecordWithMedia',\n  Masonry = 'Masonry',"
        )
    write_file_content(EMBED_TYPES_PATH, content)

def patch_image_embed():
    content = read_file(IMAGE_EMBED_PATH)
    if not content: return
    if "PostEmbedViewContext.Masonry" not in content:
        content = content.replace(
            "rest.viewContext === PostEmbedViewContext.ThreadHighlighted",
            "rest.viewContext === PostEmbedViewContext.ThreadHighlighted ||\n              rest.viewContext === PostEmbedViewContext.Masonry"
        )
    write_file_content(IMAGE_EMBED_PATH, content)

def patch_post_controls():
    content = read_file(POST_CONTROLS_PATH)
    if not content: return
    
    # 1. Add sanitizeHandle import
    if "sanitizeHandle" not in content:
        content = content.replace(
            "import * as Toast from '#/view/com/util/Toast'",
            "import * as Toast from '#/view/com/util/Toast'\nimport {sanitizeHandle} from '#/lib/strings/handles'"
        )

    # 2. Add useTheme import to #/alf
    if "useTheme" not in content:
        if "import {atoms as a, useBreakpoints} from '#/alf'" in content:
            content = content.replace(
                "import {atoms as a, useBreakpoints} from '#/alf'",
                "import {atoms as a, useBreakpoints, useTheme} from '#/alf'"
            )
        else:
            content = content.replace(
                "import {atoms as a,",
                "import {atoms as a, useTheme,"
            )

    # 3. Add UserAvatar import
    if "UserAvatar" not in content and "import {Reply as Bubble}" in content:
        content = content.replace(
            "import {Reply as Bubble}",
            "import {UserAvatar} from '#/view/com/util/UserAvatar'\nimport {Reply as Bubble}"
        )

    # 4. Inject Avatar + Handle into JSX
    if "marginLeft: 6" not in content:
        pattern = r"(return \(\s*<View\s*style=\[[\s\S]*?a\.gap_sm,\s*style,\s*\]\s*>\s*)"
        insertion = """      {/* Left side: Avatar + Handle (InlineTextPost style) */}
      <View style={[a.flex_row, a.align_center, a.gap_sm, { flex: 1, marginLeft: 6 }]}>
        <UserAvatar size={24} avatar={post.author.avatar} type="user" />
        <PostControlButtonText style={[a.text_sm, t.atoms.text_contrast_medium]}>{sanitizeHandle(post.author.handle, "@")}</PostControlButtonText>
      </View>
"""
        if re.search(pattern, content):
            content = re.sub(pattern, r"\1" + insertion, content)

    write_file_content(POST_CONTROLS_PATH, content)

def patch_video_embeds():
    # Native
    content = read_file(VIDEO_EMBED_NATIVE_PATH)
    if content:
        if "useTheme" not in content:
            content = content.replace(
                "import { atoms as a } from '#/alf'",
                "import { atoms as a, useTheme } from '#/alf'"
            )
        if "PostEmbedViewContext" not in content:
             content = content.replace(
                 "import * as VideoFallback from './VideoEmbedInner/VideoFallback'",
                 "import * as VideoFallback from './VideoEmbedInner/VideoFallback'\nimport {type CommonProps, PostEmbedViewContext} from '../types'"
             )
        if ": Props" in content and ": Props & CommonProps" not in content:
            content = content.replace(": Props", ": Props & CommonProps")
        if "function VideoEmbed({embed}:" in content:
            content = content.replace("function VideoEmbed({embed}:", "function VideoEmbed({embed, viewContext}:")
        if "viewContext === PostEmbedViewContext.Masonry" not in content:
            content = re.sub(
                r"const ratio = 1 / 2 // max of 1:2 ratio in feeds",
                "const ratio = viewContext === PostEmbedViewContext.Masonry ? 0 : 1 / 2",
                content
            )
        write_file_content(VIDEO_EMBED_NATIVE_PATH, content)

    # Web
    content = read_file(VIDEO_EMBED_WEB_PATH)
    if content:
        if "PostEmbedViewContext" not in content:
             content = content.replace(
                 "import * as VideoFallback from './VideoEmbedInner/VideoFallback'",
                 "import * as VideoFallback from './VideoEmbedInner/VideoFallback'\nimport {type CommonProps, PostEmbedViewContext} from '../types'"
             )
        if "function VideoEmbed({embed}: {embed: AppBskyEmbedVideo.View})" in content:
            content = content.replace(
                "function VideoEmbed({embed}: {embed: AppBskyEmbedVideo.View})",
                "function VideoEmbed({embed, viewContext}: {embed: AppBskyEmbedVideo.View} & CommonProps)"
            )
        if "viewContext === PostEmbedViewContext.Masonry" not in content:
            content = re.sub(
                r"const ratio = 1 / 2 // max of 1:2 ratio in feeds",
                "const ratio = viewContext === PostEmbedViewContext.Masonry ? 0 : 1 / 2",
                content
            )
        write_file_content(VIDEO_EMBED_WEB_PATH, content)

def main():
    print("Starting Masonry Feed Layout Installation...")
    create_feed_masonry_row()
    patch_embed_types()
    patch_post_feed()
    patch_post_feed_item()
    patch_image_embed()
    patch_video_embeds()
    patch_post_controls()
    print("Installation Complete!")

if __name__ == "__main__":
    main()
