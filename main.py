import requests
from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = "_DyMvda2Q_Z00viGIET8A"
BIBLE_ID = "de4e12af7f28f599-02"

@app.route('/api/bibles')
def get_bibles():
    # Get book and chapter from query parameters, default to GEN.1
    book = request.args.get('book', 'GEN')
    chapter = request.args.get('chapter', '1')
    
    chapter_id = f"{book}.{chapter}"
    url = f"https://rest.api.bible/v1/bibles/{BIBLE_ID}/chapters/{chapter_id}"
    
    response = requests.get(url, headers={"api-key": API_KEY})
    return {"response": response.json()}

if __name__ == '__main__':
    app.run(debug=True)