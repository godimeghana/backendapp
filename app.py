from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import psycopg2
import psycopg2.extras

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "http://localhost:4200"}})

DB_HOST = "localhost"
DB_NAME = "document"
DB_USER = "postgres"
DB_PASS = "mini"

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=5433,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

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
