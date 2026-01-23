import sys
import re
import os

def comment_out_regex(content, patterns):
    new_content = content
    for pattern_name, pattern_tuple in patterns:
        pattern = pattern_tuple[0]
        style = pattern_tuple[1]
        
        if style == 'jsx':
            full_pattern = r'(\{/\*\s*)?(' + pattern + r')(\s*\*/\})?'
        else: # js
            full_pattern = r'(/\*\s*)?(' + pattern + r')(\s*\*/)?'
        
        def replacement(match):
            prefix = match.group(1)
            content = match.group(2)
            suffix = match.group(3)
            
            if prefix:
                return match.group(0)
            
            if style == 'jsx':
                return f"{{/* {content} */}}"
            else:
                return f"/* {content} */"
        
        new_content = re.sub(full_pattern, replacement, new_content, flags=re.DOTALL)
    return new_content

def comment_out_indent(content, target_starts_with, matching_strings):
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if stripped.startswith('{/*'):
             new_lines.append(line)
             i += 1
             continue

        is_target_start = False
        for start_str in target_starts_with:
            if stripped.startswith(start_str):
                is_target_start = True
                break
        
        if is_target_start:
            # Check if already commented
            if i > 0 and lines[i-1].strip() == '{/*':
                new_lines.append(line)
                i += 1
                continue

            indent = len(line) - len(line.lstrip())
            j = i + 1
            block_content = [line]
            closed = False
            
            # Check if we're inside a conditional expression like {hasSession && (
            # by looking at the previous line
            inside_conditional = False
            conditional_start_line_idx = None
            if i > 0:
                prev_line = lines[i-1].strip()
                # Check for patterns like: {condition && (, {condition ? (
                if prev_line.endswith('(') and ('&&' in prev_line or '?' in prev_line):
                    inside_conditional = True
                    conditional_start_line_idx = i - 1
            
            if line.strip().endswith('/>'):
                 closed = True
                 should_comment = False
                 for target in matching_strings:
                     if target in line:
                         should_comment = True
                         break
                 if should_comment:
                     if inside_conditional:
                         # Comment out from the conditional start
                         # Pop the conditional line from new_lines and wrap everything
                         if new_lines and new_lines[-1] == lines[conditional_start_line_idx]:
                             cond_line = new_lines.pop()
                             cond_indent = len(cond_line) - len(cond_line.lstrip())
                             # Find closing )} on next lines
                             end_j = i + 1
                             while end_j < len(lines) and lines[end_j].strip() in [')', ')}',' )}']:
                                 end_j += 1
                             # Wrap the entire conditional
                             new_lines.append(f"{' ' * cond_indent}{{/* {cond_line.strip()}")
                             new_lines.append(line)
                             for k in range(i + 1, end_j):
                                 new_lines.append(lines[k])
                             new_lines.append(f"{' ' * cond_indent}*/}}")
                             i = end_j
                             continue
                     else:
                         new_lines.append(f"{' ' * indent}{{/*")
                         new_lines.append(line)
                         new_lines.append(f"{' ' * indent}*/}}")
                 else:
                     new_lines.append(line)
                 i += 1
                 continue

            while j < len(lines):
                sub_line = lines[j]
                sub_indent = len(sub_line) - len(sub_line.lstrip())
                block_content.append(sub_line)
                
                if sub_line.strip() == '/>' and sub_indent == indent:
                    closed = True
                    full_block = '\n'.join(block_content)
                    
                    should_comment = False
                    for target in matching_strings:
                        if target in full_block:
                            should_comment = True
                            break
                    
                    if should_comment:
                        if inside_conditional:
                            # Pop the conditional line and wrap everything
                            if new_lines and new_lines[-1] == lines[conditional_start_line_idx]:
                                cond_line = new_lines.pop()
                                cond_indent = len(cond_line) - len(cond_line.lstrip())
                                # Find closing )} after block
                                end_j = j + 1
                                while end_j < len(lines) and lines[end_j].strip() in [')', ')}', ' )}']:
                                    block_content.append(lines[end_j])
                                    end_j += 1
                                new_lines.append(f"{' ' * cond_indent}{{/* {cond_line.strip()}")
                                new_lines.extend(block_content)
                                new_lines.append(f"{' ' * cond_indent}*/}}")
                                i = end_j
                                break
                        else:
                            new_lines.append(f"{' ' * indent}{{/*")
                            new_lines.extend(block_content)
                            new_lines.append(f"{' ' * indent}*/}}")
                    else:
                        new_lines.extend(block_content)
                    
                    i = j + 1
                    break
                
                if sub_line.strip().startswith('</') and sub_line.strip().endswith('>') and sub_indent == indent:
                     closed = True
                     full_block = '\n'.join(block_content)
                     
                     should_comment = False
                     for target in matching_strings:
                        if target in full_block:
                            should_comment = True
                            break
                     if should_comment:
                        if inside_conditional:
                            # Pop the conditional line and wrap everything
                            if new_lines and new_lines[-1] == lines[conditional_start_line_idx]:
                                cond_line = new_lines.pop()
                                cond_indent = len(cond_line) - len(cond_line.lstrip())
                                # Find closing )} after block
                                end_j = j + 1
                                while end_j < len(lines) and lines[end_j].strip() in [')', ')}', ' )}']:
                                    block_content.append(lines[end_j])
                                    end_j += 1
                                new_lines.append(f"{' ' * cond_indent}{{/* {cond_line.strip()}")
                                new_lines.extend(block_content)
                                new_lines.append(f"{' ' * cond_indent}*/}}")
                                i = end_j
                                break
                        else:
                            new_lines.append(f"{' ' * indent}{{/*")
                            new_lines.extend(block_content)
                            new_lines.append(f"{' ' * indent}*/}}")
                     else:
                        new_lines.extend(block_content)
                     i = j + 1
                     break

                j += 1
            
            if not closed:
                new_lines.append(line)
                i += 1
        else:
            new_lines.append(line)
            i += 1
            
    return '\n'.join(new_lines)

