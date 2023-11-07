import streamlit as st
import gspread
import json
import random
import os
st.set_page_config(page_title='Label Medical Misinformation', page_icon=':face_with_thermometer:', layout='wide')

# Initialize Google Sheets with service account credentials
# gc = gspread.service_account(filename='llms-for-misinformation-196fdd9cebe7.json')
os.environ["reddit_data"]="reddit_dummy_data.json"
secrets_dict = {
    "type": st.secrets["type"],
    "project_id": st.secrets["project_id"],
    "private_key_id": st.secrets["private_key_id"],
    "private_key": st.secrets["private_key"],
    "client_email": st.secrets["client_email"],
    "client_id": st.secrets["client_id"],
    "auth_uri": st.secrets["auth_uri"],
    "token_uri": st.secrets["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["client_x509_cert_url"],
    "universe_domain": st.secrets["universe_domain"],
}

gc = gspread.service_account_from_dict(secrets_dict)

# Public Google Sheet URL (replace with your URL)
sheet_url = 'https://docs.google.com/spreadsheets/d/1Srh7lQffIXZQEJA0eBImE9LiTf0lJWZ-cvKuaDmqI7Y/edit'

# Define CSS for styling your app
css = """
<style>
.container {
    margin: 20px;
}

.comment {
    padding: 2px;
    margin-top: 5px;
}

.comment p {
    margin-left: 20px;
    margin-bottom: 5px;
}

h1 {
    color: #3498db;
    font-size: 24px;
}

h2 {
    color: #e74c3c;
    font-size: 18px;
}
</style>
"""

# Apply CSS to the whole app
st.markdown(css, unsafe_allow_html=True)

class SessionState:
    def __init__(self, session):
        if 'data' not in session:
            session.data = {}
        self._state = session.data

    def get(self, key, default):
        return self._state.get(key, default)

    def set(self, key, value):
        self._state[key] = value

    def delete(self, key):
        if key in self._state:
            del self._state[key]

# Create a session state
session_state = SessionState(st.session_state)

# Initialize 'random_post' in session_state
if 'random_post' not in st.session_state:
    st.session_state.random_post = None

# Function to display comments recursively in a threaded format
def display_comments(comment, level, parent_comment_author):
    st.write('<div class="comment">', unsafe_allow_html=True)
    st.write(f"**{comment.get('author')}** (Reply to {parent_comment_author}):", unsafe_allow_html=True)
    st.write(f"<p style='margin-left: {10 * level}px; margin-bottom: 1px;'>{comment.get('body')}</p>", unsafe_allow_html=True)
    for reply in comment.get('replies'):
        if reply != "[removed]":
            display_comments(reply, level + 1, comment.get('author'))
    st.write('</div>', unsafe_allow_html=True)

# Function to find and update a row based on userID and postID
def update_or_append_data(gc, sheet_url, user_input):
    # Open the Google Sheet by URL
    sh = gc.open_by_url(sheet_url)

    # Select a specific worksheet (you can replace 'Sheet1' with your actual sheet name)
    worksheet = sh.worksheet('Sheet1')

    # Get all the data from the worksheet
    values = worksheet.get_all_values()

    # Find the index (row) of the matching userID and postID
    found_index = -1
    for i, row in enumerate(values):
        if len(row) >= 2 and row[0] == user_input["Username"] and row[1] == user_input["Reddit Post ID"]:
            found_index = i
            break

    if found_index != -1:
        # Update the existing row with the new data
        worksheet.update(f"A{found_index + 1}:G{found_index + 1}", [list(user_input.values())])
        st.success("Data updated in Google Sheets.")
    else:
        # If not found, append a new row
        worksheet.append_row(list(user_input.values()))
        st.success("Data appended to Google Sheets.")

# Modify the preprocess_json_data function to separate posts by comments at depth=0 and add metadata
def preprocess_json_data(data):
    new_data = {}
    for subreddit, posts in data.items():
        new_data[subreddit] = []

        for post in posts:
            # Check the number of comments at depth=0
            comments_depth_0 = [comment for comment in post['comments'] if comment['depth'] == 0]

            if comments_depth_0:
                for i, comment in enumerate(comments_depth_0):
                    # Create a new post with metadata including comment index
                    new_post = {
                        'title': post['title'],
                        'author': post['author'],
                        'id': post['id'],
                        'permalink': post['permalink'],
                        'selftext': comment['body'],
                        'comments': [comment],  # Only include the comment at depth=0
                        'comment_index': i,  # Add the comment index
                        'thumbnail': post['thumbnail'],
                        'thumbnail_width': post['thumbnail_width']
                    }
                    new_data[subreddit].append(new_post)

    return new_data

# Function to load a random post
def load_random_post(selected_subreddit):
    if selected_subreddit in data:
        all_posts = data[selected_subreddit]
        if all_posts:
            # Filter out posts with no comments
            valid_posts = [
                post for post in all_posts
                if post.get('comments') != "[Removed]"  # Check if comments are not "[Removed]"
                and post.get('comments') and not all(comment['author'] == 'AutoModerator' or comment['author'] == 'None' for comment in post['comments'])
            ]
            if valid_posts:
                random_post = random.choice(valid_posts)
                return random_post
    return None

# Header
with st.container():
    st.subheader('Detecting Misinformation with LLMs')
    st.title('Labeling Misinformation from Reddit Responses')
    st.write('Thanks for taking the time to label whether responses to medical questions on Reddit are misinformation or not.')
    st.write('[Learn More About the Lab and Team >](https://www.daneshjoulab.com/)')

with st.container():
    st.write('---')
    st.header('What we plan on doing:')
    st.write('##')
    st.write(
        """
        Phase 1: 
        - Analyzing Base GPT and LLAMA2
        - Extracting and parsing layers of Reddit Q&As regarding biomedicine.

        Phase 2:
        - Train LLAMA2 with human preference standards with reinforcement learning.
        - Build code to evaluate Reddit
        - Use Likert Scale to evaluate Reddit responses
        """
    )

with st.container():
    st.title('Evaluate')

    # Streamlit app title and introduction
    st.title("Reddit Data Scraper")
    st.write("Enter a subreddit name to scrape one random post at a time.")

    # Sidebar input fields
    st.write(
        """
        On the left, type in a subreddit name from those listed below.
        - DermatologyQuestions
        - Skin
        - AskDocs
        - Dermatology
        - Popping
        - Hair
        - SkincareAddicts
        """
    )

    userID = st.sidebar.text_input('Your UserID', value="", max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, args=None, kwargs=None, placeholder=None, disabled=False, label_visibility="visible")

    if userID:
        # Load your JSON data
        with open(os.environ["reddit_data"], 'r') as json_file:
            data = json.load(json_file)
            data = preprocess_json_data(data)

        # Create a Streamlit dropdown menu for subreddit selection
        selected_subreddit = st.sidebar.selectbox("Select a Subreddit", list(data.keys()))

        if st.sidebar.button("Load Post"):
            if "random_post" not in st.session_state:
                st.session_state.random_post = None

            # Load a new random post and store it in the session state
            st.session_state.random_post = load_random_post(selected_subreddit)

        # Get the updated random_post
        random_post = st.session_state.random_post

        if random_post:
            # Create two columns for post and evaluation side-by-side
            col1, col2 = st.columns([9, 13])

            with col1:
                # Display the post content
                st.write(f"Title: {random_post.get('title')}")
                st.write("Post ID:", random_post.get('id'))
                st.write("Author:", random_post.get('author'))

                permalink = random_post.get('permalink')
                base_url = "https://www.reddit.com"
                full_url = base_url + permalink
                st.write("URL:", full_url)

                # Check if there's a thumbnail and it's not "self" or null
                thumbnail = random_post.get('thumbnail')
                if thumbnail and thumbnail != "self" and thumbnail != "null":
                    st.write("Thumbnail URL: " + str(thumbnail))
                    if thumbnail != "nsfw" and thumbnail != "spoiler":
                        # Display the image using st.image
                        st.image(thumbnail, caption='Thumbnail Image', width=random_post.get('thumbnail_width'))
                    else:
                        st.write("Click on URL to see image. Cannot display here.")

                # Display the post content
                st.write("Post Content:", random_post.get('selftext'))

                st.write("Comments:")
                for comment in random_post.get('comments'):
                    display_comments(comment, level=0, parent_comment_author=random_post.get('author'))

            with col2:
                postID = st.text_input('Reddit Post ID', value=random_post.get('id'), max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, args=None, kwargs=None, placeholder=None, disabled=False, label_visibility="visible")
                commentID = st.text_input('Comment ID', value=random_post.get('comment_index'), max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, args=None, kwargs=None, placeholder=None, disabled=False, label_visibility="visible")
                st.write('<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: center;} </style>', unsafe_allow_html=True)
                choose1 = st.radio("To the best of your knowledge is this truthful?", ("NA","Strongly Disagree","Disagree", "Neutral", "Agree", "Strongly Agree"))
                choose2 = st.radio("If false how harmful would this information be?", ("NA","Strongly Disagree","Disagree", "Neutral", "Agree", "Strongly Agree"))
                choose3 = st.radio("Does this information come from supported information (opt)?", ("NA","Strongly Disagree","Disagree", "Neutral", "Agree", "Strongly Agree"))
                choose4 = st.radio("Does this response answer the initial question?", ("NA","Strongly Disagree","Disagree", "Neutral", "Agree", "Strongly Agree"))
                choose5 = st.radio("Does response show evidence of reasoning?", ("NA","Strongly Disagree","Disagree", "Neutral", "Agree", "Strongly Agree"))

                user_input = {"Username": userID, "Reddit Post ID": postID, "Comment ID": commentID, "Q1": choose1, "Q2": choose2, "Q3": choose3, "Q4": choose4, "Q5": choose5}

                key = (userID, postID, commentID)  # Use a tuple as the key

                if st.button("Submit"):
                    if user_input:
                        session_state.set(key, user_input)
                        st.success(f"Data '{user_input}' added to the session with key {key}")

                delete_options = list(session_state._state.keys())  # Get the keys for delete options
                delete_options.insert(0, 'None')  # Add 'None' as the default option
                delete_key = st.selectbox("Select data to delete:", delete_options)
                if delete_key != 'None':
                    session_state.delete(delete_key)
                    st.success(f"Data with key {delete_key} deleted from the session")

                # Display the session data
                st.write("Session Data:")
                if session_state._state:
                    for key, data in session_state._state.items():
                        st.write(f"Key: {key}, Data: {data}")

                # When you want to export user input to Google Sheets
                if st.button("Export Evaluations To Google Sheets"):
                    # Load your Google Sheets credentials (replace with your own JSON file)
                    # gc = gspread.service_account(filename="llms-for-misinformation-196fdd9cebe7.json")
                    gc = gspread.service_account_from_dict(secrets_dict)

                    # Iterate through all the user inputs in the session and update/append them to Google Sheets
                    for key, user_input in session_state._state.items():
                        update_or_append_data(gc, sheet_url, user_input)

                    st.success("Data successfully added to Google Sheets.")
# import streamlit as st
# import pandas as pd
# import json

# from utils import get_comments

# #TODO: build a selection of posts and evaluations. 
# # how do you want to build this. 
# # build the further following. 


# # the following needs to be done in t

# # Load JSON data  




# import requests
# import streamlit as st
# from streamlit_lottie import st_lottie
# import pandas as pd
# import os

# st.set_page_config(page_title='Label Medical Misinformation', page_icon=':face_with_thermometer:', layout='wide')

# class SessionState:
#     def __init__(self, session):
#         if 'data' not in session:
#             session.data = {}
#         self._state = session.data

#     def get(self, key, default):
#         return self._state.get(key, default)

#     def set(self, key, value):
#         self._state[key] = value

#     def delete(self, key):
#         if key in self._state:
#             del self._state[key]

# # Create a session state
# session_state = SessionState(st.session_state)

# def load_lottieurl(url):
#     r = requests.get(url)
#     if r.status_code != 200:
#         return None
#     return r.json()

# # Load Assets
# lottie_coding = load_lottieurl('https://lottie.host/736990b8-90e6-4c1a-b273-cc21759292a9/PFVfPSGow1.json')

# # Header
# with st.container():
#     st.subheader('Detecting Misinformation with LLMs')
#     st.title('Labeling Misinformation from Reddit Responses')
#     st.write('Thanks for taking the time to label whether responses to medical questions on Reddit are misinformation or not.')
#     st.write('[Learn More About the Lab and Team >](https://www.daneshjoulab.com/)')

# with st.container():
#     st.write('---')
#     left_column, right_column = st.columns(2)
#     with left_column:
#         st.header('What we plan on doing:')
#         st.write('##')
#         st.write(
#             """
#             Phase 1: 
#             - Analyzing Base GPT and LLAMA2
#             - Extracting and parsing layers of Reddit Q&As regarding biomedicine.

#             Phase 2:
#             - Train LLAMA2 with human preference standards with reinforcement learning.
#             - Build code to evaluate Reddit
#             - Use Likert Scale to evaluate Reddit responses
#             """
#         )
#     with right_column:
#         st_lottie(lottie_coding, height=300, key='coding')

# with st.container():
#     st.title('Evaluate')

#     # Create a list of image paths (replace with actual image file paths)
#     # "image1.jpg", "image2.jpg", "image3.jpg", "image4.jpg"
#     image_paths = []

#     # Display images with incremental labels
#     for i, image_path in enumerate(image_paths):
#         st.image(image_path, caption=f"Image {i + 1}")
#         st.text("")  # Add some space between images

#     userID = st.text_input('Your UserID', value="", max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, args=None, kwargs=None, placeholder=None, disabled=False, label_visibility="visible")
#     threadID = st.text_input('Reddit Thread ID', value="", max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, args=None, kwargs=None, placeholder=None, disabled=False, label_visibility="visible")
#     st.write('<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: center;} </style>', unsafe_allow_html=True)
#     choose1 = st.radio("To the best of your knowledge is this truthful?",("NA","Strongly Disagree","Disagree", "Neutral", "Agree", "Strongly Agree"))
#     choose2 = st.radio("If false how harmful would this information be?",("NA","Strongly Disagree","Disagree", "Neutral", "Agree", "Strongly Agree"))
#     choose3 = st.radio("Does this information come from supported information (opt)?",("NA","Strongly Disagree","Disagree", "Neutral", "Agree", "Strongly Agree"))
#     choose4 = st.radio("Does this response answer the initial question?",("NA","Strongly Disagree","Disagree", "Neutral", "Agree", "Strongly Agree"))
#     choose5 = st.radio("Does response show evidence of reasoning?",("NA","Strongly Disagree","Disagree", "Neutral", "Agree", "Strongly Agree"))

#     user_input = {"Username": userID, "Reddit Thread ID": threadID, "Q1": choose1, "Q2": choose2, "Q3": choose3, "Q4": choose4, "Q5": choose5} 

#     key = (userID, threadID)  # Use a tuple as the key

#     if st.button("Submit"):
#         if user_input:
#             session_state.set(key, user_input)
#             st.success(f"Data '{user_input}' added to the session with key {key}.")

#     delete_options = list(session_state._state.keys())  # Get the keys for delete options
#     delete_options.insert(0, 'None')  # Add 'None' as the default option
#     delete_key = st.selectbox("Select data to delete:", delete_options)
#     if delete_key != 'None':
#         session_state.delete(delete_key)
#         st.success(f"Data with key {delete_key} deleted from the session.")

#     # Display the session data
#     st.write("Session Data:")
#     if session_state._state:
#         for key, data in session_state._state.items():
#             st.write(f"Key: {key}, Data: {data}")

#     # User input for file destination (directory path)
#     st.write('For Windows: "C:\\Users\\YourUsername\\Documents\\"')
#     st.write('For macOS or Linux: "/Users/YourUsername/Documents/"')
#     file_destination = st.text_input("Enter the Directory Path to Save CSV File", "/path/to/directory")

#     # Export session data to a local CSV file in the specified directory
#     if st.button("Export CSV Locally"):
#         if session_state._state:
#             data_list = [data for data in session_state._state.values()]
#             df = pd.DataFrame(data_list, columns=["Username", "Reddit Thread ID", "Q1", "Q2", "Q3", "Q4", "Q5"])
            
#             if file_destination:
#                 destination_path = os.path.join(file_destination, "user_data.csv")
#                 df.to_csv(destination_path, index=False)
#                 st.success(f"Data exported to {destination_path}")
#             else:
#                 st.warning("Please specify a directory path to save the CSV file.")
#         else:
#             st.warning("No data to export.")

#     st.write('Please email the exported csv to: minhle19@stanford.edu')
#     st.write('Thank you for your time!')
# uploaded_file = st.sidebar.file_uploader("Choose a JSON file or use the default", type="json")
# #HERE is where my code starts




# st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)



# data = None
# while data is None:
#     if uploaded_file is not None:
#         data = json.load(uploaded_file)
#     else:
#         try:
#             with open('reddit_dummy_data.json') as f:
#                 data = json.load(f)
#         except FileNotFoundError:
#             st.error('Default file not found. Please upload a file.')
#             continue
# def display_comment(comment, depth=0):
#     indent = "----" * depth
#     # st.write(f"depth:{depth}{indent}- {comment['body']}")
    
#     st.write(f"depth:{comment['depth']} id: {comment['id']}")
# # Display HTML conten
#     st.markdown(comment['body_html'], unsafe_allow_html=True)
#     if 'replies' in comment:
#         for reply in comment['replies']:
#             display_comment(reply, depth + 1)
# # Create a list of subreddit names
# subreddits = list(data.keys())

# # Create a sidebar for subreddit selection
# subreddit = st.sidebar.selectbox('Choose a subreddit', subreddits)

# # Display the selected subreddit
# st.title(f'Selected subreddit: {subreddit}')

# # Get the posts from the selected subreddit
# posts = data[subreddit]

# # Create a list of post ids
# post_ids = [post['id'] for post in posts]

# # Create a sidebar for post selection
# post_id = st.sidebar.selectbox('Choose a post', post_ids)

# # Get the selected post
# post = next(post for post in posts if post['id'] == post_id)
# print(post)
# # Display the selected post
# st.subheader('Selected post:')
# st.write(post['selftext'])

# # Get the comments from the selected post using the get_comments function from utils.py
# comments = get_comments(data, subreddit, post_id)
# # you need to finish this code.

# ## need to fix this and then move onto building. 
# # Display the comments
# st.subheader('Comments:')
# for comment in comments:
#     display_comment(comment)