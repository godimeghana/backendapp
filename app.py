from flask import Flask, request, jsonify,send_from_directory, render_template_string
from flask_cors import CORS
from datetime import datetime
import psycopg2
import psycopg2.extras
import os
import urllib.parse
from dotenv import load_dotenv
load_dotenv()



app = Flask(__name__,static_folder='../dist/doc-management/browser')

CORS(app, resources={r"/api/*": {"origins": "http://localhost:4200"}})
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

DATABASE_URL = os.environ.get("DATABASE_URL")

urllib.parse.uses_netloc.append("postgres")
db_url = urllib.parse.urlparse(DATABASE_URL)
print("DATABASE_URL:", DATABASE_URL)


def get_db_connection():
    conn = psycopg2.connect(
        dbname=db_url.path[1:],
        user=db_url.username,
        password=db_url.password,
        host=db_url.hostname,
        port=db_url.port,
        sslmode='require'
    )
print("Connected to DB:", db_url.path[1:])

@app.route('/documentp/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

@app.route('/documentp/')
@app.route('/documentp/<path:path>')
def index(path=None):
    index_path = os.path.join(app.static_folder, 'index.html')
    with open(index_path) as f:
        return render_template_string(f.read())

@app.route('/')
def index():
    return "Backend API is running!"

@app.route('/api/document', methods=['GET'])
def get_document():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM public.document WHERE status = 'Active'")
        rows = cur.fetchall()
        result = []
        for row in rows:
            result.append({
                'name': row['name'],
                'content': row['content'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else ''
            })
        cur.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/document', methods=['POST'])
def save_document():
    data = request.json
    name = data.get('name')
    content = data.get('content')
    current_time = datetime.now()

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        
        cur.execute("SELECT * FROM public.document WHERE name = %s", (name,))
        existing = cur.fetchone()

        if existing:
           
            cur.execute("""
                UPDATE public.document 
                SET content = %s, updated_at = %s 
                WHERE name = %s
                RETURNING *
            """, (content, current_time, name))
        else:
            
            cur.execute("""
                INSERT INTO public.document (name, content, created_at, updated_at, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
            """, (name, content, current_time, current_time, 'Active'))

        saved_doc = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        if saved_doc:
            return jsonify({
                'name': saved_doc['name'],
                'content': saved_doc['content'],
                'created_at': saved_doc['created_at'].isoformat() if saved_doc['created_at'] else '',
                'updated_at': saved_doc['updated_at'].isoformat() if saved_doc['updated_at'] else '',
                'status': saved_doc['status']
            }), 201
        else:
            return jsonify({'error': 'No document returned'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/document/<name>', methods=['DELETE'])
def delete_document(name):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE public.document SET status = 'Inactive' WHERE name = %s", (name,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Document deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
