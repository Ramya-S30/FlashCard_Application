from flask_pymongo import PyMongo
from bson import ObjectId

mongo = None

def init_db(app):
    global mongo
    app.config["MONGO_URI"] = "mongodb+srv://KEERTHISREE:keerthi1105@cluster0.kwhml3.mongodb.net/flashfocus?retryWrites=true&w=majority&appName=Cluster0"
    mongo = PyMongo(app)

def add_flashcard(data):
    return mongo.db.flashcards.insert_one(data).inserted_id

def get_flashcards():
    return [{**doc, "_id": str(doc["_id"])} for doc in mongo.db.flashcards.find()]

def delete_flashcard(flashcard_id):
    result = mongo.db.flashcards.delete_one({"_id": ObjectId(flashcard_id)})
    

    return result.deleted_count

def get_flashcard_by_id(flashcard_id):
    return mongo.db.flashcards.find_one({"_id": ObjectId(flashcard_id)})
