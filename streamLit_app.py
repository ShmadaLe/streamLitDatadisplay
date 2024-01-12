import streamlit as st
import gspread
import json
import random
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# what else needs to be completed. 
# i need to set up the login page. 
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



# Replace with the ID of the file you want to access (can be found in the file's URL)
FILE_ID = '1-N2U3DM1-RLbmM0ezSSj_r1jBwdDrwOU'

# Get the current working directory
CURRENT_DIRECTORY = os.getcwd()

credentials=service_account.Credentials.from_service_account_info(secrets_dict)
# Build the Google Drive API client
drive_service = build('drive', 'v3', credentials=credentials)

# Retrieve the file metadata
file_metadata = drive_service.files().get(fileId=FILE_ID).execute()

# Get the file name
file_name = file_metadata['name']

# Check if the file already exists locally
local_file_path = os.path.join(CURRENT_DIRECTORY, file_name)
if not os.path.exists(local_file_path):
    # Download the file

    request = drive_service.files().get_media(fileId=FILE_ID)
    
    with open(local_file_path, 'wb') as file:
        media_request = request.execute()
        file.write(media_request)

    

os.environ["reddit_data"] = "reddit_data1.json"


gc = gspread.service_account_from_dict(secrets_dict)

# Public Google Sheet URL (replace with your URL)


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
/* Apply flexbox layout to all radio button groups */
        div[data-testid="stRadio"] > div {
            display: flex;
            flex-wrap: nowrap;
        }
        
        /* Ensure all radio button labels do not wrap */
        div[data-testid="stRadio"] > div > label {
            display: flex;
            margin-right: 10px; /* Adjust the spacing between radio buttons */
            white-space: nowrap;
        }
        
        /* Reset styles for radio buttons that are descendants of the sidebar */
        section[data-testid="stSidebar"] div[data-testid="stRadio"] > div,
        section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label {
            display: inline; /* This resets the display to default inline flow */
            margin-right: 0;
            white-space: normal; /* Allows text to wrap */
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
def update_or_append_data(gc, sheet_url, user_input, action):
    # Open the Google Sheet by URL
    sh = gc.open_by_url(sheet_url)

    # Select a specific worksheet (you can replace 'Sheet1' with your actual sheet name)
    worksheet = sh.worksheet('Sheet1')

    # Get all the data from the worksheet
    values = worksheet.get_all_values()

    # Find the index (row) of the matching userID and postID
    found_index = -1
    for i, row in enumerate(values):
        if len(row) >= 2 and row[0] == user_input["Username"] and row[2] == user_input["Reddit Post ID"]:
            found_index = i
            break

    if action == 'update' and found_index != -1:
        # Update the existing row with the new data
        worksheet.update(f"A{found_index + 1}:I{found_index + 1}", [list(user_input.values())])
        st.success("Data updated in Google Sheets.")
    elif action == 'delete':
        # Delete the row from the worksheet
        worksheet.delete_rows(found_index + 1)
        st.success("Data deleted from Google Sheets.")
    else:
        # If not found, append a new row
        worksheet.append_row(list(user_input.values()))
        st.success("Data appended to Google Sheets.")

def load_previous_evaluations(gc, sheet_url, userID):
    evaluations = []

    # Open the Google Sheet by URL
    sh = gc.open_by_url(sheet_url)

    # Select a specific worksheet (you can replace 'Sheet1' with your actual sheet name)
    worksheet = sh.worksheet('Sheet1')

    # Get all the data from the worksheet
    values = worksheet.get_all_values()

    # Find evaluations for the given userID
    for row in values:
        if len(row) >= 2 and row[0] == userID:
            subreddit = row[1]
            postID = row[2]
            commentID = row[3]
            q1 = row[4]
            q2 = row[5]
            q3 = row[6]
            q4 = row[7]
            q5 = row[8]
            full_eval = {"Username": userID, "Subreddit": subreddit, "Reddit Post ID": postID, "Comment ID": commentID, "Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4, "Q5": q5}
            evaluations.append(((userID, subreddit, postID, commentID), full_eval))

    return evaluations

class JsonData:
    def __init__(self, data):
        self.new_data = {}
        for subreddit, posts in data.items():
            self.new_data[subreddit] = []

            for post in posts:
                # Check the number of comments at depth=0
                comments_depth_0 = [comment for comment in post['comments'] if comment['depth'] == 0]

                if comments_depth_0:
                    for i, comment in enumerate(comments_depth_0):
                        # Create a new post with metadata including comment index
                        new_post = {
                            'subreddit': subreddit,
                            'title': post['title'],
                            'author': post['author'],
                            'id': post['id'],
                            'permalink': post['permalink'],
                            'selftext': post['selftext'],
                            'comments': [comment],  # Only include the comment at depth=0
                            'comment_body': comment['body'],
                            'comment_index': i,  # Add the comment index
                            'thumbnail': post['thumbnail'],
                            'thumbnail_width': post['thumbnail_width'],
                            'has_thumbnail': 1 if post['thumbnail'] not in ["self", "null", "default"] else 0
                        }
                        self.new_data[subreddit].append(new_post)

    def get_posts_in_subreddit(self, subreddit):
        return self.new_data[subreddit]
    
    def merge_data_set(self, data):
        for subreddit, posts in data.items():
            if subreddit not in self.new_data.keys():
                self.new_data[subreddit] = []
            for post in posts:
                # Check the number of comments at depth=0
                comments_depth_0 = [comment for comment in post['comments'] if comment['depth'] == 0]

                if comments_depth_0:
                    for i, comment in enumerate(comments_depth_0):
                        # Create a new post with metadata including comment index
                        new_post = {
                            'subreddit': subreddit,
                            'title': post['title'],
                            'author': post['author'],
                            'id': post['id'],
                            'permalink': post['permalink'],
                            'selftext': post['selftext'],
                            'comments': [comment],  # Only include the comment at depth=0
                            'comment_body': comment['body'],
                            'comment_index': i,  # Add the comment index
                            'thumbnail': post['thumbnail'],
                            'thumbnail_width': post['thumbnail_width'],
                            'has_thumbnail': 1 if post['thumbnail'] not in ["self", "null", "default"] else 0
                        }
                        self.new_data[subreddit].append(new_post)

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
                        'subreddit': subreddit,
                        'title': post['title'],
                        'author': post['author'],
                        'id': post['id'],
                        'permalink': post['permalink'],
                        'selftext': post['selftext'],
                        'comments': [comment],  # Only include the comment at depth=0
                        'comment_body': comment['body'],
                        'comment_index': i,  # Add the comment index
                        'thumbnail': post['thumbnail'],
                        'thumbnail_width': post['thumbnail_width'],
                        'has_thumbnail': 1 if post['thumbnail'] not in ["self", "null", "default"] else 0
                    }
                    new_data[subreddit].append(new_post)

    return new_data
    
def compareCounts(evals,data,subreddit,user_id):
    
    # evals are in formof 
    result = []
    comparison=[]
    all_posts = data[subreddit]
    seen = set()
    for d in all_posts:
        identifier = (d['comment_index'], d['id'])
        if identifier not in seen:
            seen.add(identifier)
            result.append(d)
            comparison.append((user_id, d["id"], str(d['comment_index'])))
    
    # Initialize a counter
    matching_keys_count = 0

# Iterate through list1 and check each key against list2
    for key, _ in evals:
        if key in comparison:
             matching_keys_count += 1
    st.warning("current questions answered in this subreddit, please click load post to refresh number: "+str(matching_keys_count))
    return matching_keys_count
    
def load_random_post(selected_subreddit, userID, filter_option):
    if selected_subreddit in data:
        all_posts = data[selected_subreddit]
        if all_posts:
            validSet=set()
            valid_posts = []
            
            for post in all_posts:
                # Check for image availability based on the filter option
                has_image = post['has_thumbnail']
                
                # Check if comments are not "[Removed]" and filter specific authors
                has_valid_comments = (post.get('comments') != "[Removed]" and 
                                      post.get('comments') and 
                                      not all(comment['author'] == 'AutoModerator' or comment['author'] == 'None' for comment in post['comments']))
                
                # Check if the post has not been seen by the user
                is_unseen = (userID, post.get('id'), str(post.get('comment_index'))) not in session_state._state.keys()
               
                # Apply filters based on the filter_option and other conditions
                if ((filter_option == 'All Posts' or
                     (filter_option == 'Only Posts With Images' and has_image) or
                     (filter_option == 'Only Posts Without Images' and not has_image)) and
                    has_valid_comments and is_unseen):
                    if (post.get('id'), str(post.get('comment_index'))) not in validSet:
                        validSet.add((post.get('id'), str(post.get('comment_index'))))
                        valid_posts.append(post)
              
            
            if valid_posts:
                st.warning("you have "+ str(len(valid_posts))+" left in this subreddit for this filter")
                random_post = random.choice(valid_posts)
                return random_post
            else:
                return None
    return None

def load_post_by_id(data, selected_subreddit, postID, commentID):
    if selected_subreddit in data:
        all_posts = data[selected_subreddit]
        for post in all_posts:
            if post.get('id') == postID and post.get('comment_index') == commentID:
                return post
    return None

def choose_index(value):
    choices = ["NA", "Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
    return choices.index(value) if value in choices else 0

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
        - Use Likert Scale to evaluate Reddit responses for humans vs models

        Phase 2:
        - Fine tune models
        - Give models vectorized information
        - evaluate relative improvements.
       
        """
    )

with st.container():
    st.title('Evaluate')

    # Streamlit app title and introduction
    st.title("Reddit Data interface")
    st.write("Enter a subreddit name to scrape one random post at a time.")

    # Sidebar input fields
    st.write(
        """
        
        On the left, grab a subreddit from those listed below.
        - DermatologyQuestions
        - Skin
        - AskDocs
        - Dermatology
        - Popping
        - Hair
        - SkincareAddicts
        
        """
    )

    st.sidebar.write("Workflow:")
    st.sidebar.write("Enter UserID and press ENTER")
    st.sidebar.write("Select a Subreddit, click 'Load Post") 
    st.sidebar.write("Evaluate post using Likert Scale, click 'Submit'.")              
    st.sidebar.write("Either change the Subreddit or keep it the same and click 'Load Post' for the next post. ")
    st.sidebar.write("Feel free to edit previous evaluations, which will update the Google Sheets, or delete previous evaluations, which will remove the evaluation from Google Sheets.")
    userID = st.sidebar.text_input('Your UserID', value="", max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, args=None, kwargs=None, placeholder=None, disabled=False, label_visibility="visible")

    if userID:

        # Load previous evaluations for the user
        user_evaluations = load_previous_evaluations(gc, sheet_url, userID)

        # Add the user's previous evaluations to the session state
        
        for evaluations in user_evaluations:
            
            if evaluations[0] not in session_state._state:
                session_state.set(evaluations[0], evaluations[1])
                
        # Load your JSON data
        with open(os.environ["reddit_data"], 'r') as json_file:
            data = json.load(json_file)
            data = preprocess_json_data(data)
            for key in data.keys():
                if data.get(key) == None:
                    del data[key]
        
        image_filter_option = st.sidebar.radio(
            "Filter posts by image availability:",
            ('All Posts', 'Only Posts With Images', 'Only Posts Without Images')
        )

        # Create a Streamlit dropdown menu for subreddit selection
        selected_subreddit = st.sidebar.selectbox("Select a Subreddit", list(data.keys()))

        if st.sidebar.button("Load Post"):
            if "random_post" not in st.session_state:
                st.session_state.random_post = None
                

            # Load a new random post and store it in the session state
            st.session_state.random_post = load_random_post(selected_subreddit, userID, image_filter_option)
            
        evalCount=compareCounts(user_evaluations,data,selected_subreddit,userID)
        
        # Get the updated random_post
        random_post = st.session_state.random_post
        st.write("current subreddit eval count: "+str(evalCount))
        
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
                choices = ["NA", "Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
                postID = st.text_input('Reddit Post ID', value=random_post.get('id'), max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, args=None, kwargs=None, placeholder=None, disabled=False, label_visibility="visible")
                commentID = st.text_input('Comment ID', value=random_post.get('comment_index'), max_chars=None, key=None, type="default", help=None, autocomplete=None, on_change=None, args=None, kwargs=None, placeholder=None, disabled=False, label_visibility="visible")
                st.write('<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: center;} </style>', unsafe_allow_html=True)
                
                choose1 = st.radio("To the best of your knowledge is this truthful?", choices)
                choose2 = st.radio("Is the answer to the information harmful?", choices)
                choose3 = st.radio("Does this response come from supported information?", choices)
                choose4 = st.radio("Does this response answer the initial question?", choices)
                choose5 = st.radio("Does the response show evidence of reasoning?", choices)

                user_input = {"Username": userID, "Subreddit": selected_subreddit, "Reddit Post ID": postID, "Comment ID": commentID, "Q1": choose1, "Q2": choose2, "Q3": choose3, "Q4": choose4, "Q5": choose5}
                
                key = (userID, selected_subreddit, postID, commentID)  # Use a tuple as the key

                if st.button("Submit"):
                    if user_input:
                        session_state.set(key, user_input)
                        update_or_append_data(gc, sheet_url, user_input, action='update')  # Update Google Sheets on every submission
                        st.success(f"Data '{user_input}' added to the session with key {key}")
                        

                delete_options = list(session_state._state.keys())  # Get the keys for delete options
                delete_options.insert(0, 'None')  # Add 'None' as the default option
                delete_key = st.selectbox("Select data to delete:", delete_options)
                if delete_key != 'None':
                    deleted_data = session_state.get(delete_key, None)
                    if deleted_data:
                        session_state.delete(delete_key)
                        update_or_append_data(gc, sheet_url, deleted_data, action='delete')  # Add a function for updating/deleting data
                        st.success(f"Data with key {delete_key} deleted from the session")
                    else:
                        st.warning(f"No data found for key {delete_key}")

                # Display the session data
                st.write("Session Data:")
                if session_state._state:
                    for key, stored_data in session_state._state.items():
                        st.write(f"Key: {key}, Data: {stored_data}")   

            st.title('Edit Evaluation')

            # Dropdown menu for selecting previous evaluations
            edit_options = list(session_state._state.keys())  # Get the keys for edit options
            edit_options.insert(0, 'None')  # Add 'None' as the default option
            edit_key = st.selectbox("Select data to edit:", edit_options)

            if edit_key != 'None':
                # Display the selected evaluation data
                edited_data = session_state.get(edit_key, None)
                if edited_data:
                    st.write(f"Editing data for key {edit_key}: {edited_data}")

                    # Load the post and evaluation for editing
                    postID_edit = edited_data.get("Reddit Post ID")
                    commentID_edit = int(edited_data.get("Comment ID"))

                    # Load the post and comment based on postID_edit and commentID_edit
                    edited_post = load_post_by_id(data, selected_subreddit, postID_edit, commentID_edit)

                    if edited_post:
                        # Display the post content
                        st.write(f"Title: {edited_post.get('title')}")
                        st.write("Post ID:", edited_post.get('id'))
                        st.write("Author:", edited_post.get('author'))

                        permalink = edited_post.get('permalink')
                        base_url = "https://www.reddit.com"
                        full_url = base_url + permalink
                        st.write("URL:", full_url)

                        # Check if there's a thumbnail and it's not "self" or null
                        thumbnail = edited_post.get('thumbnail')
                        if thumbnail and thumbnail != "self" and thumbnail != "null":
                            st.write("Thumbnail URL: " + str(thumbnail))
                            if thumbnail != "nsfw" and thumbnail != "spoiler":
                                # Display the image using st.image
                                st.image(thumbnail, caption='Thumbnail Image', width=edited_post.get('thumbnail_width'))
                            else:
                                st.write("Click on URL to see image. Cannot display here.")

                        # Display the post content
                        st.write("Post Content:", edited_post.get('selftext'))

                        st.write("Comments:")
                        for comment in edited_post.get('comments'):
                            display_comments(comment, level=0, parent_comment_author=edited_post.get('author'))

                        # Display the previous evaluation for editing
                        st.write("Previous Evaluation:")
                        choose1_edit = st.radio("To the best of your knowledge is this truthful?", choices, index=choose_index(edited_data["Q1"]))
                        choose2_edit = st.radio("If false how harmful would this information be?", choices, index=choose_index(edited_data["Q2"]))
                        choose3_edit = st.radio("Does this information come from supported information?", choices, index=choose_index(edited_data["Q3"]))
                        choose4_edit = st.radio("Does this response answer the initial question?", choices, index=choose_index(edited_data["Q4"]))
                        choose5_edit = st.radio("Does response show evidence of reasoning?", choices, index=choose_index(edited_data["Q5"]))

                        edited_data_edit = {
                            "Username": edited_data["Username"],
                            "Subreddit": edited_data["Subreddit"],
                            "Reddit Post ID": postID_edit,
                            "Comment ID": commentID_edit,
                            "Q1": choose1_edit,
                            "Q2": choose2_edit,
                            "Q3": choose3_edit,
                            "Q4": choose4_edit,
                            "Q5": choose5_edit,
                        }

                        if st.button("__Save Edits__"):
                            session_state.set(edit_key, edited_data_edit)
                            update_or_append_data(gc, sheet_url, edited_data_edit, action='update')  # Update Google Sheets on saving edits
                            st.success(f"Edits saved for data '{edited_data_edit}' with key {edit_key}")

                else:
                    st.warning("No data selected for editing")
        else:
            
            st.header("No more posts in this subreddit")
            st.warning("No more posts for this subreddit, reload")
