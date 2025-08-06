from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import re
import random
import os

def clean_page_text(page_text):
    """
    Remove forum sections and comments from page text to avoid parsing interference
    """
    # Find section markers
    forums_start = page_text.find('Forums')
    more_matches_match = re.search(r'\.\.\. \d+ more matches', page_text)
    comments_start = page_text.find('COMMENTS:')
    
    filtered_text = page_text
    
    # Remove from "Forums" to "... X more matches" 
    if forums_start != -1 and more_matches_match:
        end_pos = more_matches_match.end()
        filtered_text = page_text[:forums_start] + page_text[end_pos:]
    elif forums_start != -1:
        # If no "more matches" found, just cut from Forums onward
        filtered_text = page_text[:forums_start]
    
    # Remove everything after COMMENTS: 
    comments_start = filtered_text.find('COMMENTS:')
    if comments_start != -1:
        filtered_text = filtered_text[:comments_start]
    
    return filtered_text




vct_teams = {
    "Sentinels": 2,
    "100 Thieves": 120,
    "Cloud9": 188,
    "NRG": 1034,
    "Evil Geniuses": 5248,
    "G2 Esports": 11058,
    "LOUD": 6961,
    "MIBR": 7386,
    "FURIA": 2406,
    "KRÜ Esports": 2355,
    "LEVIATÁN": 2359,
    "FNATIC": 2593,
    "Team Liquid": 474,
    "Team Heretics": 1001,
    "BBL Esports": 397,
    "FUT Esports": 1184,
    "Karmine Corp": 8877,
    "Team Vitality": 2059,
    "Natus Vincere": 4915,
    "Gentle Mates": 12694,
    "Apeks": 11479,
    "Paper Rex": 624,
    "DRX": 8185,
    "Gen.G": 17,
    "T1": 14,
    "Rex Regum Qeon": 878,
    "TALON": 8304,
    "Team Secret": 6199,
    "ZETA DIVISION": 5448,
    "DetonatioN FocusMe": 278,
    "Global Esports": 918,
    "EDward Gaming": 1120,
    "Bilibili Gaming": 12010,
    "FunPlus Phoenix": 628,
    "Dragon Ranger Gaming": 11981,
    "Wolves Esports": 13790,
    "Trace Esports": 12685,
    "Titan Esports Club": 14137,
    "Nova Esports": 12064,
    "All Gamers": 1119,
    "TYLOO": 731,
    "JDG Esports": 13576,
    "Rare Atom": 11985,
}




def setup_driver():
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

import re
import time
import pandas as pd
from selenium.webdriver.common.by import By

def get_team_matches(team_id, team_name, num_matches):
    driver = setup_driver()
    
    try:
        url = f"https://www.vlr.gg/team/matches/{team_id}/{team_name.lower()}/?group=completed"
        print(f"Getting matches for {team_name}...")
        
        driver.get(url)
        time.sleep(3)
        
        all_elements = driver.find_elements(By.CSS_SELECTOR, "*")
        matches = []
        seen_matches = set()
        
        # Precompile regexes once
        score_re = re.compile(r'\b\d+\s*:\s*\d+\b')
        date_re  = re.compile(r'\d{4}/\d{2}/\d{2}')
        
        for element in all_elements:
            try:
                text = element.text.strip()
                score_match = re.search(r'(\d+)\s*:\s*(\d+)', text)
                
                if score_match and 20 < len(text) < 500:
                    team_score = int(score_match.group(1))
                    opponent_score = int(score_match.group(2))
                    result = 'W' if team_score > opponent_score else 'L'
                    score = f"{team_score}:{opponent_score}"
                    
                    # Get match URL
                    match_url = None
                    try:
                        if element.tag_name == 'a':
                            match_url = element.get_attribute('href')
                        else:
                            link = element.find_element(By.TAG_NAME, 'a')
                            match_url = link.get_attribute('href')
                        if match_url and match_url.startswith('/'):
                            match_url = 'https://www.vlr.gg' + match_url
                    except:
                        pass
                    
                    match_key = (score, match_url) if match_url else (score, text[:50])
                    if match_key in seen_matches or not match_url:
                        continue
                    seen_matches.add(match_key)
                    
                    # Split into lines once
                    lines = text.split('\n')
                    
                    # --- Extract tournament name ---
                    tournament = 'Unknown'
                    # Find first hashtag line
                    first_hashtag_index = None
                    for i, line in enumerate(lines):
                        if line.strip().startswith('#'):
                            first_hashtag_index = i
                            break
                    
                    # Tournament name is ALWAYS 3 lines before the first hashtag
                    if first_hashtag_index is not None and first_hashtag_index >= 3:
                        tournament = lines[first_hashtag_index - 3].strip()
                    
                    # Pull out date line
                    match_date = None
                    for line in lines:
                        line = line.strip()
                        if date_re.match(line):
                            match_date = line
                            break
                    
                    # Existing opponent logic, now also skipping date lines
                    opponent = 'Unknown'
                    for line in lines[2:]:
                        line = line.strip()
                        if (
                            not line
                            or line.upper() == team_name.upper()
                            or line.startswith('#')
                            or score_re.match(line)
                            or date_re.match(line)
                            or (line.isdigit() and len(line) == 1)
                            or line == ':'
                        ):
                            continue
                        opponent = line
                        break

                    match_data = {
                        'team_id':     team_id,
                        'team_name':   team_name,
                        'match_number': len(matches) + 1,
                        'date':        match_date,
                        'result':      result,
                        'score':       score,
                        'opponent':    opponent,
                        'tournament':  tournament,
                        'match_url':   match_url
                    }
                    
                    matches.append(match_data)
                    print(f"  Match {len(matches)}: {match_date} {result} vs {opponent} ({score}) - {tournament}")
                    
                    if len(matches) >= num_matches:
                        break
                        
            except:
                continue
        
        return pd.DataFrame(matches)
        
    finally:
        driver.quit()


