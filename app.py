from datetime import datetime
import os
from flask import Flask, json,request,jsonify, send_file
import psycopg2
from mcp import mcp_tools,update_task,create_tasks,delete_task
from db_config import DB_CONFIG
from psycopg2.extras import RealDictCursor
from groq import Groq
import requests 
from flask_jwt_extended import JWTManager,create_access_token, get_jwt_identity,jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
import time
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

def execute_query(query, params = None, fetch=False):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
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

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = os.getenv("API_URL")

def get_embedding(text):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "x-wait-for-model": "true" 
    }
    
    API_URL = os.getenv("HUGGING_FACE_URL")
    
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

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password required"}), 400

    hashed_password = generate_password_hash(data["password"])

    execute_query(
        "INSERT INTO users (email, password) VALUES (%s, %s)",
        (data["email"], hashed_password)
    )

    return jsonify({"message": "User created"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password required"}), 400

    user = execute_dict_query(
        "SELECT userid, password FROM users WHERE email = %s",
        (data["email"],),
        fetch=True
    )
    stored_hash = user[0]["password"]

    if not user or not check_password_hash(stored_hash, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    user_id = user[0]["userid"]

    access_token = create_access_token(identity=str(user_id))

    return jsonify({"access_token": access_token}), 200

@app.route("/create_task", methods=["POST"])
@jwt_required()
def create_task():
    userid = get_jwt_identity()
    data = request.get_json()
    required_fields = ["title", "description", "status", "priority", "due_date"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    query = """INSERT INTO tasks (title,userid, description, status, priority, due_date) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"""
    params = (
        data["title"],
        userid,
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
@jwt_required()
def get_task_by_id():
    task_id = request.args.get("id")
    userid = get_jwt_identity()

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
@jwt_required()
def create_session():
    userid = int(get_jwt_identity())
    data = request.get_json()
    required_fields = ["created_at"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    query = """INSERT INTO chat_sessions (user_id,created_at) VALUES (%s, %s) RETURNING session_id"""
    params = (
        userid,
        data["created_at"]
    )
    try:
        session_id = execute_query(query, params, fetch=True)[0][0]
        return jsonify({"message": "Session created successfully","session_id": session_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat/history", methods=["GET"])
@jwt_required()
def chat_history():
    userid = get_jwt_identity()
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
@jwt_required()
def send_message():
    userid = get_jwt_identity()
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
@jwt_required()
def ingest():
    userid = get_jwt_identity()
    data = request.get_json()
    required_fields = ["content"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    try:
        embedding = get_embedding(data["content"])
        query = """INSERT INTO knowledge_base (user_id, content, embedding) VALUES (%s, %s, %s) RETURNING id"""
        params = (userid, data["content"], embedding)
        record_id = execute_query(query, params, fetch=True)[0][0]
        
        return jsonify({"message": "Success", "id": record_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search', methods=['POST'])
@jwt_required
def search_knowledge():
    userid = get_jwt_identity()
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
@jwt_required()
def agent_chat():
    userid = get_jwt_identity()
    data = request.get_json()
    user_query = data.get("message")
    session_id = request.args.get('session_id')
    
    history = execute_dict_query("SELECT role,content FROM messages WHERE session_id = %s ORDER BY msg_time DESC LIMIT 5",(session_id,),fetch=True)
    history_chat = [{"role":row['role'],"content"   :row['content']} for row in reversed(history)]
    query_vector = get_embedding(user_query)
    #IF TASK RELATED
        
    search_results = execute_dict_query(
            "SELECT content FROM knowledge_base ORDER BY embedding <=> %s::vector LIMIT 2", 
            (query_vector,), fetch=True)
    kb_context = "Relevant Knowledge Notes: \n" + "\n".join([r['content'] for r in search_results])
    
    task_results = execute_dict_query("SELECT title,description,status,priority FROM tasks WHERE userid = %s",(userid,),fetch=True)
    task_context = "Current tasks:\n" + "\n".join([f"- {t['title']} (Priority: {t['priority']}, Status: {t['status']}, Description : {t['description']}" for t in task_results])
    #KNOWLEDGE RELATED
        
    system_prompt = f"""
                    You are Vishal's Personal Assistant. 
                    Use the following retrieved context to answer the user's question accurately.
                    GUIDELINES:
                        1. Be direct and concise. Use "I" (e.g., "I have updated the task").
                        2. If a user says they DID NOT finish a task or want to REVERT, update the status to 'In Progress' or 'Pending' accordingly.
                        3. Look for the actual intent, not just keywords like "complete".

                    KNOWLEDGE: 
                    {kb_context}
                    
                    TASK:
                    {task_context}
                    Use this information to answer the user. If they ask about work, look at both tasks and notes.
                    If you need to take an action (create, update, or delete a task), use the appropriate tool.
                    Do not output command text.
                    """

    completion = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": system_prompt}
    ] + history_chat + [
        {"role": "user", "content": data.get("message")}
    ],
    tools=mcp_tools,
    tool_choice="auto"
    )

    choice = completion.choices[0]

    final_response = choice.message.content or ""

    if choice.finish_reason == "tool_calls":
        tool_call = choice.message.tool_calls[0]

        tool_name = tool_call.function.name
        args = tool_call.function.arguments
        args = json.loads(tool_call.function.arguments)
        try:
            if tool_name == "update_task":
                update_task(userid, **args)
                final_response = "I’ve updated the task."

            elif tool_name == "create_tasks":
                create_tasks(userid, **args)
                final_response = "I’ve created the task."

            elif tool_name == "delete_task":
                delete_task(userid, **args)
                final_response = "I’ve deleted the task."
        except Exception as e:
            final_response = f"Failed to execute {tool_name}: {str(e)}"
    
    execute_query("INSERT INTO messages (session_id,role,content,msg_time) VALUES (%s,%s,%s,%s)",(session_id,'user',data.get("message"),datetime.now()))
    execute_query("INSERT INTO messages (session_id,role,content,msg_time) VALUES (%s,%s,%s,%s)",(session_id,'assistant',final_response,datetime.now()))
    return jsonify({"response": final_response})

if __name__ == '__main__':    
    app.run(host="0.0.0.0",port=3400,debug=True)