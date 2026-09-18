import json
import os

from flask import Flask, render_template, request
from dotenv import load_dotenv
from groq import Groq

app = Flask(__name__)

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key=api_key
)

chat_history = []

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
            break

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

    learning_map = load_learning_map()

    known_skills = []
    unsure_skills = []

    for stage in learning_map["stages"]:
        for skill in stage["skills"]:

            skill_name = get_skill_name(skill)
            skill_id = skill_name.lower().replace(" ", "_")

            status = request.form.get(f"skill_status_{skill_id}")

            if status == "known":
                known_skills.append(skill_name)
            elif status == "unsure":
                unsure_skills.append(skill_name)

    matched_skills = known_skills

    current_stage = find_current_stage_by_order(
        learning_map, 
        matched_skills
    )

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

            for stage in learning_map["stages"]:
                for skill_data in stage["skills"]:
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

    return render_template(
            "result.html",
            goal=goal,
            learning_map=learning_map,
            matched_skills=matched_skills,
            unsure_skills=unsure_skills,
            current_stage=current_stage,
            next_stage=next_stage,
            stage_completion=stage_completion,
            next_step=next_step,
            next_step_description=next_step_description,
            next_step_resource=next_step_resource,
            get_skill_name=get_skill_name
        )

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    print("Data diterima:", data)

    message = data.get("message", "")

    learning_context = data.get("learning_context", {})

    print("Learning Context:", learning_context)

    print("Message:", message)

    chat_history.append({
        "role": "user",
        "content": message
    })
    context_message = {
        "role": "system",
        "content": f"""
You are the AI Learning Assistant for Learning GPS.

Your job is to help the user follow their personalized learning roadmap.

USER'S LEARNING CONTEXT

Goal:
{learning_context.get("goal", "")}

Known skills:
{learning_context.get("known_skills", [])}

Unsure skills:
{learning_context.get("unsure_skills", [])}

Current stage:
{learning_context.get("current_stage", "")}

Next step:
{learning_context.get("next_step", "")}

TUTOR RULES

1. Use the user's Learning GPS context when answering relevant questions.

2. Do not ask the user for information that is already provided in the context.

3. Prioritize the user's current stage and next step.

4. Do not unnecessarily jump to advanced topics that are far beyond the user's current stage.

5. If the user asks about a skill they are unsure about, explain it in a beginner-friendly way with simple examples.

6. If the user asks what they should learn next, recommend the next step from their Learning GPS roadmap.

7. If the user asks why they should learn something, explain its importance in relation to their current stage and goal.

8. When useful, give small practical examples or exercises.

9. Keep answers clear and focused. Do not overwhelm the user with unrelated technologies or advanced concepts.

10. If the user asks something unrelated to their learning journey, answer normally.

"""
}

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[context_message] + chat_history
    )
    
    reply = response.choices[0].message.content

    chat_history.append({
        "role": "assistant",
        "content": reply
    })

    print("Reply:", reply)

    return {
        "reply": reply
    }