def get_match_complete_data(match_url, team_name, match_number, match_result):
    """
    Enhanced function to get players AND maps from a single match page visit
    """
    driver = setup_driver()
    
    try:
        print(f"  Getting complete data from: {match_url}")
        
        driver.get(match_url)
        time.sleep(3)
        
        # Get player data first (from overview/all maps)
        players_df = extract_player_data(driver, match_url, match_number)
        
        # Get map data
        maps_df = extract_map_data(driver, match_url, team_name, match_number, match_result)
        
        return players_df, maps_df
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return pd.DataFrame(), pd.DataFrame()
        
    finally:
        driver.quit()

def extract_player_data(driver, match_url, match_number):
    """
    Extract player ratings (simplified without W/L logic)
    """
    try:
        # Get and clean page text
        raw_page_text = driver.find_element(By.TAG_NAME, 'body').text
        page_text = clean_page_text(raw_page_text)
        
    
        # Find where forums end (look for "... X more matches")
        more_matches = re.search(r'\.\.\. \d+ more matches', page_text)
        
        match_start = 0
        if more_matches:
            match_start = more_matches.end()
        
        # Find where comments start
        comments_start = page_text.find('COMMENTS:')
        
        # Extract only the match section
        if comments_start != -1:
            page_text = page_text[match_start:comments_start]
        else:
            page_text = page_text[match_start:]
        
        lines = page_text.split('\n')
        
        players = []
        
        # Looking for rating lines and extract player info
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for rating lines that start with decimal
            if re.match(r'^(0\.\d{2}|1\.\d{2}|2\.\d{2})', line):
                rating = float(line.split()[0])
                
                # Player name is 2 lines before, team is 1 line before
                if i >= 2:
                    player_name = lines[i - 2].strip()
                    team_name = lines[i - 1].strip()
                    
                    # Basic validation
                    if (2 <= len(player_name) <= 20 and 
                        2 <= len(team_name) <= 10 and
                        team_name.isupper()):
                        
                        players.append({
                            'player_name': player_name,
                            'team': team_name,
                            'rating': rating,
                            'match_number': match_number,  
                            'match_url': match_url
                        })
                        print(f"    {player_name} ({team_name}): {rating}")
        
        print(f"  Found {len(players)} players")
        return pd.DataFrame(players)
    
    except Exception as e:
        print(f"  Error extracting player data: {e}")
        return pd.DataFrame()

