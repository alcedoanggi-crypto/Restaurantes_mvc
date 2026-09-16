"""Punto de entrada. Uso:  flask --app run run  |  python run.py"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
