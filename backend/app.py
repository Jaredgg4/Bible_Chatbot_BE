import requests
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import os
import psycopg2
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from PIL import Image
import base64
from dotenv import load_dotenv

load_dotenv()

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
    # Fix for Render: SQLAlchemy requires 'postgresql://' but Render may provide 'postgres://'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    avatar = db.Column(db.LargeBinary, nullable=False)
    notes = db.relationship('Notes', backref='user', lazy=True)

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
            'avatar': avatar_base64,
            'notes': [note.json() for note in self.notes]
        }

class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def json(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'user_id': self.user_id
        }

class Verses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    verse = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def json(self):
        return {
            'id': self.id,
            'verse': self.verse,
            'user_id': self.user_id
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

print("=" * 50)
print("Flask app initialized successfully")
print(f"DATABASE_URL set: {bool(os.environ.get('DATABASE_URL'))}")
print(f"API_KEY set: {bool(API_KEY)}")
print(f"FRONTEND_URL: {os.environ.get('FRONTEND_URL', 'Not set')}")
print("=" * 50)

# Root route for health check
@app.route('/', methods=['GET'])
def root():
    return make_response(jsonify({'status': 'ok', 'message': 'Bible Chatbot API is running'}), 200)

# Test route
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

#Save User Note
@app.route('/api/users/<int:id>/notes', methods=['POST'])
def save_user_note(id):
    try:
        user = Users.query.filter_by(id=id).first()
        if user:
            data = request.get_json()
            new_note = Notes(
                title=data.get('title'),
                content=data.get('content'),
                user_id=id
            )
            db.session.add(new_note)
            db.session.commit()
            return make_response(jsonify({"message": "Note saved successfully", "note": new_note.json()}), 201)
        else:
            return make_response(jsonify({"error": "User not found"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

@app.route('/api/users/<int:id>/verses', methods=['POST'])
def save_user_verse(id):
    try:
        user = Users.query.filter_by(id=id).first()
        if user:
            data = request.get_json()
            new_verse = Verses(
                verse=data.get('verse'),
                user_id=id
            )
            db.session.add(new_verse)
            db.session.commit()
            return make_response(jsonify({"message": "Verse saved successfully", "verse": new_verse.json()}), 201)
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

@app.route("/api/scripture")
def get_scripture():
    verse_id = request.args.get('verse_id', 'GEN.1.1')
    url = f"https://rest.api.bible/v1/bibles/{BIBLE_ID}/verses/{verse_id}"
    
    response = requests.get(url, headers={"api-key": API_KEY})
    return {"response": response.json()}

@app.route("/api/chapter")
def get_chapter():
    chapter_id = request.args.get('chapter_id', 'GEN.1')
    
    url = f"https://rest.api.bible/v1/bibles/{BIBLE_ID}/chapters/{chapter_id}/verses"
    
    response = requests.get(url, headers={"api-key": API_KEY})
    return {"response": response.json()}
    

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4000))
    app.run(host='0.0.0.0', port=port, debug=False)