def extract_map_data(driver, match_url, team_name, match_number, match_result):
    """
    Extract map results - handles both multi-map and single-map matches
    Only processes maps that were actually played based on overall score
    """
    maps_data = []
    
    try:
        print(f"  Extracting map data for {team_name}...")
        
        # First, determine how many maps were actually played from overall score
        maps_played = get_maps_actually_played(driver, match_url)
        print(f"  Maps actually played: {maps_played}")
        
        # Find map navigation buttons
        map_buttons = driver.find_elements(By.CSS_SELECTOR, ".vm-stats-gamesnav-item.js-map-switch")
        print(f"  Found {len(map_buttons)} map navigation items")
        
        # Check if this is a single map match (no numbered maps)
        numbered_maps = [b for b in map_buttons if not ('mod-all' in b.get_attribute('class'))]
        
        if len(numbered_maps) == 0:
            print(f"  Single map match detected - extracting from overview")
            # This is a single map match, extract from the overview/all maps section
            single_map_data = extract_single_map_data(driver, match_url, team_name, match_number, match_result)
            if single_map_data:
                maps_data.append(single_map_data)
        else:
            # Multi-map match - process each map that was actually played
            maps_processed = 0
            
            for i, button in enumerate(map_buttons):
                button_classes = button.get_attribute('class')
                if 'mod-all' in button_classes:
                    print(f"  Skipping 'All Maps' button")
                    continue
                    
                # Get map info from button text
                button_text = button.text.strip()
                clean_text = ' '.join(button_text.split())
                parts = clean_text.split(' ', 1)
                
                if len(parts) >= 2 and parts[0].isdigit():
                    map_number = int(parts[0])
                    map_name = parts[1]
                    
                    # Only process maps that were actually played
                    if map_number <= maps_played:
                        print(f"  Processing Map {map_number}: {map_name}")
                        
                        
                        try:
                            button.click()
                            time.sleep(2)
                            
                            # Get result AND scores for target team
                            result, our_score, their_score = get_map_result_from_page(driver, team_name)
                            print(f"    {team_name} result on {map_name}: {result} ({our_score}-{their_score})")
                            
                            maps_data.append({
                                'team_name': team_name,
                                'match_number': match_number,
                                'overall_match_result': match_result,
                                'map_number': map_number,
                                'map_name': map_name,
                                'map_result': result,
                                'our_score': our_score,
                                'their_score': their_score,
                                'map_score': f"{our_score}-{their_score}" if our_score is not None else None,
                                'match_url': match_url
                            })
                            
                            maps_processed += 1
                            
                        except Exception as e:
                            print(f"    Error processing map {map_number}: {e}")
                    else:
                        print(f"  Skipping Map {map_number}: {map_name} (not played - series ended {maps_played} maps)")
        
        print(f"  Found {len(maps_data)} maps that were actually played")
        return pd.DataFrame(maps_data)
        
    except Exception as e:
        print(f"  Error extracting maps: {e}")
        return pd.DataFrame()












