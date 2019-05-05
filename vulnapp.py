from app import app, db

if __name__ == "__main__":
    db.init_db("schema.sql")
    app.run(debug=False)