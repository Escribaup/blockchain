from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import hashlib
import json
from time import time

app = Flask(__name__)
CORS(app)

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_docs = []
        self.create_block(proof=1, previous_hash='0')

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'documents': self.pending_docs,
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.pending_docs = []
        self.chain.append(block)
        return block

    def get_last_block(self):
        return self.chain[-1]

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
    proof = blockchain.proof_of_work(last_block['proof'])
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(proof, previous_hash)
    return jsonify({'mensagem': 'Bloco minerado com sucesso', 'bloco': block}), 200

@app.route('/blockchain', methods=['GET'])
def exibir_blockchain():
    return jsonify({
        'chain': blockchain.chain,
        'tamanho': len(blockchain.chain)
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
