import json

from flask import Flask, render_template, request

app = Flask(__name__)

def get_skill_name(skill):
    if isinstance(skill, dict):
        return skill["name"]
    return skill

def get_skill_description(skill):
    if isinstance(skill, dict):
        return skill.get("description", "")
    return ""

def get_skill_resource(skill):
    if isinstance(skill, dict):
        return skill.get("resource", "")
    return ""

def load_learning_map():
    with open("data/learning_map.json", "r") as file:
        learning_map = json.load(file)
    return learning_map


def calculate_stage_scores(matched_skills, learning_map):
    stage_scores = []

    for stage in learning_map["stages"]:
        score = 0

        for skill in stage["skills"]:

            if get_skill_name(skill) in matched_skills:
                score += 1

        stage_scores.append({
            "stage": stage["name"],
            "score": score
        })

    return stage_scores

def find_current_stage_by_order(learning_map, matched_skills):
    for stage in learning_map["stages"]:
        stage_skills = stage["skills"]

        if not stage_skills:
            continue

        is_complete = True
        for skill in stage_skills:
            if get_skill_name(skill) not in matched_skills:
                is_complete = False

        if not is_complete:
            completed_count = 0

            for skill in stage_skills: 
                if get_skill_name(skill) in matched_skills:
                    completed_count += 1
            return {
                "stage": stage["name"],
                "score": completed_count
            }
        
    return {
        "stage": "Roadmap Complete",
        "score": 0
    }

def find_next_stage(current_stage, learning_map):
    if current_stage["stage"] == "Roadmap Complete":
        return None

    for index, stage in enumerate(learning_map["stages"]):
        if stage["name"] == current_stage["stage"]:
            next_index = index + 1

            if next_index >= len(learning_map["stages"]):
                return None
            
            return learning_map["stages"][next_index]
    return None

def check_stage_completion(current_stage, learning_map, matched_skills):
    if current_stage["stage"] == "Roadmap Complete":
        return {
            "stage": "Roadmap Complete",
            "total_skills": 0,
            "completed_skills": [],
            "missing_skills": [],
            "is_complete": True
        }
    
    stage_data = None

    for stage in learning_map["stages"]:
        if stage["name"] == current_stage["stage"]:
            stage_data = stage

    total_skills = len(stage_data["skills"])

    completed_skills = []

    for skill in stage_data["skills"]:
        skill_name = get_skill_name(skill)

        if skill_name in matched_skills:
            completed_skills.append(skill_name)

    missing_skills = []

    for skill in stage_data["skills"]:
        skill_name = get_skill_name(skill)

        if skill_name not in matched_skills:
            missing_skills.append(skill_name)

    is_complete = len(completed_skills) == total_skills

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
        skill_name = get_skill_name(skill)

        if skill_name in matched_skills:
            completed_skills.append(skill_name)

    total_skills = len(next_stage["skills"])

    return {
        "completed_skills": completed_skills,
        "completed_count": len(completed_skills),
        "total_skills": total_skills
    }

@app.route("/")
def home():
    learning_map = load_learning_map()

    return render_template(
        "index.html",
        learning_map=learning_map,
        get_skill_name=get_skill_name
    )

@app.route("/analyze", methods=["POST"])
def analyze():
    goal = request.form["goal"]

    matched_skills = request.form.getlist("learned_skills")

    learning_map = load_learning_map()

    stage_scores = calculate_stage_scores(
        matched_skills,
        learning_map
    )

    current_stage = find_current_stage_by_order(learning_map, matched_skills)

    stage_completion = check_stage_completion(
        current_stage,
        learning_map,
        matched_skills
    )

    next_step_resource = ""

    if current_stage["stage"] == "Roadmap Complete":
        next_step = "🎉 You have completed the entire roadmap!"
        next_step_description = ""

    elif stage_completion["is_complete"]:
        next_step = "You are ready to move to the next stage!"
        next_step_description = ""

    else:
        missing_skills = stage_completion["missing_skills"]

        if missing_skills:
            next_skill_name = missing_skills[0]

            next_step = f"Focus on: {next_skill_name}"

            next_step_description = ""
            next_step_resource = ""

            for skill in learning_map["stages"]:
                for skill_data in skill["skills"]:
                    if get_skill_name(skill_data) == next_skill_name: 
                        next_step_description = get_skill_description(skill_data)
                        next_step_resource = get_skill_resource(skill_data)
                        break
                if next_step_description:
                    break
        else:
            next_step = "Keep learning!"
            next_step_description = ""

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

    return render_template(
        "result.html",
        goal=goal,
        learning_map=learning_map,
        matched_skills=matched_skills,
        current_stage=current_stage,
        stage_scores=stage_scores,
        next_stage=next_stage,
        stage_completion=stage_completion,
        next_stage_progress=next_stage_progress,
        next_step=next_step,
        next_step_description=next_step_description,
        next_step_resource=next_step_resource,
        get_skill_name=get_skill_name
    )

