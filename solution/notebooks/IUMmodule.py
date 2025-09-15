import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import self
from pandas import value_counts
from collections import defaultdict
from pandas.tseries.offsets import DateOffset
from fuzzywuzzy import fuzz
from num2words import num2words
import recordlinkage
import textdistance

plt.style.use('ggplot')

grade_mapping = {
    'A+': '5.0/5',
    'A': '5.0/5',
    'A-': '4.7/5',
    'B+': '4.3/5',
    'B': '4.0/5',
    'B-': '3.7/5',
    'C+': '3.3/5',
    'C': '3.0/5',
    'C-': '2.7/5',
    'D+': '2.3/5',
    'D': '2.0/5',
    'D-': '1.7/5',
    'F': '1.0/5',
    'F+': '1.3/5',
    'F-': '0.7/5'
}

# Checks if the score is a letter grade (A+, A-, B+, etc.)
# If the match is true, returns the correspondig score
# otherwise it returns the original pattern
def convert_grade_to_5_scale(score):
    score = re.sub(r'\s+', '', str(score))  # Ignores all the spaces
    if score in grade_mapping:
        return grade_mapping[score]  
    return score  

# Checks the score format and converts it into a /5 format
# Case 1:
#   If there is a "/", it treats it like a fraction, grouping the denominator and the numerator
# Case 2:
#   If it's an integer value
def normalize_review_score(review):
    if pd.isna(review):
        return review

    # Case 1: Match fraction format
    if '/' in review:
        match = re.match(r'(\d+(\.\d+)?)/(\d+)', review)
        if match:
            numerator = float(match.group(1))
            denominator = match.group(3)

            if denominator == '0':
                return np.nan

            try:
                denominator = float(denominator)
                if (numerator > denominator) & (denominator == 10):
                    # Convert to /100 scale
                    denominator = 100
                if numerator > denominator:
                    return np.nan
                score = (numerator / denominator) * 5
                return f'{round(score, 2)}/5'  # Limit to 2 decimal places
            except ZeroDivisionError:
                return np.nan

    # Case 2: Match integer values
    match = re.match(r'^\d+$', review)
    if match:
        number = int(review)
        if number < 10:
            # Treat as /10 scale
            return f'{round((number / 10) * 5, 2)}/5'
        elif number > 100:
            # Treat as a typo (divide by 10) and convert to /5 scale
            return f'{round((number / 10 / 100) * 5, 2)}/5'
        else:
            # Treat as /100 scale
            return f'{round((number / 100) * 5, 2)}/5'

    return np.nan  # Return the original if it doesn't match any format



def standardazing_age_ratings(rating):
    # If the rating is NaN, return 'Unrated'
    if pd.isna(rating):
        return 'Unrated'
    
    if rating == 'U':
        return 'G'
    
    if rating == 'R':
        return '18+'
    
    if rating == 'PG':
        return '12+'
    
    match = re.search(r'(\d+)', rating)  # Find the first number in the string
    if match:
        num = int(match.group(1))  # Extract the number
        
        # Based on the number, return the appropriate rating
        if num >= 18:
            return '18+'
        elif num == 17:
            return '17+'
        elif num == 16:
            return '16+'
        elif num == 15:
            return '15+'
        elif num == 14:
            return '14+'
        elif num == 13:
            return '13+' 
        elif num == 12:
            return '12+'
        elif num == 11:
            return '11+'
        elif num == 10:
            return '10+'
        else:
            return 'Unrated'
    else:
        # No number is found
        return 'Unrated'
    
def convert_to_float(review):
    if isinstance(review, str) and '/' in review:
        match = re.match(r'(\d+(\.\d+)?)/(\d+)', review)
        if match:
            return float(match.group(1)) # numerator

def normalize_title(title):
    return re.sub(r'[^\w\s]', '', str(title).lower()).strip()

def build_lookup_structures(df_movies, df_oscars):
    # anni degli oscar
    oscar_years = df_oscars['year_film'].unique()

    year_movies = df_movies[
        df_movies['date'].dt.year.isin(oscar_years) &
        df_movies['name'].notna()
    ].copy()

    title_to_id = dict(zip(year_movies['name'], year_movies['id']))
    norm_title_to_id = {}
    for title, movie_id in title_to_id.items():
        norm_title_to_id[normalize_title(title)] = movie_id

    year_to_titles = defaultdict(list)
    for _, row in year_movies.iterrows():
        year = row['date'].year
        norm_title = normalize_title(row['name'])
        year_to_titles[year].append((norm_title, row['id']))

    return title_to_id, norm_title_to_id, year_to_titles

