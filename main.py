import requests
from flask import Flask, request
from flask_cors import CORS
import os
import psycopg2

app = Flask(__name__)
CORS(app)

db_password = os.getenv("db_password")
API_KEY = os.getenv("API_KEY")
BIBLE_ID = "de4e12af7f28f599-02"

con = psycopg2.connect(host= "localhost", user= "postgres", password= db_password, port= "5432", database= "postgres")

cursor = con.cursor()


con.commit()

cursor.close()
con.close()

@app.route('/api/bibles')
def get_bibles():
    book = request.args.get('book', 'GEN')
    chapter = request.args.get('chapter', '1')
    
    chapter_id = f"{book}.{chapter}"
    url = f"https://rest.api.bible/v1/bibles/{BIBLE_ID}/chapters/{chapter_id}"
    
    response = requests.get(url, headers={"api-key": API_KEY})
    return {"response": response.json()}

@app.route("/api/books")
def get_books():
    url = f"https://rest.api.bible/v1/bibles/{BIBLE_ID}/books"
    
    response = requests.get(url, headers={"api-key": API_KEY})
    return {"response": response.json()}

if __name__ == '__main__':
    app.run(debug=True)