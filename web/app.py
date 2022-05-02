from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from chat import get_response

app = Flask(__name__)


@app.get('/')
def index():
    return render_template('base.html')


@app.post('/predict')
def predict():
    text = request.get_json().get('message')
    response = get_response(text)
    return jsonify({'response': response})


if __name__ == '__main__':
    app.run(debug=True)
