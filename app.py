import datetime
import os
from flask import Flask,request,jsonify, send_file
import psycopg2
from db_config import DB_CONFIG
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import requests
import time
from groq import Groq
import certifi
import os

os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
os.environ["SSL_CERT_FILE"] = certifi.where()

load_dotenv()
app = Flask(__name__)

# API Configurations
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = os.getenv("HF_EMBEDDING_MODEL")
HF_API_BASE = os.getenv("HF_API_BASE")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")


client = Groq(api_key=GROQ_API_KEY)

def get_embedding(text):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "x-wait-for-model": "true" 
    }
    API_URL = f"{HF_API_BASE}/{MODEL_ID}/pipeline/feature-extraction"
    
    response = requests.post(API_URL, headers=headers, json={"inputs": text})
    
    if response.status_code == 200:
        result = response.json()

        while isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            result = result[0]
        return result
    else:
        fallback_url = f"https://router.huggingface.co/hf-inference/models/{MODEL_ID}"
        response = requests.post(fallback_url, headers=headers, json={"inputs": text})
        if response.status_code == 200:
            return response.json()[0]
        raise Exception(f"HF API Error: {response.status_code} - {response.text}")

def execute_query(query, params = None, fetch=False):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT current_database(), inet_server_port(), current_schema()")
    print("DB DEBUG:", cur.fetchone())
    try:
        print(query,params)
        cur.execute(query, params)
        conn.commit()
        if fetch:
            result = cur.fetchall()
        else:
            result = None
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def execute_dict_query(query, params = None, fetch=False):
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            print(query,params)
            cur.execute(query, params)
            conn.commit()
            if fetch:
                result = cur.fetchall()
            else:
                result = None
            return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

@app.route("/create_task", methods=["POST"])
def create_task():
    data = request.get_json()
    required_fields = ["title", "description", "status", "priority", "due_date","userid"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    query = """INSERT INTO tasks (title,userid, description, status, priority, due_date) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"""
    params = (
        data["title"],
        data["userid"],
        data["description"],
        data["status"],
        data["priority"],
        data["due_date"],
    )
    try:
        task_id = execute_query(query, params, fetch=True)[0][0]
        return jsonify({"message": "Task created successfully","task_id": task_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_tasks", methods=["GET"])
def get_task_by_id():
    task_id = request.args.get("id")

    if not task_id:
        return jsonify({"error": "Task id is required"}), 400

    query = """SELECT id, title, description, status, priority, due_date,userid FROM tasks WHERE id = %s"""
    try:
        result = execute_dict_query(query, (task_id,), fetch=True)
        if not result:
            return jsonify({"error": "Task not found"}), 404

        task = result[0]
        return jsonify(task), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat/session", methods=["POST"])
def create_session():
    data = request.get_json()
    required_fields = ["userid","created_at"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    query = """INSERT INTO chat_sessions (user_id,created_at) VALUES (%s, %s) RETURNING session_id"""
    params = (
        data["userid"],
        data["created_at"]
    )
    try:
        session_id = execute_query(query, params, fetch=True)[0][0]
        return jsonify({"message": "Session created successfully","session_id": session_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat/history", methods=["GET"])
def chat_history():
    session_id = request.args.get("session_id")
    array = []
    if not session_id:
        return jsonify({"error": "Session id is required"}), 400

    query = """SELECT role, content,msg_time FROM messages WHERE session_id = %s ORDER BY msg_time ASC"""
    try:
        result = execute_dict_query(query, (session_id,), fetch=True)
        if not result:
            return jsonify({"error": "Session not found"}), 404
        msg = result
        for i in msg:
            array.append(i)
        return jsonify(array), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat/messages',methods=['POST'])
def send_message():
    data = request.get_json()
    required_fields = ["session_id","role","content","msg_time"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    query = """INSERT INTO messages (session_id,role,content,msg_time) VALUES (%s, %s, %s, %s) RETURNING id"""
    params = (data["session_id"],data["role"],data["content"],data["msg_time"])
    try:
        id = execute_query(query, params, fetch=True)[0][0]
        return jsonify({"message": "Message sent successfully","id": id}), 201
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

@app.route('/ingest',methods=['POST'])
def ingest():
    data = request.get_json()
    required_fields = ["userid","content"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    try:
        embedding = get_embedding(data["content"])
        print('doing')
        query = """INSERT INTO knowledge_base (user_id, content, embedding) VALUES (%s, %s, %s) RETURNING id"""
        params = (data["userid"], data["content"], embedding)
        record_id = execute_query(query, params, fetch=True)[0][0]
        
        return jsonify({"message": "Success", "id": record_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search', methods=['POST'])
def search_knowledge():
    data = request.get_json()
    if "query" not in data:
        return jsonify({"error": "Missing search query"}), 400

    try:
        query_vector = get_embedding(data["query"])
        query = """SELECT content, 1 - (embedding <=> %s::vector) AS similarity  FROM knowledge_base  ORDER BY similarity DESC  LIMIT 3"""

        results = execute_dict_query(query, (query_vector,), fetch=True)

        return jsonify({"query": data["query"],"matches":results }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/agent/chat', methods=['POST'])
def agent_chat():
    data = request.get_json()
    user_query = data.get("message")
    
    query_vector = get_embedding(user_query)
    search_results = execute_dict_query(
        "SELECT content FROM knowledge_base ORDER BY embedding <=> %s::vector LIMIT 2", 
        (query_vector,), fetch=True
    )
    
    context = "\n".join([r['content'] for r in search_results])

    system_prompt = f"""
    You are Vishal's Personal Assistant. 
    Use the following retrieved context to answer the user's question accurately.
    Context: {context}
    
    If the context doesn't have the answer, use your own knowledge but mention that it's not in the records.
    """

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    )
    return jsonify({"response": completion.choices[0].message.content})

if __name__ == '__main__':    
    app.run(host="0.0.0.0",port=3400,debug=True)   