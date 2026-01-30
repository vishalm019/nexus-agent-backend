import datetime
import os
from flask import Flask,request,jsonify, send_file
import psycopg2
from db_config import DB_CONFIG
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

def execute_query(query, params = None, fetch=False):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
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

if __name__ == '__main__':    
    app.run(host="0.0.0.0",port=3400,debug=True)   