def get_maps_actually_played(driver, match_url):
    """
    Determine how many maps were actually played based on the overall score
    """
    try:
        # Method 1: Target the specific .match-header-vs element
        try:
            vs_element = driver.find_element(By.CSS_SELECTOR, '.match-header-vs')
            vs_text = vs_element.text
            print(f"    Found .match-header-vs text: {vs_text}")
            
            # Extract score from format like "FNATIC[2110]final2:0vs.Bo3Karmine Corp[1765]"
            score_match = re.search(r'final\s*(\d+)\s*:\s*(\d+)\s*vs', vs_text)
            if score_match:
                score1, score2 = int(score_match.group(1)), int(score_match.group(2))
                total_maps = score1 + score2
                if is_valid_match_score(score1, score2):
                    print(f"    Found overall score: {score1}:{score2} (total maps: {total_maps})")
                    return total_maps
        except Exception as e:
            print(f"    Could not find .match-header-vs element: {e}")
        
        # Method 2: Look for score in .match-header element(I dont even think I used method 1 I think I just use this one)
        try:
            header_element = driver.find_element(By.CSS_SELECTOR, '.match-header')
            header_text = header_element.text
            
            # Look for "final X:Y vs" pattern in header
            score_match = re.search(r'final\s*(\d+)\s*:\s*(\d+)\s*vs', header_text)
            if score_match:
                score1, score2 = int(score_match.group(1)), int(score_match.group(2))
                total_maps = score1 + score2
                if is_valid_match_score(score1, score2):
                    print(f"    Found overall score in header: {score1}:{score2} (total maps: {total_maps})")
                    return total_maps
        except Exception as e:
            print(f"    Could not find .match-header element: {e}")
        
        # Method 3: Search page source for the pattern (before falling back to body text)
        try:
            page_source = driver.page_source
            # Look for the "final X:Y vs" pattern identified
            score_match = re.search(r'final\s*(\d+)\s*:\s*(\d+)\s*vs', page_source)
            if score_match:
                score1, score2 = int(score_match.group(1)), int(score_match.group(2))
                total_maps = score1 + score2
                if is_valid_match_score(score1, score2):
                    print(f"    Found overall score in page source: {score1}:{score2} (total maps: {total_maps})")
                    return total_maps
        except Exception as e:
            print(f"    Error searching page source: {e}")
        
        # Method 4: Fallback - look in body text but avoid comments section
        try:
            raw_body_text = driver.find_element(By.TAG_NAME, 'body').text
            body_text = clean_page_text(raw_body_text)
            
            # Find where comments start and exclude that section (case insensitive)
            comments_start = body_text.lower().find('comments')
            if comments_start != -1:
                pre_comments_text = body_text[:comments_start]
            else:
                pre_comments_text = body_text
            
            # Look for valid match scores in the non-comment section
            score_patterns = re.findall(r'(\d)\s*:\s*(\d)(?!\d)(?!\s*[AP]M)', pre_comments_text)
            for score_match in score_patterns:
                score1, score2 = int(score_match[0]), int(score_match[1])
                total_maps = score1 + score2
                if is_valid_match_score(score1, score2):
                    print(f"    Found overall score in body: {score1}:{score2} (total maps: {total_maps})")
                    return total_maps
        except Exception as e:
            print(f"    Error searching body text: {e}")
        
        # Method 5: Last resort - check title
        try:
            title = driver.title
            score_in_title = re.search(r'(\d+)\s*[:-]\s*(\d+)', title)
            if score_in_title:
                score1, score2 = int(score_in_title.group(1)), int(score_in_title.group(2))
                total_maps = score1 + score2
                if is_valid_match_score(score1, score2):
                    print(f"    Found score in title: {score1}:{score2} (total maps: {total_maps})")
                    return total_maps
        except Exception as e:
            print(f"    Error checking title: {e}")
        
        # If we can't determine, assume all available maps were played
        print(f"    Could not determine maps played, assuming all maps were played")
        return 5  # Max possible in a BO5
        
    except Exception as e:
        print(f"    Error determining maps played: {e}")
        return 5  # Safe default

def is_valid_match_score(score1, score2):
    """
    Check if a score looks like a valid Valorant match score
    """
    total_maps = score1 + score2
    max_score = max(score1, score2)
    
    # Valorant match constraints:
    # - Total maps: 1-5 (BO1, BO3, BO5)
    # - Max score for winner: 1-3 
    # - Both scores should be reasonable (not round scores like 13:11)
    return (
        1 <= total_maps <= 5 and      # Valid total maps
        1 <= max_score <= 3 and       # Valid max score for winner  
        score1 <= 3 and score2 <= 3   # Both scores reasonable
    )

