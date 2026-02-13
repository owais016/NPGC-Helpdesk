import os
from datetime import datetime 
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random
import math

app = Flask(__name__) # making application object
CORS(app) # enabling cors, CORS = cross-Origin Resource Sharing

# loading files
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "QnA.csv")
feedback_csv = os.path.join(base_dir, "appfeedback.csv")


df = pd.read_csv(csv_path)

# handle NaN in all required columns
df["Question"] = df["Question"].fillna("")
df["Informational"] = df["Informational"].fillna("")
df["Guidance oriented"] = df["Guidance oriented"].fillna("")
df["Institutional"] = df["Institutional"].fillna("")
df["Conversational"] = df["Conversational"].fillna("")

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df["Question"])

# context memory
# last_best_match = None   # stores last matched row index

# feedback routes
@app.route("/feedback", methods=["POST"])
def save_feedback():
    data = request.get_json()
    feedback_text = data.get("feedback", "").strip()

    if not feedback_text:
        return jsonify({"status": "error"})

    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "feedback": feedback_text
    }

    file_exists = os.path.isfile(feedback_csv)

    df_fb = pd.DataFrame([row])
    df_fb.to_csv(
        feedback_csv,
        mode="a",
        header=not file_exists,
        index=False
    )

    return jsonify({"status": "success"})


# routes
@app.route("/")
def home():
    return render_template("appindex.html")

@app.route("/chat", methods=["POST"])
def chat():
    # global last_best_match

    data = request.get_json()
    user_query = data.get("message", "").strip()

    if not user_query:
        return jsonify({"reply": "Please ask a question."})

    user_vec = vectorizer.transform([user_query])
    similarity = cosine_similarity(user_vec, X)

    best_match = similarity.argmax()
    score = similarity[0][best_match]

    if score <= 0.3: 
        return jsonify({
            "reply": "sorry, I couldn't understand that. could you please rephrase?"
        })

# #    contexaat handling
#     if score > 0.3:
#         last_best_match = best_match
#         selected_index = best_match
#     else:
#         if last_best_match is not None:
#             selected_index = last_best_match
#         else:
#             return jsonify({
#                 "reply": "Sorry, I couldn't understand that. Could you please rephrase?"
#             })

    # random answer
    rand_num = random.randint(1, 4)

    if rand_num == 1:
        answer = df["Informational"][best_match]
    elif rand_num == 2:
        answer = df["Guidance oriented"][best_match]
    elif rand_num == 3:
        answer = df["Institutional"][best_match]
    else:
        answer = df["Conversational"][best_match]

    # for empty answers
    if (
        answer is None
        or isinstance(answer, float) and math.isnan(answer)
        or str(answer).strip() == ""
    ):
        answer = "This information is currently unavailable. Please ask something else."

    return jsonify({"reply": answer})


if __name__ == "__main__":
    app.run(debug=True)


