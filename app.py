import json
import os

from flask import Flask, render_template, request, session
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

api_key = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key=api_key
)


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

def get_roadmap_sequence(learning_map):
    roadmap = []

    for stage in learning_map["stages"]:
        for skill in stage["skills"]:
            roadmap.append(skill["name"])

    return roadmap


def get_remaining_skills(roadmap_sequence, known_skills):
    return [skill for skill in roadmap_sequence if skill not in known_skills]

def get_unlearned_skills(
        roadmap_sequence,
        known_skills, 
        unsure_skills
):
    return [
        skill
        for skill in roadmap_sequence
        if skill not in known_skills
        and skill not in unsure_skills
    ]

def get_following_skill(
        roadmap_sequence,
        next_skill_name,
        known_skills,
        unsure_skills
):
    if next_skill_name not in roadmap_sequence:
        return None

    next_step_index = roadmap_sequence.index(next_skill_name)

    for skill in roadmap_sequence[next_step_index + 1:]:
        if skill not in known_skills:
            return skill

    return None


def find_current_stage_by_order(learning_map, matched_skills):
    for stage in learning_map["stages"]:
        stage_skills = stage["skills"]

        if not stage_skills:
            continue

        completed_count = 0

        for skill in stage_skills:
            if get_skill_name(skill) in matched_skills:
                completed_count += 1

        if completed_count < len(stage_skills):
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
    missing_skills = []

    for skill in stage_data["skills"]:
        skill_name = get_skill_name(skill)

        if skill_name in matched_skills:
            completed_skills.append(skill_name)
        else:
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
    roadmap_sequence = get_roadmap_sequence(learning_map)

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

    remaining_skills = get_remaining_skills(
        roadmap_sequence,
        known_skills
    )

    unlearned_skills = get_unlearned_skills(
        roadmap_sequence,
        known_skills, 
        unsure_skills
    )

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
    next_skill_name = None

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

    following_step = get_following_skill(
        roadmap_sequence,
        next_skill_name,
        known_skills,
        unsure_skills
    )

    return render_template(
            "result.html",
            goal=goal,
            learning_map=learning_map,
            matched_skills=matched_skills,
            unsure_skills=unsure_skills,
            remaining_skills=remaining_skills,
            unlearned_skills=unlearned_skills,
            current_stage=current_stage,
            next_stage=next_stage,
            stage_completion=stage_completion,
            next_step=next_step,
            next_step_description=next_step_description,
            next_step_resource=next_step_resource,
            roadmap_sequence=roadmap_sequence,
            following_step=following_step,
            get_skill_name=get_skill_name
        )

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "reply": "Invalid request data."
        }, 400

    chat_history = session.get("chat_history", [])
    
    message = data.get("message", "")

    if not isinstance(message, str):
        return {
            "reply": "Invalid message."
        }, 400

    if len(message) > 2000:
        return {
            "reply": "Your message is too long. Please keep it under 2000 characters."
        }, 400

    if not message.strip():
        return {
            "reply": "Please enter a message first."
        }

    learning_context = data.get("learning_context", {})

    context_message = {
        "role": "system",
        "content": f"""
You are the AI Learning Assistant for Learning GPS.

Your job is to help the user understanting and navigate their learning journey based on the learning context provided below.  

USER'S LEARNING CONTEXT

Goal:
{learning_context.get("goal", "")}

Learned skills:
{learning_context.get("learned_skills", [])}

Unsure skills:
{learning_context.get("unsure_skills", [])}

Unlearned skills:
{learning_context.get("unlearned_skills", [])}

Current stage:
{learning_context.get("current_stage", "")}

Next step determined by Learning GPS:
{learning_context.get("next_step", "")}

Next step description:
{learning_context.get("next_step_description", "")}

Following step:
{learning_context.get("following_step", "")}

Learning roadmap:
{learning_context.get("roadmap", [])}


ANSWERING RULES

1. Match  the user's current learning level.
   Prefer explanations that are appropriate for a beginner unless
   the conversation clearly shows that the user understands more advanced topics.

2. Answer the user's actual question first.
   Do not introduce unrelated concepts just because they are part of
   the roadmap.

3. Keep answers focused and proportional to the question.
   Simple questions should receive short explanations.
   More complex questions may receive more detail when necessary.
   Do not add information that the user did not ask for unless it is
   necessary for understanding the answer.

3A. DO NOT AUTOMATICALLY REVEAL FUTURE STEPS.

   When explaining a skill or answering a question about a concept,
   focus only on the user's current question.

   Do not mention the next skill or following skill anywhere in the answer,
   including at the beginning, middle, or end.

   Do not use phrases such as:
   "next you will learn..."
   "after this..."
   "you are ready for..."
   "the next concept is..."
   or similar statements.

   Only mention the next step or following step if the user explicitly asks
   what they should learn next, what comes after the current skill,
   or asks for a learning recommendation.

   The Learning GPS next step and following step should guide the assistant
   when relevant, but they should not be inserted into unrelated answers.

3B. STAY WITHIN THE CURRENT LEARNING TOPIC.

   When the user asks to learn or understand the current next skill,
   focus primarily on that skill.

   Do not teach other roadmap skills in detail unless they are necessary
   to explain the current skill.

   For example, if the current next skill is Data Types, focus on basic
   Python data types relevant to the user's current level.

   Do not expand the lesson into Lists, Dictionaries, Loops, Functions,
   or other separate roadmap skills unless the user explicitly asks about them.

4. Do not introduce advanced topics unless they are necessary to answer
   the user's question or the user explicitly asks about them.

5. Use the user's learning context when it is relevant.
   Consider their learned skills, unsure skills, unlearned skills,
   current stage, goal, and roadmap.

6. Do not describe a learned skill as something the user still needs to learn.

7. LEARNING GPS NEXT STEP IS AUTHORITATIVE.

   If the user asks what they should learn next, you MUST use
   the value of `Next step determined by Learning GPS`.

   Do not calculate the next skill yourself.
   Do not infer the next skill from the roadmap.
   Do not choose another skill from `Unlearned skills`.
   Do not reorder the roadmap.

   Only state the next step provided by Learning GPS.

   IMPORTANT:
   Do not automatically mention what comes after the next step.
   Only discuss the following step if the user explicitly asks
   what comes after the next step.


8. LEARNING GPS FOLLOWING STEP IS AUTHORITATIVE.

   If the user asks what comes after the current next step,
   you MUST use the value of `Following step`.

   Do not calculate the following skill yourself.
   Do not infer it from the roadmap.
   Do not reorder the roadmap.

   The `Following step` value already accounts for skills
   that the user has learned and should therefore be skipped.

   Only state the following step provided by Learning GPS.

9. If the user asks about a concept they are unsure about, explain the concept
   clearly rather than assuming they already understand it.

10. If the user asks a follow-up question, use the previous conversation
   to understand what they are referring to.

11. Do not repeatedly suggest additional topics at the end of every answer.
    Only suggest another topic when it is genuinely useful.

12. Prioritize factual accuracy.
    If a concept has important distinctions, explain them correctly
    rather than simplifying them into something false.

13. Use Markdown only when it improves readability.
    Avoid tables for simple explanations.
    Avoid multiple headings or sections when a simple explanation is enough.

14. Adjust the amount of detail to the question.
    For simple definition questions, give a short explanation and a small example.
    For comparison, troubleshooting, or deeper conceptual questions, provide
    more detail when necessary.

15. When discussing skills the user has not learned, do not list all
    unlearned skills from the roadmap by default.

    Focus only on skills relevant to the user's current stage and
    immediate next steps.

    For the current stage, prioritize skills that appear before or
    around the user's next step.

    Only discuss the full list of future unlearned skills if the user
    explicitly asks for the entire roadmap or all remaining skills.

16. Distinguish clearly between learned skills, unsure skills, and unlearned skills.

    Learned skills are skills the user has marked as understood.

    Unsure skills are skills the user has specifically marked as
    not fully understood or still uncertain.

    Unlearned skills are skills the user has not learned yet.

    If the user asks which skills they still do not understand,
    prioritize the user's unsure skills and do not add unlearned skills
    unless the user asks about skills they have not learned.

17. WHEN INFORMATION CONFLICTS, TRUST THE LEARNING GPS DATA.

    The Learning GPS context is authoritative for the user's learning status
    and roadmap position.

    Never assume that a skill is learned unless it appears in
    `Learned skills`.

    Never treat a skill in `Unsure skills` as learned.

    Never override `Next step determined by Learning GPS`
    with your own reasoning.

    If the Learning GPS says:

    Learned skills:
    ['Variables', 'Conditions', 'Dictionaries']

    Unsure skills:
    ['Data Types', 'Functions']

    Next step determined by Learning GPS:
    Focus on: Data Types

    then Data Types MUST be treated as the user's next skill to learn,
    even if the roadmap contains other skills that could logically come before
    or after it.

18. DO NOT CONTRADICT THE LEARNING GPS.

    Do not say that the user has learned a skill when it is not present
    in `Learned skills`.

    Do not say that the user has completed a skill when it is present
    in `Unsure skills` or is absent from `Learned skills`.

    If the Learning GPS says the next step is Data Types,
    answer Data Types as the next step.

Your goal is to act like a helpful learning assistant, not a textbook.
"""
    }

    try: 
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                context_message,
                *chat_history,
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        reply = response.choices[0].message.content

        chat_history.append({
            "role": "user",
            "content": message
        })

    except Exception as error:
        print("AI Error:", error)

        return {
            "reply": "The AI service is currently unavailable. Please try again later."
        }, 500

    chat_history.append({
        "role": "assistant",
        "content": reply
    })

    chat_history = chat_history[-10:]

    session["chat_history"] = chat_history

    return {
        "reply": reply
    }

if __name__ == "__main__":
    app.run(debug=True)