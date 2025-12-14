import requests
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import os
import psycopg2
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from PIL import Image
import base64

app = Flask(__name__)
# Configure CORS to allow requests from your Vercel frontend
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",  # Local development
            os.environ.get('FRONTEND_URL', '*')  # Production frontend URL
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Database configuration with error handling
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("WARNING: DATABASE_URL not set. Database features will not work.")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///temp.db'  # Fallback for testing
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    avatar = db.Column(db.LargeBinary, nullable=False)

    def json(self):
        # Convert binary avatar to base64 string for display
        avatar_base64 = None
        if self.avatar:
            avatar_base64 = f"data:image/jpeg;base64,{base64.b64encode(self.avatar).decode('utf-8')}"
        
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'avatar': avatar_base64
        }

try:
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")
except Exception as e:
    print(f"WARNING: Failed to initialize database: {str(e)}")
    print("App will continue but database features may not work")

API_KEY = os.getenv("API_KEY")
BIBLE_ID = "de4e12af7f28f599-02"

# Test
@app.route('/test', methods=['GET'])
def test():
    return make_response(jsonify({'message': 'Test successful'}), 200)

# Sign up
@app.route('/api/users', methods=['POST'])
def signup():
    try:
        # Get form data instead of JSON
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        avatar_file = request.files.get('avatar')
        
        if not username or not email or not password:
            return make_response(jsonify({"error": "Username, email, and password are required"}), 400)
        
        # Hash the password before storing
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Read avatar file if provided
        avatar_bytes = avatar_file.read() if avatar_file else None
        
        new_user = Users(username=username, email=email, password=hashed_password.decode('utf-8'), avatar=avatar_bytes)
        db.session.add(new_user)
        db.session.commit()
        return make_response(jsonify({"id": new_user.id, "username": new_user.username, "email": new_user.email}), 201)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Login
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return make_response(jsonify({"error": "Email and password are required"}), 400)
        
        # Find user by email
        user = Users.query.filter_by(email=email).first()
        
        if not user:
            print(f"User not found with email: {email}")
            return make_response(jsonify({"error": "Invalid credentials"}), 401)
        
        print(f"Found user: {user.email}")
        print(f"Stored password hash starts with: {user.password[:10]}")
        
        # Check password
        try:
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                return make_response(jsonify({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }), 200)
            else:
                print("Password check failed")
                return make_response(jsonify({"error": "Invalid credentials"}), 401)
        except Exception as bcrypt_error:
            print(f"Bcrypt error: {str(bcrypt_error)}")
            print("This likely means the password in DB is not bcrypt-hashed")
            return make_response(jsonify({"error": "Invalid credentials"}), 401)
    except Exception as e:
        print(f"Login error: {str(e)}")
        return make_response(jsonify({"error": str(e)}), 500)

# Get all users
@app.route("/api/users", methods=['GET'])
def get_users():
    try:
        users = Users.query.all()
        users_data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
        return jsonify(users_data), 200
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Get user by id
@app.route('/api/users/<int:id>', methods=['GET'])
def get_user(id):
    try:
        user = Users.query.filter_by(id=id).first()
        if user:
            user_data = user.json()
            return make_response(jsonify({"user": user_data}), 200)
        else:
            return make_response(jsonify({"error": "User not found"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Update user by id
@app.route('/api/users/<int:id>', methods=['PUT'])
def update_user(id):
    try:
        user = Users.query.filter_by(id=id).first()
        if user:
            data = request.get_json()
            user.username = data['username']
            user.email = data['email']
            user.password = data['password']
            db.session.commit()
            return make_response(jsonify({"user": user.json()}), 200)
        else:
            return make_response(jsonify({"error": "User not found"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Delete user by id
@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        user = Users.query.filter_by(id=id).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            return make_response(jsonify({"message": "User deleted successfully"}), 200)
        else:
            return make_response(jsonify({"error": "User not found"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Get bible
@app.route('/api/bibles')
def get_bibles():
    book = request.args.get('book', 'GEN')
    chapter = request.args.get('chapter', '1')
    
    chapter_id = f"{book}.{chapter}"
    url = f"https://rest.api.bible/v1/bibles/{BIBLE_ID}/chapters/{chapter_id}"
    
    response = requests.get(url, headers={"api-key": API_KEY})
    return {"response": response.json()}

# Get books
@app.route("/api/books")
def get_books():
    url = f"https://rest.api.bible/v1/bibles/{BIBLE_ID}/books"
    
    response = requests.get(url, headers={"api-key": API_KEY})
    return {"response": response.json()}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4000))
    app.run(host='0.0.0.0', port=port, debug=False)