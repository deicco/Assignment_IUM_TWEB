import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import self
from pandas import value_counts
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