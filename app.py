from flask import Flask, request, jsonify, render_template
import instaloader
import csv
from joblib import load  
import pandas as pd
#gytr
app = Flask(__name__)

# Function to convert boolean value to 0 or 1
def bool_to_int(value):
    return 1 if value else 0

# Function to check if username and full name are the same
def same_name(username, full_name):
    return 1 if username == full_name else 0

# Function to load the trained model and make predictions
def predictions():
    # Load the trained model
    best_gb_model = load('best_gradient_boosting_model.joblib')
    new_data = pd.read_csv('profile_info.csv')

    # Use the loaded model to make predictions
    predictions = best_gb_model.predict(new_data)

    # Return the predictions
    return predictions

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return render_template('index.html', error=str(e))

@app.route('/profile_info', methods=['POST'])
def get_profile_info():
    try:
        # Get the Instagram profile username from the request
        username = request.form.get('profile_username')

        # Create an instaloader instance
        L = instaloader.Instaloader()

        # Fetch profile information (handle potential exceptions)
        try:
            profile = instaloader.Profile.from_username(L.context, username)
            if profile is None:
                return render_template('index.html', error="Profile not found.")
        except instaloader.ProfileNotExistsException:
            return render_template('index.html', error="Profile not found.")
        except Exception as e:
            return render_template('index.html', error=str(e))

        # Construct the profile information dictionary with converted values
        profile_info = {
            "profile_pic": bool_to_int(bool(profile.profile_pic_url)),
            "username_length": len(profile.username),
            "fullname_words": len(profile.full_name.split()),
            "fullname_length": len(profile.full_name),
            "name_equals_username": same_name(profile.username, profile.full_name),
            "bio_length": len(profile.biography),
            "external_url": bool_to_int(bool(profile.external_url)),
            "is_private": bool_to_int(profile.is_private),
            "num_posts": profile.mediacount,
            "num_followers": profile.followers,
            "num_follows": profile.followees
        }
        
        # Write profile_info to profile_info.csv
        with open('profile_info.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = profile_info.keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            # Check if the file is empty, if so, write the header
            if csvfile.tell() == 0:
                writer.writeheader()
            writer.writerow(profile_info)

        return jsonify(profile_info)
    
    except Exception as e:
        return render_template('index.html', error=str(e))
    
@app.route('/result',methods=['POST'])
def result():
    try:
        # Get profile information
        profile_info = get_profile_info()
        
        # Make predictions
        predictions = predictions()

        # Convert predictions to text labels
        prediction_labels = ["Fake" if pred == 1 else "Not Fake" for pred in predictions]

        # Pass profile info and predictions to the HTML template
        return render_template('result.html', profile_info=profile_info, predictions=prediction_labels)
    except Exception as e:
        return render_template('index.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True)
