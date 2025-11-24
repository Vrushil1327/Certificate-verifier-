import hashlib
import json
from time import time
from flask import Flask, request, jsonify


class CertificateBlockchain:
    def __init__(self):
        self.chain = []
        self.pending_certificates = []

        # genesis block
        self.new_block(previous_hash="0", proof=100)

    # Add a new certificate entry
    def add_certificate(self, student_name, cert_id, course, grade):
        cert_data = {
            "student_name": student_name,
            "certificate_id": cert_id,
            "course": course,
            "grade": grade,
        }
        self.pending_certificates.append(cert_data)
        return self.last_block['index'] + 1

    # Mine a new block for pending certificates
    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'certificates': self.pending_certificates,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        self.pending_certificates = []
        self.chain.append(block)
        return block

    # Last block
    @property
    def last_block(self):
        return self.chain[-1]

    # Block hash
    @staticmethod
    def hash(block):
        encoded = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

    # Proof of work
    def proof_of_work(self, last_proof):
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    # Validate proof
    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f"{last_proof}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# ----------------------
#       Flask App
# ----------------------

app = Flask(__name__)
blockchain = CertificateBlockchain()


# Add a certificate (College/Admin)
@app.route('/add_certificate', methods=['POST'])
def add_certificate():
    data = request.get_json()

    required = ["student_name", "certificate_id", "course", "grade"]
    if not all(field in data for field in required):
        return jsonify({"message": "Missing fields!"}), 400

    index = blockchain.add_certificate(
        data["student_name"],
        data["certificate_id"],
        data["course"],
        data["grade"]
    )

    return jsonify({"message": f"Certificate will be added to block {index}"}), 201


# Mine block (Admin)
@app.route('/mine', methods=['GET'])
def mine():
    last_proof = blockchain.last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    block = blockchain.new_block(proof)

    return jsonify({
        "message": "New block mined!",
        "index": block['index'],
        "certificates": block['certificates'],
        "proof": block['proof'],
        "previous_hash": block['previous_hash']
    }), 200


# Verify certificate (Student/Employer)
@app.route('/verify/<cert_id>', methods=['GET'])
def verify(cert_id):
    for block in blockchain.chain:
        for cert in block['certificates']:
            if cert['certificate_id'] == cert_id:
                return jsonify({
                    "status": "VALID",
                    "certificate_details": cert,
                    "block_index": block['index']
                }), 200

    return jsonify({"status": "INVALID"}), 404


# View entire blockchain
@app.route('/chain', methods=['GET'])
def full_chain():
    return jsonify({
        "length": len(blockchain.chain),
        "chain": blockchain.chain
    }), 200


# Run server
if __name__ == "__main__":
    app.run(port=5000, debug=True)