def extract_single_map_data(driver, match_url, team_name, match_number, match_result):
    """
    Extract map data for single-map matches (like 1:0 scores)
    Now also extracts scores when possible
    """
    try:
        print(f"    Extracting single map data...")
        
        # Get and clean page text
        raw_page_text = driver.find_element(By.TAG_NAME, 'body').text
        page_text = clean_page_text(raw_page_text)


        # Find where forums end (look for "... X more matches") (for comment exclusion)
        more_matches = re.search(r'\.\.\. \d+ more matches', page_text)
        
        match_start = 0
        if more_matches:
            match_start = more_matches.end()
        
        # Find where comments start
        comments_start = page_text.find('COMMENTS:')
        
        # Extract only the match section
        if comments_start != -1:
            page_text = page_text[match_start:comments_start]
        else:
            page_text = page_text[match_start:]
        
        # Try to get the actual map scores for single map matches
        result, our_score, their_score = get_map_result_from_page(driver, team_name)
        
        # Strategy 1: Look for "X remains" pattern (most reliable for single maps)
        remains_match = re.search(r'(\w+)\s+remains', page_text, re.IGNORECASE)
        if remains_match:
            found_map = remains_match.group(1).capitalize()
            print(f"    Found map from 'remains' pattern: {found_map}")
            
            # Validate it's a real Valorant map
            map_names = ['ascent', 'bind', 'haven', 'icebox', 'lotus', 'sunset', 'split', 
                         'breeze', 'fracture', 'pearl', 'dust2', 'abyss',
                         'corrode'] #screw corrode
            
            if found_map.lower() in map_names:
                return {
                    'team_name': team_name,
                    'match_number': match_number,
                    'overall_match_result': match_result,
                    'map_number': 1,
                    'map_name': found_map,
                    'map_result': result if result != 'Unknown' else match_result,
                    'our_score': our_score,
                    'their_score': their_score,
                    'map_score': f"{our_score}-{their_score}" if our_score is not None else None,
                    'match_url': match_url
                }
        
        # Strategy 2: Look for pick/ban phase and find the final map
        ban_phase_match = re.search(r'ban\s+\w+.*?(\w+)\s+remains', page_text, re.IGNORECASE | re.DOTALL)
        if ban_phase_match:
            found_map = ban_phase_match.group(1).capitalize()
            print(f"    Found map from ban phase: {found_map}")
            
            map_names = ['ascent', 'bind', 'haven', 'icebox', 'lotus', 'sunset', 'split', 
                         'breeze', 'fracture', 'pearl', 'dust2', 'abyss', 'corrode']

            if found_map.lower() in map_names:
                return {
                    'team_name': team_name,
                    'match_number': match_number,
                    'overall_match_result': match_result,
                    'map_number': 1,
                    'map_name': found_map,
                    'map_result': result if result != 'Unknown' else match_result,
                    'our_score': our_score,
                    'their_score': their_score,
                    'map_score': f"{our_score}-{their_score}" if our_score is not None else None,
                    'match_url': match_url
                }
        
        # Strategy 3: Look for map in page title
        title = driver.title.lower()
        map_names = ['ascent', 'bind', 'haven', 'icebox', 'lotus', 'sunset', 'split', 
                     'breeze', 'fracture', 'pearl', 'dust2','abyss', 'corrode']
        
        for map_name in map_names:
            if map_name in title:
                found_map = map_name.capitalize()
                print(f"    Found map in title: {found_map}")
                return {
                    'team_name': team_name,
                    'match_number': match_number,
                    'overall_match_result': match_result,
                    'map_number': 1,
                    'map_name': found_map,
                    'map_result': result if result != 'Unknown' else match_result,
                    'our_score': our_score,
                    'their_score': their_score,
                    'map_score': f"{our_score}-{their_score}" if our_score is not None else None,
                    'match_url': match_url
                }
        
        # Strategy 4: Fallback - search page text but be more careful
        for map_name in map_names:
            # Look for map name with word boundaries
            pattern = r'\b' + map_name + r'\b'
            if re.search(pattern, page_text, re.IGNORECASE):
                # Additional check: make sure it's not in a ban context
                context_match = re.search(r'.{0,20}\b' + map_name + r'\b.{0,20}', page_text, re.IGNORECASE)
                if context_match and 'ban' not in context_match.group().lower():
                    found_map = map_name.capitalize()
                    print(f"    Found map in page text (verified): {found_map}")
                    return {
                        'team_name': team_name,
                        'match_number': match_number,
                        'overall_match_result': match_result,
                        'map_number': 1,
                        'map_name': found_map,
                        'map_result': result if result != 'Unknown' else match_result,
                        'our_score': our_score,
                        'their_score': their_score,
                        'map_score': f"{our_score}-{their_score}" if our_score is not None else None,
                        'match_url': match_url
                    }
        
        # If all else fails
        print(f"    Could not determine map name, using 'Unknown'")
        return {
            'team_name': team_name,
            'match_number': match_number,
            'overall_match_result': match_result,
            'map_number': 1,
            'map_name': 'Unknown',
            'map_result': result if result != 'Unknown' else match_result,
            'our_score': our_score,
            'their_score': their_score,
            'map_score': f"{our_score}-{their_score}" if our_score is not None else None,
            'match_url': match_url
        }
        
    except Exception as e:
        print(f"    Error extracting single map: {e}")
        return None


