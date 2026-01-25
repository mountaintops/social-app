
import sys
import re
import os

def replace_regex(content, replacements):
    new_content = content
    for pattern, replacement in replacements:
        new_content = re.sub(pattern, replacement, new_content, flags=re.DOTALL)
    return new_content

def process_file(file_path, patterns=None, regex_replacements=None, literal_replacements=None):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Reading {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content

    if regex_replacements:
        new_content = replace_regex(new_content, regex_replacements)

    if literal_replacements:
        for target, replacement in literal_replacements:
            if replacement in new_content: 
                continue
            new_content = new_content.replace(target, replacement)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Modified {file_path}")
    else:
        print(f"No changes for {file_path}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    def p(path): return os.path.join(base_dir, path)

    # 1. RightNav: Remove completely
    right_nav_path = p('src/view/shell/desktop/RightNav.tsx')
    with open(right_nav_path, 'r') as f:
         if 'return null; // disabled' not in f.read():
             right_nav_regex = [
                 (r'(export function DesktopRightNav\(\{.*?\}\) \{)', r'\1\n  return null; // disabled')
             ]
             process_file(right_nav_path, regex_replacements=right_nav_regex)

    # 2. PostFeedItem: Remove Avatar (layoutAvi) and ReplyLine
    feed_item_path = p('src/view/com/posts/PostFeedItem.tsx')
    process_file(feed_item_path, 
        literal_replacements=[('style={styles.layoutAvi}', "style={[styles.layoutAvi, {display: 'none', width: 0, paddingHorizontal: 0}]}")],
        regex_replacements=[(r'(<View\s+style=\{\[\s*styles\.replyLine.*?/>)', r'null')]
    )

    # 3. PostMeta: Hide component completely (removes top handle/header)
    post_meta_path = p('src/view/com/util/PostMeta.tsx')
    process_file(post_meta_path, regex_replacements=[(r'(let PostMeta = \(opts: PostMetaOpts\): React.ReactNode => \{)', r'\1\n  return null; // disabled')])

    # 4. PostControls: Reorder buttons
    post_controls_path = p('src/components/PostControls/index.tsx')
    
    # Add UserAvatar/sanitizeHandle import if missing
    with open(post_controls_path, 'r') as f:
        content = f.read()
        if 'UserAvatar' not in content:
             process_file(post_controls_path, literal_replacements=[("import { useAnalytics } from '#/analytics'", "import { useAnalytics } from '#/analytics'\nimport { UserAvatar } from '#/view/com/util/UserAvatar'")])
        if 'sanitizeHandle' not in content:
             process_file(post_controls_path, literal_replacements=[("import { useAnalytics } from '#/analytics'", "import { useAnalytics } from '#/analytics'\nimport { sanitizeHandle } from '#/lib/strings/handles'")])

    new_post_controls_view = (
        'return (\n'
        '    <View\n'
        '      style={[\n'
        '        a.flex_row,\n'
        '        a.justify_between,\n'
        '        a.align_center,\n'
        '        !big && a.pt_2xs,\n'
        '        a.gap_sm,\n'
        '        style,\n'
        '      ]}>\n'
        '      {/* Left side: Avatar + Handle (InlineTextPost style) */}\n'
        '      <View style={[a.flex_row, a.align_center, a.gap_sm, {flex: 1, marginLeft: 6}]}>\n'
        '        <UserAvatar size={24} avatar={post.author.avatar} type="user" />\n'
        '        <PostControlButtonText style={[a.text_sm, t.atoms.text_contrast_medium]}>{sanitizeHandle(post.author.handle, "@")}</PostControlButtonText>\n'
        '      </View>\n'
        '      {/* Right side: Buttons (compact) */}\n'
        '      <View style={[a.flex_row, a.align_center, a.gap_xs, {maxWidth: 320}]}>\n'
        '      {/* Reply */}\n'
        '      <View style={[a.align_center]}>\n'
        '        <PostControlButton\n'
        '            testID="replyBtn"\n'
        '            onPress={\n'
        '              !replyDisabled\n'
        '                ? () =>\n'
        '                    requireAuth(() => {\n'
        '                      ax.metric(\'post:clickReply\', {\n'
        '                        uri: post.uri,\n'
        '                        authorDid: post.author.did,\n'
        '                        logContext,\n'
        '                        feedDescriptor,\n'
        '                      })\n'
        '                      onPressReply()\n'
        '                    })\n'
        '                : undefined\n'
        '            }\n'
        '            label={_(\n'
        '              msg({\n'
        '                message: `Reply (${plural(post.replyCount || 0, {\n'
        '                  one: \'# reply\',\n'
        '                  other: \'# replies\',\n'
        '                })})`,\n'
        '                comment:\n'
        '                  \'Accessibility label for the reply button, verb form followed by number of replies and noun form\',\n'
        '              }),\n'
        '            )}\n'
        '            big={big}>\n'
        '            <PostControlButtonIcon icon={Bubble} />\n'
        '            {typeof post.replyCount !== \'undefined\' && post.replyCount > 0 && (\n'
        '              <PostControlButtonText>\n'
        '                {formatPostStatCount(post.replyCount)}\n'
        '              </PostControlButtonText>\n'
        '            )}\n'
        '          </PostControlButton>\n'
        '      </View>\n'
        '\n'
        '      {/* Like */}\n'
        '      <View style={[a.align_center]}>\n'
        '          <PostControlButton\n'
        '            testID="likeBtn"\n'
        '            big={big}\n'
        '            onPress={() => requireAuth(() => onPressToggleLike())}\n'
        '            label={\n'
        '              post.viewer?.like\n'
        '                ? _(\n'
        '                    msg({\n'
        '                      message: `Unlike (${plural(post.likeCount || 0, {\n'
        '                        one: \'# like\',\n'
        '                        other: \'# likes\',\n'
        '                      })})`,\n'
        '                      comment:\n'
        '                        \'Accessibility label for the like button when the post has been liked, verb followed by number of likes and noun\',\n'
        '                    }),\n'
        '                  )\n'
        '                : _(\n'
        '                    msg({\n'
        '                      message: `Like (${plural(post.likeCount || 0, {\n'
        '                        one: \'# like\',\n'
        '                        other: \'# likes\',\n'
        '                      })})`,\n'
        '                      comment:\n'
        '                        \'Accessibility label for the like button when the post has not been liked, verb form followed by number of likes and noun form\',\n'
        '                    }),\n'
        '                  )\n'
        '            }>\n'
        '            <AnimatedLikeIcon\n'
        '              isLiked={Boolean(post.viewer?.like)}\n'
        '              big={big}\n'
        '              hasBeenToggled={hasLikeIconBeenToggled}\n'
        '            />\n'
        '            <CountWheel\n'
        '              likeCount={post.likeCount ?? 0}\n'
        '              big={big}\n'
        '              isLiked={Boolean(post.viewer?.like)}\n'
        '              hasBeenToggled={hasLikeIconBeenToggled}\n'
        '            />\n'
        '          </PostControlButton>\n'
        '      </View>\n'
        '\n'
        '      <View style={[a.flex_row, a.justify_end, secondaryControlSpacingStyles]}>\n'
        '        <BookmarkButton\n'
        '          post={post}\n'
        '          big={big}\n'
        '          logContext={logContext}\n'
        '          hitSlop={{\n'
        '            right: secondaryControlSpacingStyles.gap / 2,\n'
        '          }}\n'
        '        />\n'
        '        <ShareMenuButton\n'
        '          testID="postShareBtn"\n'
        '          post={post}\n'
        '          big={big}\n'
        '          record={record}\n'
        '          richText={richText}\n'
        '          timestamp={post.indexedAt}\n'
        '          threadgateRecord={threadgateRecord}\n'
        '          onShare={onShare}\n'
        '          hitSlop={{\n'
        '            left: secondaryControlSpacingStyles.gap / 2,\n'
        '            right: secondaryControlSpacingStyles.gap / 2,\n'
        '          }}\n'
        '          logContext={logContext}\n'
        '        />\n'
        '        <PostMenuButton\n'
        '          testID="postDropdownBtn"\n'
        '          post={post}\n'
        '          postFeedContext={feedContext}\n'
        '          postReqId={reqId}\n'
        '          big={big}\n'
        '          record={record}\n'
        '          richText={richText}\n'
        '          timestamp={post.indexedAt}\n'
        '          threadgateRecord={threadgateRecord}\n'
        '          onShowLess={onShowLess}\n'
        '          hitSlop={{\n'
        '            left: secondaryControlSpacingStyles.gap / 2,\n'
        '          }}\n'
        '          logContext={logContext}\n'
        '        />\n'
        '      </View>\n'
        '      </View>\n'
        '    </View>\n'
        '  )'
    )
    
    post_controls_regex = [
        (r'(return \(\s+<View\s+style=\{\[\s*a\.flex_row,\s+a\.justify_between[\s\S]*?logContext=\{logContext\}\n\s+/>\n\s+</View>\n\s+</View>\n\s+\))', new_post_controls_view)
    ]
    
    process_file(post_controls_path, regex_replacements=post_controls_regex)

    # 4.1 PostControls: Fix color and vertical alignment (ensure theme color)
    process_file(post_controls_path, literal_replacements=[
        ("style={{fontSize: 15, fontWeight: 'bold', color: 'black'}}", "style={[{fontSize: 15, fontWeight: 'bold'}, t.atoms.text]}")
    ])

    # 5. PostFeedItem: Fix Media Centering (symmetric padding) and Reduce Bottom Margin
    process_file(feed_item_path, regex_replacements=[
        (r'outer: \{\s*paddingLeft: 10,\s*paddingRight: 15,', r'outer: {\n    paddingHorizontal: 10,'),
        (r'embed: \{\n\s*marginBottom: 6,', r'embed: {\n    marginBottom: 0,\n    marginTop: 0,\n    marginHorizontal: 0,') 
    ])

    # 4.2 PostControls: Add useTheme Hook
    process_file(post_controls_path, literal_replacements=[
        ("import { atoms as a, useBreakpoints } from '#/alf'", "import { atoms as a, useBreakpoints, useTheme } from '#/alf'"),
        ("const ax = useAnalytics()", "const ax = useAnalytics()\n  const t = useTheme()")
    ])

    # 5. Settings (Links) - DISABLED: causes duplicate Help buttons
    # settings_replacement = (...)
    # The replacement logic was creating duplicates, removed for now

    # 6. InlineTextPost (Text-only links disabled)
    inline_text_replacements = [
        ('href={itemHref}', 'href={undefined} accessible={false}'),
    ]
    process_file(p('src/components/Post/InlineTextPost.tsx'), literal_replacements=inline_text_replacements)

    # 7. ThreadComposePrompt (Hide)
    compose_prompt_path = p('src/screens/PostThread/components/ThreadComposePrompt.tsx')
    if os.path.exists(compose_prompt_path):
        with open(compose_prompt_path, 'r') as f:
             if 'return null;' not in f.read():
                process_file(compose_prompt_path, regex_replacements=[(r'(export function ThreadComposePrompt\(\{.*?\}\) \{)', r'\1\n  return null;')])

    # 8. Explore (Hide modules)
    explore_patterns = [
        ("Trending Topics", (r'(i\.push\(trendingTopicsModule\))', 'js')),
        ("Suggested Feeds", (r'(i\.push\(\.\.\.suggestedFeedsModule\))', 'js')),
        ("Suggested Follows", (r'(i\.push\(\.\.\.suggestedFollowsModule\))', 'js')),
        ("Suggested Starter Packs", (r'(i\.push\(\.\.\.suggestedStarterPacksModule\))', 'js')),
        ("Feed Previews", (r'(i\.push\(\.\.\.feedPreviewsModule\))', 'js')),
        ("Interests Nux", (r'(i\.push\(\.\.\.interestsNuxModule\))', 'js')),
        ("Live Event Feeds", (r'(i\.push\(\{type: \'liveEventFeedsBanner\', key: \'liveEventFeedsBanner\'\}\))', 'js')),
    ]
    process_file(p('src/screens/Search/Explore.tsx'), patterns=explore_patterns)

    # 9. Drawer (Hide footer)
    drawer_patterns = [
        ("DrawerFooter", (r'(<DrawerFooter[^>]*/>)', 'jsx')),
        ("ExtraLinks", (r'(<ExtraLinks[^>]*/>)', 'jsx')),
    ]
    process_file(p('src/view/shell/Drawer.tsx'), patterns=drawer_patterns)

    # 10. ComposerPrompt (Hide)
    composer_prompt_path = p('src/view/com/feeds/ComposerPrompt.tsx')
    if os.path.exists(composer_prompt_path):
        with open(composer_prompt_path, 'r') as f:
             if 'return null;' not in f.read():
                process_file(composer_prompt_path, regex_replacements=[(r'(export function ComposerPrompt\(\) \{)', r'\1\n  return null;')])

    # 11. FollowingEndOfFeed (Hide)
    end_of_feed_path = p('src/view/com/posts/FollowingEndOfFeed.tsx')
    if os.path.exists(end_of_feed_path):
        with open(end_of_feed_path, 'r') as f:
             if 'return null;' not in f.read():
                process_file(end_of_feed_path, regex_replacements=[(r'return \(', 'return null;\n    return (')])

    # 12. ThreadItemPost (Hide lines)
    thread_item_patterns = [
        ("ParentReplyLine", (r'(<ThreadItemPostParentReplyLine\s+item=\{item\}\s*/>)', 'jsx'))
    ]
    thread_item_literal = [
        ('item.ui.showChildReplyLine', 'false && item.ui.showChildReplyLine'),
        ('item.ui.precedesChildReadMore', 'false && item.ui.precedesChildReadMore')
    ]
    process_file(p('src/screens/PostThread/components/ThreadItemPost.tsx'), patterns=thread_item_patterns, literal_replacements=thread_item_literal)

    # 13. PostMenuItems (Transferred from comment_out_ui.py)
    # Using regex replacement to safely nullify items without nesting comments
    post_menu_items_replacements = [
        (r'(<Menu\.Item\s+[^>]*testID="postDropdownTranslateBtn"[\s\S]*?</Menu\.Item>)', '{null}'),
        (r'(<Menu\.Item\s+[^>]*testID="postDropdownCopyTextBtn"[\s\S]*?</Menu\.Item>)', '{null}'),
        (r'(<Menu\.Item\s+[^>]*testID="postDropdownShowMoreBtn"[\s\S]*?</Menu\.Item>)', '{null}'),
        (r'(<Menu\.Item\s+[^>]*testID="postDropdownShowLessBtn"[\s\S]*?</Menu\.Item>)', '{null}'),
        (r'(<Menu\.Item\s+[^>]*testID="postDropdownMuteThreadBtn"[\s\S]*?</Menu\.Item>)', '{null}'),
        (r'(<Menu\.Item\s+[^>]*testID="postDropdownReportMisclassificationBtn"[\s\S]*?</Menu\.Item>)', '{null}'),
        (r'(<Menu\.Divider\s*/>)', '{null}'),
    ]
    process_file(p('src/components/PostControls/PostMenu/PostMenuItems.tsx'), regex_replacements=post_menu_items_replacements)

    # 14. LeftNav: Remove "Add another account"
    # Target: <Menu.Item label={_(msg`Add another account`)} ... </Menu.Item>
    left_nav_replacements = [
        (r'(<Menu\.Item\s+[^>]*label=\{_\(msg`Add another account`\)\}[\s\S]*?</Menu\.Item>)', '{null}'),
    ]
    process_file(p('src/view/shell/desktop/LeftNav.tsx'), regex_replacements=left_nav_replacements)

    # 15. AccountSettings: Remove "Export my data"
    # Target: <SettingsList.PressableItem ... label={_(msg`Export my data`)} ... </SettingsList.PressableItem>
    account_settings_replacements = [
        (r'(<SettingsList\.PressableItem\s+[^>]*label=\{_\(msg`Export my data`\)\}[\s\S]*?</SettingsList\.PressableItem>)', '{null}'),
    ]
    process_file(p('src/screens/Settings/AccountSettings.tsx'), regex_replacements=account_settings_replacements)

    # 16. ServerInput: Remove disclaimer
    # Target: Bluesky is an open network... (handles line breaks)
    server_input_replacements = [
         (r'(Bluesky is an open network where you can choose your own[\s\S]*?default Bluesky Social option\.)', ''),
         (r'(Bluesky is an open network where you can choose your hosting[\s\S]*?host your own server\.)', ''), 
         (r'(Note: Bluesky is an open and public network[\s\S]*?logged-out users by other apps and websites\.)', ''),
         (r'(If you\'re a developer, you can host your own server\.)', '') # Also remove this short one if present
    ]
    process_file(p('src/components/dialogs/ServerInput.tsx'), regex_replacements=server_input_replacements)

    # 17. Moderation: Remove "Bluesky Moderation Service" label
    moderation_replacements = [
        (r"sourceDisplayName = 'Bluesky Moderation Service'", "sourceDisplayName = ''"),
    ]
    process_file(p('src/lib/moderation/useModerationCauseDescription.ts'), literal_replacements=moderation_replacements)

    # 18. VerificationCheck: Return null
    verification_check_path = p('src/components/verification/VerificationCheck.tsx')
    if os.path.exists(verification_check_path):
        with open(verification_check_path, 'r') as f:
             if 'return null; // disabled' not in f.read():
                process_file(verification_check_path, regex_replacements=[(r'(export function VerificationCheck\(\{[\s\S]*?\) \{)', r'\1\n  return null; // disabled')])

    # 19. LiveEventFeedsSettingsToggle: Hide
    live_event_replacements = [
        (r'(export function LiveEventFeedsSettingsToggle\(\) \{)', r'\1\n  return null; // disabled'),
    ]
    process_file(p('src/features/liveEvents/components/LiveEventFeedsSettingsToggle.tsx'), regex_replacements=live_event_replacements)

    # 20. PostInteractionSettingsDialog: Remove "Allow quote posts"
    # DISABLED: causes syntax errors due to conditional wrapping
    # post_interaction_replacements = [
    #     (r'(<Toggle\.Item\s+name="quoteposts"[\s\S]*?</Toggle\.Item>)', '{null}'),
    #     (r'(<View style=\{\[\{minHeight: 24\}, a\.justify_center\]\}>[\s\S]*?</View>)', '{null}'),
    # ]
    # process_file(p('src/components/dialogs/PostInteractionSettingsDialog.tsx'), regex_replacements=post_interaction_replacements)

    # 21. PostFeedItem: Disable clicks on text posts
    # Target: <Link ... testID={`feedItem-by-${post.author.handle}`} ...>
    # We want to replace Link with View, AND remove href/onPress props.
    # regex to match opening tag of Link with that testID
    # It constructs testID dynamically.
    # Pattern: <Link testID={`feedItem-by-${post.author.handle}`} ... >
    # In regex: r'<Link\s+testID=\{`feedItem-by-\$\{post\.author\.handle\}`\}'
    post_feed_item_replacements = [
        # Replace opening Link with View and strip params (simplified approach: just replace component name and let View ignore href? No, View warns on href/onPress)
        # Better: Replace <Link ...> with <View ...> and remove props?
        # Props are spread ...rest? No.
        # Look at file: <Link testID=... style=... href=... onPress=... ... >
        # We can just change the component name to 'View' and replace 'href={...}' with ''
        (r'(<Link\s+testID=\{`feedItem-by-\$\{post\.author\.handle\}`\})', r'<View testID={`feedItem-by-${post.author.handle}`}'),
        (r'(href=\{makeProfileLink\(post\.author, \'post\', post\.rkey\)\})', ''),
        (r'(onPress=\{onPressPost\})', ''),
        (r'(</Link>)', r'</View>'),
    ]
    # Note: Regex for closing tag </Link> might be too broad if nested.
    # BUT PostFeedItem structure:
    # <Link ...>
    #   <PostFeedItemInner ... />
    # </Link>
    # It wraps the whole item.
    # Wait, PostFeedItem.tsx uses `Link`?
    # I need to check if `Link` is imported as `Link` or from `#/components/Link`.
    # It imports `Link`? I need to check the file imports.
    # IF it's `import {Link} from ...`
    # Let's verify PostFeedItem.tsx imports.
    
    process_file(p('src/view/com/posts/PostFeedItem.tsx'), regex_replacements=post_feed_item_replacements)

    # 22. Verification Settings (remove from Navigation/Settings)
    # This is tricky without exact file content for Settings.tsx, but user said "Verification Settings".
    # We can try to remove the Link in Settings.tsx if it exists.
    # Or in Navigation.tsx if it defines the screen.
    
    # 23. Trending Videos (Interstitials)
    # Remove usage in Explore or Feed.
    trending_videos_replacements = [
        (r'(<TrendingVideos\s*/>)', '{null}'),
    ]
    # Where is TrendingVideos used? Check grep.
    # It's likely in FeedInterstitials.tsx or similar.
    # We'll just run this on src/components/interstitials/TrendingVideos.tsx to return null.
    trending_videos_path = p('src/components/interstitials/TrendingVideos.tsx')
    if os.path.exists(trending_videos_path):
        with open(trending_videos_path, 'r') as f:
             if 'return null; // disabled' not in f.read():
                process_file(trending_videos_path, regex_replacements=[(r'(export function TrendingVideos\(\)\s*\{)', r'\1\n  return null; // disabled')])

    # 24. WhoCanReply: Remove "everyone can reply" text
    who_can_reply_path = p('src/components/WhoCanReply.tsx')
    if os.path.exists(who_can_reply_path):
        with open(who_can_reply_path, 'r') as f:
             if 'return null; // disabled' not in f.read():
                process_file(who_can_reply_path, regex_replacements=[(r'(export function WhoCanReply\(\{[^)]*\}:\s*WhoCanReplyProps\)\s*\{)', r'\1\n  return null; // disabled')])

    # 25. ThreadItemAnchor: Remove full date display (niceDate), avatar and display name (keep handle)
    thread_item_anchor_path = p('src/screens/PostThread/components/ThreadItemAnchor.tsx')
    anchor_replacements = [
        # Hide main date
        (r"(\{niceDate\(i18n, post\.indexedAt, 'dot separated'\)\})", r'{null}'),
        # Remove avatar and display name, keep only handle
        (r'<View style=\{\[a\.flex_row, a\.gap_md, a\.pb_md\]\}>\s*<View collapsable=\{false\}>[\s\S]*?</Link>',
         '''<View style={[a.flex_row, a.gap_md]}>
          {/* Handle/Avatar removed entirely */}
          <View style={[a.flex_1]} />'''),
    ]
    process_file(thread_item_anchor_path, regex_replacements=anchor_replacements)

    # 26. ThreadItemPost: Hide avatar and display name in post thread (keep handle)
    # This removes the entire avatar wrapper View to prevent layout gaps
    thread_item_post_path = p('src/screens/PostThread/components/ThreadItemPost.tsx')
    thread_post_replacements = [
        # Remove avatar View wrapper entirely
        (r'<View style=\{\[a\.flex_row, a\.gap_md\]\}>\s*<View>[\s\S]*?</View>\s*<View style=\{\[a\.flex_1\]\}>', 
         '<View style={[a.flex_row, a.gap_md]}>\n            {/* Avatar container removed to fix layout */}\n\n            <View style={[a.flex_1]}>'),
        # Hide PostMeta (which contains display name)
        (r'(<PostMeta\s+author=\{post\.author\}[\s\S]*?/>)', r'{null /* PostMeta hidden */}'),
    ]
    process_file(thread_item_post_path, regex_replacements=thread_post_replacements)

    # 27. Settings: Remove AddAccountRow from menu (already done via direct edit, but ensure idempotent)
    settings_path = p('src/screens/Settings/Settings.tsx')
    settings_regex = [
        (r'<AddAccountRow\s*/>', 'null // AddAccountRow removed'),
    ]
    process_file(settings_path, regex_replacements=settings_regex)

if __name__ == "__main__":
    main()
