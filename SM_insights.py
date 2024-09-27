import pandas as pd
import re
from datetime import datetime

class SM:
    def response(self, npi_id):
        # Load dataframes
        keywords_df = pd.read_csv('./Keywords_df.csv')
        posts_df = pd.read_csv('./Posts_df.csv', encoding='ISO-8859-1')

        posts_df.columns = posts_df.columns.str.strip()
        keywords_df.columns = keywords_df.columns.str.strip()

        # Create keyword-response and keyword-priority dictionaries
        keywords_to_responses = dict(zip(keywords_df['Keyword'], keywords_df['Response']))
        keywords_to_priority = dict(zip(keywords_df['Keyword'], keywords_df['Keyword_Priority']))

        # Medical keywords to filter posts
        medical_keywords = ['lymphoma', 'cancer', 'oncology'] 

        # Function to filter posts with medical keywords
        def filter_medical_keywords(post_text):
            post_text = str(post_text).lower()
            return any(med_keyword in post_text for med_keyword in medical_keywords)

        # Filter posts based on medical keywords
        filtered_posts_df = posts_df[posts_df['Post_Text'].apply(filter_medical_keywords)]

        # Define priority ranges
        priority_days = {
            1: 7,
            2: 14,
            3: 30,
            4: 60,
            5: 90,
            6: 180,
            7: 365,
            8: 730,
            9: 1095,
            10: float('inf')  # Priority 10 for posts older than 3 years
        }

        # Calculate date priority
        def calculate_date_priority(post_date_str, reference_date=None):
            if reference_date is None:
                reference_date = datetime.now()

            try:
                post_date = datetime.strptime(post_date_str, '%m-%d-%Y')
                days_diff = (reference_date - post_date).days

                for priority, days in sorted(priority_days.items()):
                    if days_diff <= days:
                        return priority
            except ValueError:
                return 10  # Default priority if date is not valid

            return 10  # Default priority for posts older than the maximum specified

        # Extract keyword context
        def extract_keyword_context(post_text, keyword, word_limit=15):
            sentences = re.split(r'(?<=[.!?]) +', post_text)
            keyword_sentences = [sentence for sentence in sentences if keyword.lower() in sentence.lower()]

            hashtags = re.findall(r'#\w+', post_text)
            top_hashtags = hashtags[:2]

            snippets = []
            for sentence in keyword_sentences:
                words = sentence.split()
                keyword_index = next((i for i, word in enumerate(words) if keyword.lower() in word.lower()), None)
                if keyword_index is not None:
                    start = max(keyword_index - (word_limit // 2), 0)
                    end = min(keyword_index + (word_limit // 2) + 1, len(words))
                    snippet = ' '.join(words[start:end])
                    if len(words) > word_limit:
                        snippet += "..."
                    snippets.append(snippet)

            context = ' '.join(snippets)
            hashtags_str = ", ".join(top_hashtags)

            return context, hashtags_str

        # Check for keywords in a post
        def check_post_for_keywords(row):
            post_text = str(row.get('Post_Text', ''))
            source = row.get('Source', '')
            hcp_name = row.get('HCP_Name', '')
            post_url = row.get('Post_URL', '')
            post_date = row.get('Post_Date', '')

            if pd.isna(post_text):
                post_text = ''

            for keyword, response in keywords_to_responses.items():
                if keyword.lower() in post_text.lower():
                    context, hashtags_str = extract_keyword_context(post_text, keyword)
                    keyword_priority = keywords_to_priority.get(keyword, 10)
                    date_priority = calculate_date_priority(post_date)

                    final_priority = (keyword_priority + date_priority) / 2

                    if hashtags_str:
                        full_response = f'{hcp_name} has posted on {source} about "{context}" and "{hashtags_str}". [Click here]({post_url})'
                    else:
                        full_response = f'{hcp_name} has posted on {source} about "{context}". [Click here]({post_url})'
                    return full_response, keyword, keyword_priority, date_priority, final_priority, post_date

            return None, None, None, None, None, post_date

        # Apply the keyword detection function
        filtered_posts_df[['Keyword_Response', 'Detected_Keyword', 'Keyword_Priority', 'Date_Priority', 'Final_Priority', 'Post_Date']] = filtered_posts_df.apply(
            lambda row: pd.Series(check_post_for_keywords(row)), axis=1
        )

        # Further filter out posts without detected keywords
        final_filtered_posts_df = filtered_posts_df.dropna(subset=['Detected_Keyword'])

        # Sort the final filtered posts
        final_filtered_posts_df = final_filtered_posts_df.sort_values(by='Final_Priority', ascending=True)

        # Ensure 'NPI_ID' column is string type for filtering
        final_filtered_posts_df['NPI_ID'] = final_filtered_posts_df['NPI_ID'].astype(str)

        # Filter results by NPI_ID
        filtered_by_npi_df = final_filtered_posts_df[final_filtered_posts_df['NPI_ID'] == str(npi_id)]

        if filtered_by_npi_df.empty:
            return f"No results found for NPI_ID: {npi_id}"
        else:
            return filtered_by_npi_df[['NPI_ID', 'HCP_Name', 'Source', 'Post_Date', 'Keyword_Response', 'Final_Priority']].to_dict(orient='records')
