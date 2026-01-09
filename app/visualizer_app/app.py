from flask import Flask, jsonify, request, send_from_directory, render_template
import os
import json

app = Flask(__name__)
DATA_FOLDER = 'data'


def load_json_files(start_with=None):
    json_files = []
    for filename in os.listdir(DATA_FOLDER):
        if filename.endswith('.json'):
            if start_with is None or filename.startswith(start_with):
                file_path = os.path.join(DATA_FOLDER, filename)
                with open(file_path, 'r') as file:
                    try:
                        json_content = json.load(file)
                        json_files.append(
                            {"filename": filename, "content": json_content})
                    except json.JSONDecodeError:
                        pass
    return json_files


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/data', methods=['GET'])
def get_all_files():
    name_param = request.args.get('name')
    json_files = load_json_files(start_with=name_param)
    return jsonify(json_files)


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    app.run(debug=True)
