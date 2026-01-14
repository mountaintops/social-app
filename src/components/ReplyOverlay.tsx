import { memo, useMemo } from 'react'
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
import { atoms as a, useTheme } from '#/alf'

const MAX_OVERLAYS = 9

interface ReplyOverlayProps {
    replies: AppBskyFeedDefs.PostView[]
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

let ReplyOverlay = ({ replies }: ReplyOverlayProps): React.ReactNode => {
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
                // Check for media
                return getMediaUrl(reply) !== null
            })
            .slice(0, MAX_OVERLAYS)
    }, [replies])

    // Debug logging
    console.log('[ReplyOverlay] Received replies:', replies.length, 'Media replies:', mediaReplies.length)

    if (mediaReplies.length === 0) {
        return null
    }

    const handlePress = (post: AppBskyFeedDefs.PostView) => {
        const href = makeProfileLink(post.author, 'post', post.uri.split('/').pop())
        navigation.push('PostThread', { name: post.author.handle, rkey: post.uri.split('/').pop() })
    }

    // Layout: 3 or less = vertical, 4+ = grid (2 columns)
    const isGrid = mediaReplies.length >= 4
    const columns = 2 // Always 2 columns for grid

    return (
        <View style={[styles.container]}>
            <View
                style={[
                    styles.overlayContainer,
                    isGrid ? styles.gridContainer : styles.verticalContainer,
                    isGrid && { width: columns * 54 },
                ]}>
                {mediaReplies.map((reply, index) => {
                    const mediaUrl = getMediaUrl(reply)
                    if (!mediaUrl) return null

                    return (
                        <Pressable
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
