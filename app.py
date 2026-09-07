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

def find_current_stage_by_progress(stage_scores, learning_map):
    for index, stage_score in enumerate(stage_scores):

        stage = learning_map["stages"][index]
        total_skills = len(stage["skills"])
        if stage_score["score"] < total_skills:
            return stage_score
        
    return stage_scores[-1]

def find_next_stage(current_stage, learning_map):
    next_stage = None

    for index, stage in enumerate(learning_map["stages"]):
        if stage["name"] == current_stage["stage"]:
            next_index = index + 1
            next_stage = learning_map["stages"][next_index]
            print("Next stage:", next_stage["name"])

    return next_stage

def check_stage_completion(current_stage, learning_map, matched_skills):
    stage_data = None

    for stage in learning_map["stages"]:
        if stage["name"] == current_stage["stage"]:
            stage_data = stage

    total_skills = len(stage_data["skills"])
    print("Total skills:", total_skills)

    completed_skills = []

    for skill in stage_data["skills"]:
        if skill in matched_skills:
            completed_skills.append(skill)

    print("Completed skills:", completed_skills)

    missing_skills = []

    for skill in stage_data["skills"]:
        if skill not in matched_skills:
            missing_skills.append(skill)

    print("Missing skills:", missing_skills)

    is_complete = len(completed_skills) == total_skills

    print("Stage complete:", is_complete)

    return {
        "stage": stage_data["name"],
        "total_skills": total_skills,
        "completed_skills": completed_skills,
        "missing_skills": missing_skills,
        "is_complete": is_complete
    }

def check_next_stage_progress(next_stage, matched_skills):
    if next_stage is None:
        return None

    completed_skills = []

    for skill in next_stage["skills"]:
        if skill in matched_skills:
            completed_skills.append(skill)
    total_skills = len(next_stage["skills"])

    return {
        "completed_skills": completed_skills,
        "completed_count": len(completed_skills),
        "total_skills": total_skills
    }

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

    print("Stage scores:", stage_scores)

    current_stage = find_current_stage(stage_scores)

    current_stage_by_progress = find_current_stage_by_progress(
        stage_scores,
        learning_map
    )
    print(
        "Current stage by progress:",
          current_stage_by_progress
    )

    stage_completion = check_stage_completion(
        current_stage,
        learning_map,
        matched_skills
    )

    print(stage_completion)

    for index, stage in enumerate(stage_scores):
        print(
            "Index:", index,
            "| Stage:", stage["stage"],
            "| Score:", stage["score"]
        )

    if stage_completion["is_complete"]:
        next_stage = find_next_stage(
            current_stage,
            learning_map
        )
    else:
        next_stage = None

    next_stage_progress = check_next_stage_progress(
        next_stage,
        matched_skills
    )

    print("Next stage progress:", next_stage_progress)

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
        next_stage=next_stage,
        stage_completion=stage_completion,
        next_stage_progress=next_stage_progress
    )

