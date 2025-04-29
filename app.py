# 更新日期: 当前
# 作者: Claude 3.7 Sonnet
# 描述: 修改app.py以适应生产环境部署，添加从环境变量获取端口的逻辑，增加调试信息，添加Flask-CORS支持和 /api/query 端点以供外部API调用

from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from flask_cors import CORS # Import CORS
import uuid
import secrets
import os
import sys

# 调试信息：打印环境变量和系统信息
print(f"Python version: {sys.version}")
print(f"SUPABASE_DB_URI 是否存在: {'是' if os.getenv('SUPABASE_DB_URI') else '否'}")
if os.getenv('SUPABASE_DB_URI'):
    # 只打印URI的前10个字符，避免泄露敏感信息
    print(f"SUPABASE_DB_URI前缀: {os.getenv('SUPABASE_DB_URI')[:10]}...")

# 在导入agent_core前先打印调试信息
try:
    from agent_core import run_agent_with_key
    print("成功导入agent_core")
except Exception as e:
    print(f"导入agent_core失败: {e}")

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = secrets.token_hex(16)  # Needed for session management
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes session timeout

# Initialize CORS - Allow all origins for now
# In production, you might want to restrict this to specific origins:
# CORS(app, resources={r"/api/*": {"origins": "https://your-friend-frontend.com"}})
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route("/", methods=["GET", "POST"])
def index():
    # Initialize conversation history if it doesn't exist
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    
    # Generate a unique session ID if one doesn't exist
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    if request.method == "POST":
        user_input = request.form.get("user_input", "")
        
        # Get API key from form or session
        user_key = request.form.get("api_key", "")
        if user_key:
            # Store API key in session for future use
            session['api_key'] = user_key
        elif 'api_key' in session:
            user_key = session['api_key']
        
        # If we have both input and key, process the request
        if user_input and user_key:
            # Use a unique session ID for each API call if needed, or manage sessions
            # For simplicity, let's generate a new one for each web UI post for now
            session_id_for_call = str(uuid.uuid4()) 
            result = run_agent_with_key(user_input, user_key, session_id_for_call)
            
            # Add to conversation history (only relevant for the web UI session)
            session['conversation_history'].append({
                'user_input': user_input,
                'response': result
            })
            
            # Update session to save changes
            session.modified = True
            
            # If it's an AJAX request (from the web UI's JS)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'response': result,
                    'success': True
                })
    
    return render_template(
        "index.html", 
        conversation_history=session.get('conversation_history', []),
        api_key=session.get('api_key', '')
    )

@app.route("/reset_conversation", methods=["POST"])
def reset_conversation():
    # Clear the conversation history
    session['conversation_history'] = []
    
    # Generate a new session ID
    session['session_id'] = str(uuid.uuid4())
    
    # Keep the API key
    api_key = session.get('api_key', '')
    
    # If it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': '对话已重置'
        })
    
    # If it's a regular form submission
    return redirect(url_for('index'))

# New dedicated API endpoint
@app.route("/api/query", methods=["POST"])
def api_query():
    # Expect JSON input for the API
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    user_input = data.get("user_input")
    user_key = data.get("api_key")
    session_id = data.get("session_id") # Optional: client can manage session ID

    if not user_input or not user_key:
        return jsonify({"error": "Missing user_input or api_key in JSON payload"}), 400

    # Generate a new session ID if not provided by the client
    if not session_id:
        session_id = str(uuid.uuid4())
        
    try:
        # Call the core agent function
        result = run_agent_with_key(user_input, user_key, session_id)
        return jsonify({
            "success": True,
            "response": result,
            "session_id": session_id # Return session_id used
        }), 200
    except Exception as e:
        print(f"API Error: {e}") # Log the error server-side
        return jsonify({"error": "An internal error occurred"}), 500

if __name__ == "__main__":
    # 获取环境变量中的端口或使用默认端口5000
    port = int(os.environ.get('PORT', 5000))
    # 在生产环境中禁用debug模式
    debug = os.environ.get('FLASK_ENV', 'production') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
