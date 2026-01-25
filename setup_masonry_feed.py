
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

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created/Overwritten {path}")

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file_content(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {path}")

def create_feed_masonry_row():
    content = """import { memo } from 'react'
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
    write_file(FEED_MASONRY_ROW_PATH, content)

def patch_post_feed():
    content = read_file(POST_FEED_PATH)
    
    # 1. Ensure FeedMasonryRow is imported
    if "FeedMasonryRow" not in content:
        content = re.sub(
            r"(import \{ PostFeedItem \} from '\./PostFeedItem')",
            r"\1\nimport { FeedMasonryRow } from '#/components/feeds/FeedMasonryRow'",
            content
        )

    # 2. Fix broken syntax for masonryRow if present (handling the specific error user might have faced)
    # The pattern matches the broken object definition and replaces it
    broken_pattern = r"type: 'masonryRow'\s+key: string\s+leftItem: FeedRow \| null\s+rightItem: FeedRow \| null\s+}\s+\|\s+{"
    if re.search(broken_pattern, content):
         # This specific fix depends on the context, assuming it was inside arr.push
         # But in the full file provided earlier, it was inside FeedRow type AND logic
         # Let's target the runtime push first
         pass 
         # Using a regex to fix the "type pasted into code" error
         content = re.sub(
             r"arr\.push\(\{\s+type: 'masonryRow'\s+key: string\s+leftItem: FeedRow \| null\s+rightItem: FeedRow \| null\s+\}\s+\|\s+\{",
             r"arr.push({",
             content
         )

    # 3. Add renderMasonryItem helper
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

    write_file_content(POST_FEED_PATH, content)

def patch_post_feed_item():
    content = read_file(POST_FEED_ITEM_PATH)

    # 1. Add isMasonryItem to FeedItemProps if not present (already there in source, but good to check)
    # 2. Add isMasonryItem to destructured props in PostFeedItem
    if "isMasonryItem," not in content:
        content = content.replace("onShowLess,", "onShowLess,\n  isMasonryItem,")
        
        # Add to FeedItemInner props
        # We need to find the specific `onShowLess,` in PostFeedItem and FeedItemInner
        # This simple replace might be too broad, let's use context
        pass

    # Better regex approach for Props destructuring
    content = re.sub(
        r"(onShowLess,\n\}: FeedItemProps & \{)",
        r"onShowLess,\n  isMasonryItem,\n}: FeedItemProps & {",
        content
    )
    
    # 3. Pass isMasonryItem to FeedItemInner
    content = re.sub(
        r"(onShowLess=\{onShowLess\}\n\s+/\>)",
        r"onShowLess={onShowLess}\n        isMasonryItem={isMasonryItem}\n      />",
        content
    )

    # 4. Handle outerStyles logic
    if "const outerStyles = isMasonryItem" not in content:
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
        # Replace existing outerStyles definition
        content = re.sub(
            r"const outerStyles = \[\s+styles\.outer,[\s\S]+?\]",
            masonry_styles,
            content
        )

    # 5. Pass isMasonryItem to PostContent
    # Update PostContent props destructuring
    content = re.sub(
        r"(replyMedia \?:\s+AppBskyFeedDefs\.PostView\[\])",
        r"\1\n  isMasonryItem?: boolean",
        content
    )
    # Update PostContent call
    if "isMasonryItem={isMasonryItem}" not in content:
         content = re.sub(
             r"(replyMedia=\{replyMedia\}\n\s+/\>)",
             r"replyMedia={replyMedia}\n              isMasonryItem={isMasonryItem}\n            />",
             content
         )
         
    # Update PostEmbedViewContext usage
    if "PostEmbedViewContext.Masonry" not in content:
        content = content.replace(
            "viewContext={PostEmbedViewContext.Feed}",
            "viewContext={isMasonryItem ? PostEmbedViewContext.Masonry : PostEmbedViewContext.Feed}"
        )

    write_file_content(POST_FEED_ITEM_PATH, content)

def patch_embed_types():
    content = read_file(EMBED_TYPES_PATH)
    if "Masonry = 'Masonry'" not in content:
        content = content.replace(
            "FeedEmbedRecordWithMedia = 'FeedEmbedRecordWithMedia',",
            "FeedEmbedRecordWithMedia = 'FeedEmbedRecordWithMedia',\n  Masonry = 'Masonry',"
        )
    write_file_content(EMBED_TYPES_PATH, content)

def patch_image_embed():
    content = read_file(IMAGE_EMBED_PATH)
    if "PostEmbedViewContext.Masonry" not in content:
        content = content.replace(
            "rest.viewContext === PostEmbedViewContext.ThreadHighlighted",
            "rest.viewContext === PostEmbedViewContext.ThreadHighlighted ||\n              rest.viewContext === PostEmbedViewContext.Masonry"
        )
    write_file_content(IMAGE_EMBED_PATH, content)

def patch_video_embeds():
    # Native
    content = read_file(VIDEO_EMBED_NATIVE_PATH)
    
    # Add CommonProps to interface
    if "import {type CommonProps} from '../types'" not in content:
         content = content.replace(
             "import * as VideoFallback from './VideoEmbedInner/VideoFallback'",
             "import * as VideoFallback from './VideoEmbedInner/VideoFallback'\nimport {type CommonProps, PostEmbedViewContext} from '../types'"
         )

    if ": Props" in content:
        content = content.replace(": Props", ": Props & CommonProps")
    
    # Destructure viewContext
    if "function VideoEmbed({embed}:" in content:
        content = content.replace("function VideoEmbed({embed}:", "function VideoEmbed({embed, viewContext}:")
    
    # Logic for aspect ratio
    if "const ratio = 1 / 2" in content:
        content = re.sub(
            r"const ratio = 1 / 2 // max of 1:2 ratio in feeds",
            "const ratio = viewContext === PostEmbedViewContext.Masonry ? 0 : 1 / 2",
            content
        )
    
    write_file_content(VIDEO_EMBED_NATIVE_PATH, content)

    # Web
    content = read_file(VIDEO_EMBED_WEB_PATH)
     # Add CommonProps to interface
    if "import {ConstrainedImage}" in content: # Just a marker
         if "import {type CommonProps}" not in content:
             content = content.replace(
                 "import * as VideoFallback from './VideoEmbedInner/VideoFallback'",
                 "import * as VideoFallback from './VideoEmbedInner/VideoFallback'\nimport {type CommonProps, PostEmbedViewContext} from '../types'"
             )

    if "function VideoEmbed({embed}: {embed: AppBskyEmbedVideo.View})" in content:
        content = content.replace(
            "function VideoEmbed({embed}: {embed: AppBskyEmbedVideo.View})",
            "function VideoEmbed({embed, viewContext}: {embed: AppBskyEmbedVideo.View} & CommonProps)"
        )
        
    # Logic for aspect ratio
    if "const ratio = 1 / 2" in content:
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
    print("Installation Complete!")

if __name__ == "__main__":
    main()
