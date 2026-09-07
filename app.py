import json

from flask import Flask, render_template, request

app = Flask(__name__)

def load_learning_map():
    with open("data/learning_map.json", "r") as file:
        learning_map = json.load(file)
    return learning_map
    
def find_matching_skills(learning_story, learning_map):
    matched_skills = []

    learning_story = learning_story.lower()

    for stage in learning_map["stages"]:
        for skill in stage["skills"]:
            if skill.lower() in learning_story:
                matched_skills.append(skill)

    return matched_skills

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    goal = request.form["goal"]

    learning_story = request.form["learning_story"]
    learning_map = load_learning_map()

    matched_skills = find_matching_skills(
        learning_story,
        learning_map
    )
    print(matched_skills)


    if goal == learning_map["goal"]:
        print("Goal found!")

    return render_template(
        "result.html",
        goal=goal,
        learning_story=learning_story,
        learning_map=learning_map,
        matched_skills=matched_skills
    )