def process_file(file_path, patterns=None, indent_config=None):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Reading {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    if patterns:
        new_content = comment_out_regex(new_content, patterns)
    
    if indent_config:
        new_content = comment_out_indent(new_content, indent_config[0], indent_config[1])

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Modified {file_path}")
    else:
        print(f"No changes for {file_path}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    def p(path): return os.path.join(base_dir, path)

    # 2. Drawer.tsx
    # Reverted SearchMenuItem
    drawer_start_tags = ['<ChatMenuItem', '<FeedsMenuItem', '<ListsMenuItem']
    drawer_targets = ['ChatMenuItem', 'FeedsMenuItem', 'ListsMenuItem']
    process_file(p('src/view/shell/Drawer.tsx'), indent_config=(drawer_start_tags, drawer_targets))

    # 3. PostMenuItems.tsx
    post_menu_start_tags = ['<Menu.Item']
    post_menu_targets = [
        'testID="postDropdownTranslateBtn"',
        'testID="postDropdownCopyTextBtn"',
        'testID="postDropdownShowMoreBtn"',
        'testID="postDropdownShowLessBtn"',
        'testID="postDropdownMuteThreadBtn"',
        'testID="postDropdownReportMisclassificationBtn"',
    ]
    process_file(p('src/components/PostControls/PostMenu/PostMenuItems.tsx'), indent_config=(post_menu_start_tags, post_menu_targets))

    # 4. ContentAndMediaSettings.tsx
    settings_patterns = [
        ("Manage Saved Feeds", (r'(<SettingsList\.LinkItem\s+[^>]*label=\{_\(msg`Manage saved feeds`\)\}.*?</SettingsList\.LinkItem>)', 'jsx')),
        ("Thread Preferences", (r'(<SettingsList\.LinkItem\s+[^>]*label=\{_\(msg`Thread preferences`\)\}.*?</SettingsList\.LinkItem>)', 'jsx')),
        ("Following Feed Preferences", (r'(<SettingsList\.LinkItem\s+[^>]*label=\{_\(msg`Following feed preferences`\)\}.*?</SettingsList\.LinkItem>)', 'jsx')),
        ("External Media", (r'(<SettingsList\.LinkItem\s+[^>]*label=\{_\(msg`External media`\)\}.*?</SettingsList\.LinkItem>)', 'jsx')),
    ]
    process_file(p('src/screens/Settings/ContentAndMediaSettings.tsx'), patterns=settings_patterns)

    # 5. ThreadItemAnchor.tsx
    thread_anchor_patterns = [
        ("Quotes Link", (r'(<Link\s+[^>]*to=\{quotesHref\}[^>]*label=\{_\(msg`Quotes of this post`\)\}.*?</Link>)', 'jsx')),
    ]
    process_file(p('src/screens/PostThread/components/ThreadItemAnchor.tsx'), patterns=thread_anchor_patterns)

    # 6. Profile.tsx
    profile_patterns = [
        ("Starter Packs Tab Title", (r'(showStarterPacksTab\s*\?\s*_\(msg`Starter Packs`\)\s*:\s*undefined,)', 'js')),
        ("Starter Packs Tab Content", (r'(\{showStarterPacksTab\s*\?\s*\(\{headerHeight,\s*isFocused,\s*scrollElRef\}\)\s*=>\s*\(\s*<ProfileStarterPacks.*?: null\})', 'jsx')),
        
        # New pattern additions for Feeds, Lists, Media
        ("Lists Tab Title 1", (r'(showListsTab && hasLabeler\s*\?\s*_\(msg`Lists`\)\s*:\s*undefined,)', 'js')),
        ("Lists Tab Title 2", (r'(showListsTab && !hasLabeler\s*\?\s*_\(msg`Lists`\)\s*:\s*undefined,)', 'js')),
        ("Media Tab Title", (r'(showMediaTab\s*\?\s*_\(msg`Media`\)\s*:\s*undefined,)', 'js')),
        ("Feeds Tab Title", (r'(showFeedsTab\s*\?\s*_\(msg`Feeds`\)\s*:\s*undefined,)', 'js')),
        
        ("Lists Tab Content 1", (r'(\{showListsTab && !!profile\.associated\?\.labeler\s*\?.*?: null\})', 'jsx')),
        ("Lists Tab Content 2", (r'(\{showListsTab && !profile\.associated\?\.labeler\s*\?.*?: null\})', 'jsx')),
        ("Media Tab Content", (r'(\{showMediaTab\s*\?\s*\(\{headerHeight,\s*isFocused,\s*scrollElRef\}\)\s*=>\s*\(\s*<ProfileFeedSection\s+ref=\{mediaSectionRef\}.*?: null\})', 'jsx')),
        ("Feeds Tab Content", (r'(\{showFeedsTab\s*\?\s*\(\{headerHeight,\s*isFocused,\s*scrollElRef\}\)\s*=>\s*\(\s*<ProfileFeedgens.*?: null\})', 'jsx')),
    ]
    process_file(p('src/view/screens/Profile.tsx'), patterns=profile_patterns)

    # 8. Desktop RightNav.tsx
    # Reverted Desktop Search
    right_nav_start_tags = ['<DesktopFeeds', '<SidebarTrendingTopics', '<ProgressGuideList']
    right_nav_targets = ['DesktopFeeds', 'SidebarTrendingTopics', 'ProgressGuideList']
    process_file(p('src/view/shell/desktop/RightNav.tsx'), indent_config=(right_nav_start_tags, right_nav_targets))

    # 9. ProfileMenu.tsx
    profile_menu_start_tags = ['<Menu.Item']
    profile_menu_targets = [
        'testID="profileHeaderDropdownStarterPackAddRemoveBtn"',
        'testID="profileHeaderDropdownListAddRemoveBtn"'
    ]
    process_file(p('src/view/com/profile/ProfileMenu.tsx'), indent_config=(profile_menu_start_tags, profile_menu_targets))

    # Indentation Based files
    
    # 1. BottomBar.tsx
    # Reverted bottomBarSearchBtn
    bottom_bar_targets = [
        'testID="bottomBarMessagesBtn"',
    ]
    process_file(p('src/view/shell/bottom-bar/BottomBar.tsx'), indent_config=(['<Btn'], bottom_bar_targets))

    # 7. Desktop LeftNav.tsx
    # Reverted href="/search"
    left_nav_start_tags = ['<NavItem', '<ChatNavItem']
    left_nav_targets = [
        '<ChatNavItem',
        'href="/feeds"',
        'href="/lists"',
    ]
    process_file(p('src/view/shell/desktop/LeftNav.tsx'), indent_config=(left_nav_start_tags, left_nav_targets))

    # 10. BottomBarWeb.tsx
    # Reverted routeName="Search"
    bottom_bar_web_start_tags = ['<NavItem']
    bottom_bar_web_targets = [
        'routeName="Messages"',
    ]
    process_file(p('src/view/shell/bottom-bar/BottomBarWeb.tsx'), indent_config=(bottom_bar_web_start_tags, bottom_bar_web_targets))

    # 11. Explore.tsx (Search Screen Content)
    explore_patterns = [
        ("Top Border", (r'(i\.push\(topBorder\))', 'js')),
        ("Interests Nux", (r'(i\.push\(\.\.\.interestsNuxModule\))', 'js')),
        ("Trending Topics", (r'(i\.push\(trendingTopicsModule\))', 'js')),
        ("Suggested Feeds", (r'(i\.push\(\.\.\.suggestedFeedsModule\))', 'js')),
        ("Suggested Follows", (r'(i\.push\(\.\.\.suggestedFollowsModule\))', 'js')),
        ("Suggested Follows (Simple)", (r'(i\.push\(\.\.\.suggestedFollowsModule\))', 'js')), # Duplicate handle? regex will catch all
        ("Suggested Starter Packs", (r'(i\.push\(\.\.\.suggestedStarterPacksModule\))', 'js')),
        ("Feed Previews", (r'(i\.push\(\.\.\.feedPreviewsModule\))', 'js')),
    ]
    # Note: re.sub replaces all occurrences by default, so 'Suggested Follows' covers both if-else branches 
    # if the string is identical.
    process_file(p('src/screens/Search/Explore.tsx'), patterns=explore_patterns)

    # 12. Menu Dividers (PostMenuItems.tsx and ProfileMenu.tsx)
    divider_patterns = [
        ("Menu Divider", (r'(<Menu\.Divider\s*/>)', 'jsx')),
    ]
    process_file(p('src/components/PostControls/PostMenu/PostMenuItems.tsx'), patterns=divider_patterns)
    process_file(p('src/view/com/profile/ProfileMenu.tsx'), patterns=divider_patterns)

    # 13. FeedInterstitials.tsx (Assign Topic for Algo)
    interstitials_patterns = [
        ("Progress Guide List", (r'(<ProgressGuideList\s*/>)', 'jsx')),
    ]
    process_file(p('src/components/FeedInterstitials.tsx'), patterns=interstitials_patterns)

    # 14. HomeHeaderLayoutMobile.tsx (Feed Hashtag Button)
    # Target the Link component with testID="viewHeaderHomeFeedPrefsBtn"
    # It has a closing </Link> tag, so we use indentation logic or regex if single line.
    # It spans multiple lines, so indentation logic is best, but let's try regex for start/end if possible.
    # Actually, indentation logic is safest for components.
    
    # We will use the indent_config approach.
    home_header_start_tags = ['<Link']
    home_header_targets = ['testID="viewHeaderHomeFeedPrefsBtn"']
    process_file(p('src/view/com/home/HomeHeaderLayoutMobile.tsx'), indent_config=(home_header_start_tags, home_header_targets))

    # 15. HomeHeaderLayout.web.tsx (Desktop Feed Hashtag Button)
    # Target the Link to /feeds
    home_header_web_start_tags = ['<Link']
    home_header_web_targets = ['to="/feeds"']
    process_file(p('src/view/com/home/HomeHeaderLayout.web.tsx'), indent_config=(home_header_web_start_tags, home_header_web_targets))

if __name__ == "__main__":
    main()