def get_map_result_from_page(driver, target_team_name):
    """
    Extract win/loss result AND scores for target team from current map page
    Returns: (result, our_score, their_score) or ('Unknown', None, None)
    """
    try:
        print(f"    Looking for {target_team_name} result...")
        
        # Get and clean page text
        raw_page_text = driver.find_element(By.TAG_NAME, 'body').text
        page_text = clean_page_text(raw_page_text)
        
        # EXCLUDE COMMENTS SECTION (just like in get_maps_actually_played)
        comments_start = page_text.lower().find('comments')
        if comments_start != -1:
            page_text = page_text[:comments_start]
        
        lines = page_text.split('\n')
        
        # Valorant map names
        map_names = ['ascent', 'bind', 'haven', 'icebox', 'lotus', 'sunset', 'split', 
                     'breeze', 'fracture', 'pearl', 'dust2', 'abyss',
                     'corrode']
        
        # Look for map names and analyze surrounding context
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Check if this line contains a map name
            for map_name in map_names:
                if line_lower == map_name or (map_name in line_lower and len(line_lower) < 20):
                    print(f"    Found map line: '{line}' at index {i}")
                    
                    # Look for the score pattern in surrounding lines
                    # Pattern: Score, Team Name, A/D, Map, (PICK), Time, Team Name, A/D, Score
                    
                    # Check lines before the map (typically 1-3 lines)
                    team1_score = None
                    team1_name = None
                    
                    for j in range(max(0, i-4), i):
                        prev_line = lines[j].strip()
                        
                        # Check if it's a score (single number 0-25 for overtime)
                        if prev_line.isdigit() and 0 <= int(prev_line) <= 25:
                            team1_score = int(prev_line)
                            # Team name should be right after the score
                            if j+1 < i and not lines[j+1].strip().isdigit():
                                potential_team = lines[j+1].strip()
                                # Validate it's a team name (not A/D pattern)
                                if not re.match(r'^\d+\s*/\s*\d+$', potential_team):
                                    team1_name = potential_team
                            break
                    
                    # Check lines after the map
                    team2_score = None
                    team2_name = None
                    
                    # Skip "PICK" line if present
                    start_idx = i + 1
                    if i+1 < len(lines) and lines[i+1].strip().upper() == 'PICK':
                        start_idx = i + 2
                    
                    # Skip time line (format: MM:SS or HH:MM:SS)
                    if start_idx < len(lines) and re.match(r'^\d+:\d+(:\d+)?$', lines[start_idx].strip()):
                        start_idx += 1
                    
                    # Now look for team2 info
                    for j in range(start_idx, min(len(lines), start_idx + 4)):
                        current_line = lines[j].strip()
                        
                        # First non-time line should be team name
                        if team2_name is None and current_line and not current_line.isdigit():
                            # Check if it's not A/D pattern
                            if not re.match(r'^\d+\s*/\s*\d+$', current_line):
                                team2_name = current_line
                        
                        # Look for score after team name
                        elif team2_name and current_line.isdigit() and 0 <= int(current_line) <= 25:
                            team2_score = int(current_line)
                            break
                    
                    # If we found both scores and at least one team name
                    if team1_score is not None and team2_score is not None:
                        print(f"    Found scores - Team1: {team1_name} ({team1_score}) vs Team2: {team2_name} ({team2_score})")
                        
                        # Determine which score belongs to our target team
                        if team1_name and target_team_name.lower() in team1_name.lower():
                            our_score, their_score = team1_score, team2_score
                        elif team2_name and target_team_name.lower() in team2_name.lower():
                            our_score, their_score = team2_score, team1_score
                        else:
                            # If we can't match names exactly, look in broader context
                            context_start = max(0, i-10)
                            context_end = min(len(lines), i+10)
                            context = ' '.join(lines[context_start:context_end])
                            
                            # Find which position our team appears more prominently
                            team_mentions_before = context[:context.find(map_name)].lower().count(target_team_name.lower())
                            team_mentions_after = context[context.find(map_name):].lower().count(target_team_name.lower())
                            
                            if team_mentions_before > team_mentions_after:
                                our_score, their_score = team1_score, team2_score
                            else:
                                our_score, their_score = team2_score, team1_score
                        
                        result = 'W' if our_score > their_score else 'L'
                        print(f"    {target_team_name} scored {our_score} vs opponent's {their_score}")
                        return result, our_score, their_score
        
        print(f"    Could not determine result for {target_team_name}")
        return 'Unknown', None, None
        
    except Exception as e:
        print(f"    Error getting map result: {e}")
        return 'Unknown', None, None
    
