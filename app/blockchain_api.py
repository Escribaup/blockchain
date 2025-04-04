import json
import hashlib
from time import time
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

# Conexão com o banco PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )

# Inicializa tabela se não existir
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blocos (
            id SERIAL PRIMARY KEY,
            index_bloco INTEGER,
            timestamp DOUBLE PRECISION,
            proof INTEGER,
            previous_hash TEXT,
            documentos JSONB
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

class Blockchain:
    def __init__(self):
        self.pending_docs = []
        self.chain = self.load_chain()

    def load_chain(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT index_bloco, timestamp, proof, previous_hash, documentos FROM blocos ORDER BY index_bloco")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        chain = []
        for row in rows:
            chain.append({
                'index': row[0],
                'timestamp': row[1],
                'proof': row[2],
                'previous_hash': row[3],
                'documents': row[4]
            })
        return chain

    def get_last_block(self):
        return self.chain[-1] if self.chain else None

    def add_document(self, titulo, descricao):
        doc = {
            'titulo': titulo,
            'descricao': descricao,
            'timestamp': time()
        }
        self.pending_docs.append(doc)
        return doc

    def proof_of_work(self, previous_proof):
        new_proof = 1
        while True:
            hash_op = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_op[:4] == '0000':
                return new_proof
            new_proof += 1

    def hash(self, block):
        encoded = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'documents': self.pending_docs,
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.save_block(block)
        self.pending_docs = []
        self.chain.append(block)
        return block

    def save_block(self, block):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO blocos (index_bloco, timestamp, proof, previous_hash, documentos) VALUES (%s, %s, %s, %s, %s)",
            (block['index'], block['timestamp'], block['proof'], block['previous_hash'], Json(block['documents']))
        )
        conn.commit()
        cur.close()
        conn.close()

blockchain = Blockchain()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/adicionar_documento', methods=['POST'])
def adicionar_documento():
    data = request.get_json()
    doc = blockchain.add_document(data['titulo'], data['descricao'])
    return jsonify({'mensagem': 'Documento adicionado', 'documento': doc}), 201

@app.route('/minerar_bloco', methods=['GET'])
def minerar_bloco():
    last_block = blockchain.get_last_block()
    previous_proof = last_block['proof'] if last_block else 1
    previous_hash = blockchain.hash(last_block) if last_block else '0'
    proof = blockchain.proof_of_work(previous_proof)
    block = blockchain.create_block(proof, previous_hash)
    return jsonify({'mensagem': 'Bloco minerado com sucesso', 'bloco': block}), 200

@app.route('/blockchain', methods=['GET'])
def exibir_blockchain():
    return jsonify({
        'chain': blockchain.chain,
        'tamanho': len(blockchain.chain)
    }), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