def find_matching_movie(oscar_title, oscar_year, title_to_id, norm_title_to_id, year_to_titles):
    if oscar_title in title_to_id:
        return title_to_id[oscar_title]

    normalized = normalize_title(oscar_title)
    if normalized in norm_title_to_id:
        return norm_title_to_id[normalized]

    start_year = pd.Timestamp(oscar_year) - DateOffset(years=3)
    end_year = pd.Timestamp(oscar_year) + DateOffset(years=4)

    candidate_titles = []
    for year, titles in year_to_titles.items():
        year_date = pd.Timestamp(year=year, month=1, day=1)
        if start_year <= year_date <= end_year:
            candidate_titles.extend(titles)

    best_match = None
    best_score = 0
    for title, movie_id in candidate_titles:
        score = max(
            fuzz.token_set_ratio(oscar_title, title),
            fuzz.token_set_ratio(normalized, title)
        )
        if score > best_score:
            best_score = score
            best_match = movie_id

    return best_match if best_score > 85 else None

REPLACEMENTS = {
    "&": "and",
    "'": "",
    "’": "",
}

def normalize_text(text):
    text = text.lower()
    text = replace_numbers_with_words(text)
    for k, v in REPLACEMENTS.items():
        text = text.replace(k, v)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def replace_numbers_with_words(text):
    def convert(match):
        number = int(match.group())
        if number < 100:
            return num2words(number)
        return match.group()
    return re.sub(r'\b\d+\b', convert, text)

def clean_title_for_matching(title):
    if pd.isna(title):
        return []
    title = title.strip()
    parts = re.split(r'\s*\(|\)\s*', title)
    parts = [normalize_text(p) for p in parts if p.strip()]
    normalized_full_title = normalize_text(title)
    if normalized_full_title not in parts:
        parts.append(normalized_full_title)
    return list(set(parts))

def generate_blocking_keys(df, title_col, candidates_col='title_candidates', blocking_col='blocking_key'):
    df[candidates_col] = df[title_col].apply(clean_title_for_matching)
    df[blocking_col] = df[candidates_col].apply(lambda x: x[0] if x else "")
    return df

def perform_recordlinkage(df_left, df_right, left_block='blocking_key', right_block='blocking_key', threshold=0.85):
    indexer = recordlinkage.Index()
    indexer.block(left_on=left_block, right_on=right_block)
    pairs = indexer.index(df_left, df_right)

    matches = []
    for idx_left, idx_right in pairs:
        left_row = df_left.loc[idx_left]
        right_row = df_right.loc[idx_right]

        for lt in left_row['title_candidates']:
            for rt in right_row['name_candidates']:
                score = textdistance.levenshtein.normalized_similarity(lt, rt)
                if score >= threshold:
                    matches.append((idx_left, right_row['id']))
                    break
            else:
                continue
            break

    return dict(matches)

# non funziona nel notebook non so perché
def map_category(category_name):
    categories_map = {
        'BEST PICTURE': ['OUTSTANDING PICTURE', 'OUTSTANDING MOTION PICTURE', 'BEST MOTION PICTURE', 'OUTSTANDING PRODUCTION', 'BEST PICTURE'],
        'DIRECTING': ['DIRECTING'],
        'ACTING': ['ACTOR', 'ACTRESS', 'ACTOR IN A LEADING ROLE', 'ACTRESS IN A LEADING ROLE', 'ACTOR IN A SUPPORTING ROLE', 'ACTRESS IN A SUPPORTING ROLE'],
        'WRITING': ['WRITING', 'SCREENPLAY', 'STORY', 'ADAPTED', 'ORIGINAL', 'MOTION PICTURE STORY', 'STORY AND SCREENPLAY'],
        'TECHNICAL': ['CINEMATOGRAPHY', 'FILM EDITING', 'PRODUCTION DESIGN', 'SOUND', 'VISUAL EFFECTS','MAKEUP', 'COSTUME DESIGN', 'ART DIRECTION', 'SPECIAL EFFECTS'],
        'INTERNATIONAL': ['INTERNATIONAL FEATURE FILM', 'FOREIGN LANGUAGE FILM'],
        'MUSIC': ['MUSIC', 'SONG', 'SCORE', 'SCORING'],
        'DOCUMENTARY': ['DOCUMENTARY'],
        'SHORT FILM': ['SHORT FILM', 'SHORT SUBJECT']
    }
    category_name = str(category_name).upper()
    for group, keywords in categories_map.items():
        if any(keyword in category_name for keyword in keywords):
            return group
    return 'OTHER'

def cleanup_temp_columns(df, columns):
    df.drop(columns=columns, inplace=True)