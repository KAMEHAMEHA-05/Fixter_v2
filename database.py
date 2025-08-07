from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt

def insert_document(json_data, collection):
    CONNECTION_STRING = "mongodb://localhost:27017/" 
    try:
        client = MongoClient(CONNECTION_STRING)
        db = client['Fixter']
        issues_collection = db[collection]
        result = issues_collection.insert_one(json_data)

        print(f"Document inserted with _id: {result.inserted_id}")
        return str(result.inserted_id)

    except Exception as e:
        print(f"Error inserting into MongoDB: {e}")
        return None
    
def update_field(issue_id, field_name, new_value, collection_name="Issues"):
    try:
        client = MongoClient("mongodb://localhost:27017")
        db = client['Fixter']
        collection = db[collection_name]

        result = collection.update_one(
            {"_id": ObjectId(issue_id)},
            {"$set": {field_name: new_value}}
        )

        if result.matched_count > 0:
            print(f"Updated field '{field_name}' to '{new_value}' in document {issue_id}")
            return True
        else:
            print("No document found with that _id.")
            return False
    except Exception as e:
        print(f"Error updating document: {e}")
        return False
    
def move_to_collection(issue_id, source_collection="Issues", target_collection="Resolved"):
    try:
        client = MongoClient("mongodb://localhost:27017")
        db = client['Fixter']
        source = db[source_collection]
        target = db[target_collection]

        doc = source.find_one({"_id": ObjectId(issue_id)})
        if not doc:
            print("No document found with that _id.")
            return False
        target.insert_one(doc)

        source.delete_one({"_id": ObjectId(issue_id)})

        print(f"Moved issue {issue_id} from '{source_collection}' to '{target_collection}'.")
        return True
    except Exception as e:
        print(f"Error moving document: {e}")
        return False

def hash_existing_resident_passwords():
    client = MongoClient("mongodb://localhost:27017")
    db = client['Fixter']
    collection = db['Resident']

    residents = collection.find()
    for resident in residents:
        if not resident.get("Password").startswith("$2b$"):  # naive check to skip already hashed ones
            hashed = bcrypt.hashpw(resident['Password'].encode('utf-8'), bcrypt.gensalt())
            collection.update_one(
                {"_id": resident["_id"]},
                {"$set": {"Password": hashed.decode('utf-8')}}
            )
            print(f"Updated password for resident {resident['Reg No']}")

def authenticate_resident(regno, password):
    client = MongoClient("mongodb://localhost:27017/")  # Update if needed
    db = client['Fixter']
    collection = db['Resident']

    resident = collection.find_one({"Reg No": regno})

    if not resident:
        print("No resident found")
        return False

    stored_hashed_pw = resident['Password']  # This is already in bytes

    if isinstance(stored_hashed_pw, str):
        stored_hashed_pw = stored_hashed_pw.encode('utf-8')  # Handle string case just in case

    if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_pw):
        return True
    else:
        return False

def get_documents(collection_name, filter_field=None, filter_value=None):
    client = MongoClient("mongodb://localhost:27017")
    db = client['Fixter']
    collection = db[collection_name]

    if filter_field and filter_value is not None:
        query = {filter_field: filter_value}
    else:
        query = {}

    try:
        documents = list(collection.find(query))
        return documents
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return []
    
def add_resident(name, regno, password):
    client = MongoClient("mongodb://localhost:27017")
    db = client['Fixter']
    collection = db['Resident']
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    if collection.find_one({"Reg No": regno}):
        print("Resident already exists.")
        return False

    try:
        collection.insert_one({
            "Name": name,
            "Reg No": regno,
            "Password": hashed_pw
        })
        print("Resident added successfully.")
        return True
    except Exception as e:
        print(f"Error adding resident: {e}")
        return False
    
def delete_resident(regno):
    client = MongoClient("mongodb://localhost:27017")
    db = client['Fixter']
    collection = db['Resident']

    try:
        result = collection.delete_one({"Reg No": regno})
        if result.deleted_count == 1:
            print("Resident deleted successfully.")
            return True
        else:
            print("Resident not found.")
            return False
    except Exception as e:
        print(f"Error deleting resident: {e}")
        return False