def extract_score_from_team_element(team_element, target_team_name):
    """
    Extract score from a team-specific element
    """
    try:
        # Look for score patterns within this team element
        element_text = team_element.text.strip()
        
        # Look for patterns like "Team Name 13" or "13 Team Name"
        # First, find where the team name is
        team_pos = element_text.lower().find(target_team_name.lower())
        
        if team_pos != -1:
            # Look for numbers near the team name (within 20 characters)
            nearby_text = element_text[max(0, team_pos-20):team_pos+len(target_team_name)+20]
            
            # Find all numbers in the nearby text
            numbers = re.findall(r'\b(\d{1,2})\b', nearby_text)
            
            # Filter to valid Valorant scores
            valid_scores = [int(n) for n in numbers if 0 <= int(n) <= 15]
            
            if len(valid_scores) >= 1:
                our_score = valid_scores[0]  # Take the first valid score near team name
                
                # Now find the opponent's score
                # Look for other team elements or score elements
                parent = team_element.find_element(By.XPATH, "..")
                parent_text = parent.text.strip()
                
                # Find all valid scores in parent
                all_scores = re.findall(r'\b(\d{1,2})\b', parent_text)
                all_valid_scores = [int(n) for n in all_scores if 0 <= int(n) <= 15]
                
                # Remove our score and take the next one as opponent's
                remaining_scores = [s for s in all_valid_scores if s != our_score]
                
                if remaining_scores:
                    their_score = remaining_scores[0]
                    print(f"    Team element analysis: {target_team_name} {our_score} - {their_score} opponent")
                    return 'W' if our_score > their_score else 'L'
        
        return 'Unknown'
        
    except Exception as e:
        print(f"    Error extracting from team element: {e}")
        return 'Unknown'

def parse_match_score_structure(driver, target_team_name):
    """
    Parse the overall match score structure to find the current map result
    """
    try:
        # Get and clean page text
        raw_page_text = driver.find_element(By.TAG_NAME, 'body').text
        page_text = clean_page_text(raw_page_text)
        
        # BETTER COMMENT EXCLUSION - exclude forums AND comments
        # Find where forums end (look for "... X more matches")
        more_matches = re.search(r'\.\.\. \d+ more matches', page_text)
        
        match_start = 0
        if more_matches:
            match_start = more_matches.end()
        
        # Find where comments start
        comments_start = page_text.find('COMMENTS:')
        
        # Extract only the match section
        if comments_start != -1:
            filtered_page_text = page_text[match_start:comments_start]
        else:
            filtered_page_text = page_text[match_start:]
        
        # Look for the match header or score display area
        header_selectors = [
            ".match-header",
            ".vm-stats-game",
            ".match-header-vs",
            "[class*='match-score']"
        ]
        
        for selector in header_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            
            for element in elements:
                try:
                    element_text = element.text.strip()
                    
                    # Use our filtered page text instead of element text for consistency
                    # Look for team names and scores in structured format
                    lines = filtered_page_text.split('\n')
                    
                    for i, line in enumerate(lines):
                        if target_team_name.lower() in line.lower():
                            # Look in current line and surrounding lines for scores
                            context_lines = lines[max(0, i-1):i+2]
                            
                            for context_line in context_lines:
                                # Look for isolated scores (not timestamps)
                                score_matches = re.findall(r'\b(\d{1,2})\s*[:\-]\s*(\d{1,2})\b', context_line)
                                
                                for score_match in score_matches:
                                    score1, score2 = int(score_match[0]), int(score_match[1])
                                    
                                    # Validate Valorant scores and exclude timestamps
                                    if (0 <= score1 <= 25 and 0 <= score2 <= 25 and 
                                        not (score1 > 30 or score2 > 30)):  # Exclude timestamps like 55:43
                                        
                                        # Determine which is ours based on team position in line
                                        team_pos = line.lower().find(target_team_name.lower())
                                        score_pos = context_line.find(f"{score1}:{score2}")
                                        if score_pos == -1:
                                            score_pos = context_line.find(f"{score1}-{score2}")
                                        
                                        if team_pos < score_pos:
                                            our_score, their_score = score1, score2
                                        else:
                                            our_score, their_score = score2, score1
                                        
                                        print(f"    Structure analysis: {target_team_name} {our_score} - {their_score} opponent")
                                        return 'W' if our_score > their_score else 'L'
                
                except Exception as e:
                    continue
        
        return 'Unknown'
        
    except Exception as e:
        print(f"    Error in structure parsing: {e}")
        return 'Unknown'



