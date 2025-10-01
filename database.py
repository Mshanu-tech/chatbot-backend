import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",   # your MySQL password
    port="3307",
    database="chatbot"
)

cursor = db.cursor(dictionary=True)
