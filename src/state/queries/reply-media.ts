import {
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