def scrape_team_data(team_id, team_name, num_matches):
    print(f"\nScraping {team_name}...")
    
    # Get matches
    matches_df = get_team_matches(team_id, team_name, num_matches)
    
    if matches_df.empty:
        print(f"No matches found for {team_name}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # Get complete data for each match (players + maps)
    all_players = []
    all_maps = []
    
    for _, match in matches_df.iterrows():
        if match['match_url']:
            print(f"Match {match['match_number']}: {match['result']} vs {match['opponent']} ({match['score']})")
            
            players_df, maps_df = get_match_complete_data(
                match['match_url'], 
                team_name, 
                match['match_number'], 
                match['result']
            )
            
            if not players_df.empty:
                all_players.append(players_df)
            
            if not maps_df.empty:
                all_maps.append(maps_df)
            
            # Respectful delay
            time.sleep(random.randint(1, 3))
    
    players_df = pd.concat(all_players, ignore_index=True) if all_players else pd.DataFrame()
    maps_df = pd.concat(all_maps, ignore_index=True) if all_maps else pd.DataFrame()
    
    return matches_df, players_df, maps_df

if __name__ == "__main__":
    # Configuration
    num_matches = 50  # Number of matches per team

    # Create directory structure once
    matches_dir = '../data/raw/vlr_data/matches'
    players_dir = '../data/raw/vlr_data/players'
    maps_dir = '../data/raw/vlr_data/maps'
    
    os.makedirs(matches_dir, exist_ok=True)
    os.makedirs(players_dir, exist_ok=True)
    os.makedirs(maps_dir, exist_ok=True)
    
    print(f"Starting scraping for {len(vct_teams)} teams...")
    successful_teams = 0
    failed_teams = []
    
    # Loop through all teams, yes I copy pasted from claude idgaf
    for team_name, team_id in vct_teams.items():
        try:
            print(f"\n{'='*60}")
            print(f"SCRAPING TEAM {successful_teams + 1}/{len(vct_teams)}: {team_name}")
            print(f"{'='*60}")
            
            matches_df, players_df, maps_df = scrape_team_data(team_id, team_name, num_matches)
            
            print(f"\nResults for {team_name}:")
            print(f"Matches: {len(matches_df)}")
            print(f"Player records: {len(players_df)}")
            print(f"Map records: {len(maps_df)}")
            
            # Save data with team-specific filenames
            if not matches_df.empty:
                matches_file = f'{matches_dir}/{team_name.upper()}_matches.csv'
                matches_df.to_csv(matches_file, index=False)
                print(f"Saved {len(matches_df)} matches to {matches_file}")
            
            if not players_df.empty:
                players_file = f'{players_dir}/{team_name.upper()}_players.csv'
                players_df.to_csv(players_file, index=False)
                print(f"Saved {len(players_df)} player records to {players_file}")
            
            if not maps_df.empty:
                maps_file = f'{maps_dir}/{team_name.upper()}_maps.csv'
                maps_df.to_csv(maps_file, index=False)
                print(f"Saved {len(maps_df)} map records to {maps_file}")

            successful_teams += 1
            
            # Brief delay between teams
            if team_name != list(vct_teams.keys())[-1]:  # Don't delay after last team
                delay = random.randint(2, 4)  # 2-4 seconds between teams
                print(f"⏳ Waiting {delay} seconds before next team...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"FAILED to scrape {team_name}: {str(e)}")
            failed_teams.append((team_name, str(e)))
            continue
    
    # Final summary
    print(f"\n{'='*60}")
    print("SCRAPING COMPLETE!")
    print(f"{'='*60}")
    print(f"Successfully scraped: {successful_teams}/{len(vct_teams)} teams")
    print(f"Failed: {len(failed_teams)} teams")
    
    if failed_teams:
        print("\nFailed teams:")
        for team, error in failed_teams:
            print(f"  - {team}: {error}")
    
    print(f"\nAll CSV files saved to:")
    print(f"  - Matches: {matches_dir}")
    print(f"  - Players: {players_dir}")
    print(f"  - Maps: {maps_dir}")