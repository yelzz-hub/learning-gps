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

def calculate_stage_scores(matched_skills, learning_map):
    stage_scores = []

    for stage in learning_map["stages"]:
        score = 0

        for skill in stage["skills"]:

            if skill in matched_skills:
                score += 1

        stage_scores.append({
            "stage": stage["name"],
            "score": score
        })

    return stage_scores

def find_current_stage(stage_scores):
    current_stage = stage_scores[0]

    for stage in stage_scores:
        if stage["score"] > current_stage["score"]:
            current_stage = stage

    return current_stage

def find_next_stage(current_stage, learning_map):
    next_stage = None

    for index, stage in enumerate(learning_map["stages"]):
        if stage["name"] == current_stage["stage"]:
            next_index = index + 1
            next_stage = learning_map["stages"][next_index]
            print("Next stage:", next_stage["name"])

    return next_stage

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

    stage_scores = calculate_stage_scores(
        matched_skills,
        learning_map
    )

    current_stage = find_current_stage(stage_scores)

    next_stage = find_next_stage(
        current_stage,
        learning_map
    )

    if goal == learning_map["goal"]:
        print("Goal found!")

    return render_template(
        "result.html",
        goal=goal,
        learning_story=learning_story,
        learning_map=learning_map,
        matched_skills=matched_skills,
        current_stage=current_stage,
        stage_scores=stage_scores,
        next_stage=next_stage
    )

