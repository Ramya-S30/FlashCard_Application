from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import random

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb://localhost:27017")
db = client.flashfocus

flashcards_col = db.flashcards
mistakes_col = db.mistakes

def serialize_flashcard(doc):
    return {
        "_id": str(doc["_id"]),
        "question": doc["question"],
        "answer": doc["answer"],
        "hint": doc.get("hint", ""),
        "difficulty": doc.get("difficulty", "")
    }

@app.route("/flashcards", methods=["GET"])
def get_flashcards():
    cards = list(flashcards_col.find())
    return jsonify([serialize_flashcard(c) for c in cards])

@app.route("/flashcards", methods=["POST"])
def add_flashcard():
    data = request.get_json()
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()
    hint = data.get("hint", "").strip()
    difficulty = data.get("difficulty", "").strip()

    if not question or not answer or not difficulty:
        return jsonify({"error": "Question, answer, and difficulty required"}), 400

    new_card = {
        "question": question,
        "answer": answer,
        "hint": hint,
        "difficulty": difficulty
    }
    res = flashcards_col.insert_one(new_card)
    new_card["_id"] = str(res.inserted_id)
    return jsonify(new_card), 201

@app.route("/flashcards/<id>", methods=["DELETE"])
def delete_flashcard(id):
    try:
        oid = ObjectId(id)
    except:
        return jsonify({"error": "Invalid id"}), 400
    res = flashcards_col.delete_one({"_id": oid})
    if res.deleted_count == 0:
        return jsonify({"error": "Flashcard not found"}), 404
    mistakes_col.delete_many({"flashcard_id": id})

    return jsonify({"message": "Deleted"}), 200

@app.route("/quiz", methods=["GET"])
def get_quiz():
    cards = list(flashcards_col.find())
    if not cards:
        return jsonify({"error": "No flashcards"}), 404
    card = random.choice(cards)
    return jsonify(serialize_flashcard(card))

@app.route("/answer", methods=["POST"])
def check_answer():
    data = request.get_json()
    id = data.get("id", "")
    user_answer = data.get("answer", "").strip().lower()

    if not id or not user_answer:
        return jsonify({"error": "id and answer required"}), 400

    try:
        oid = ObjectId(id)
    except:
        return jsonify({"error": "Invalid id"}), 400

    card = flashcards_col.find_one({"_id": oid})
    if not card:
        return jsonify({"error": "Flashcard not found"}), 404

    correct_answer = card["answer"].strip().lower()

    if user_answer == correct_answer:
        mistakes_col.delete_many({"flashcard_id": id})
        return jsonify({"correct": True})
    else:
        mistakes_col.update_one({"flashcard_id": id}, {"$set": {"flashcard_id": id}}, upsert=True)
        return jsonify({"correct": False, "correct_answer": card["answer"]})

@app.route("/mistakes", methods=["GET"])
def get_mistakes():
    mistakes = list(mistakes_col.find())
    mistake_ids = [m["flashcard_id"] for m in mistakes]
    return jsonify(mistake_ids)
@app.route('/')
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
