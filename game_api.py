import os
import json
from flask import Flask, render_template, jsonify, request, send_file

app = Flask(__name__)

# Game data initialization
game_state = {
    "current_level": 0,
    "levels": ["easy", "medium", "hard"],
    "level_config": {
        "easy": {
            "use_color_hints": True,
            "labels": ["A", "1", "B", "2", "C", "3", "D", "4", "E", "5"]
        },
        "medium": {
            "use_color_hints": False,
            "labels": ["A", "1", "B", "2", "C", "3", "D", "4"]
        },
        "hard": {
            "use_color_hints": False,
            "labels": ["A", "1", "B", "2", "C", "3", "D", "4", "E", "5", "F", "6", "G", "7", "H", "8"]
        }
    },
    "level_data": {
        "easy": {
            "score": 0,
            "correct_steps": 0,
            "wrong_steps": 0,
            "round_times": [],
            "interstep_times": [],
            "step_types": []
        },
        "medium": {
            "score": 0,
            "correct_steps": 0,
            "wrong_steps": 0,
            "round_times": [],
            "interstep_times": [],
            "step_types": []
        },
        "hard": {
            "score": 0,
            "correct_steps": 0,
            "wrong_steps": 0,
            "round_times": [],
            "interstep_times": [],
            "step_types": []
        }
    },
    "game_over": False
}

# Path to store the game data in Vercel's writable /tmp directory
GAME_DATA_PATH = "/tmp/game_data.json"

# Save game state to file
def save_game_data_to_file():
    # Ensure all levels have data, even if they weren't played
    for level in game_state["levels"]:
        if level not in game_state["level_data"]:
            game_state["level_data"][level] = {
                "score": 0,
                "correct_steps": 0,
                "wrong_steps": 0,
                "round_times": [],
                "interstep_times": [],
                "step_types": []
            }
    
    with open(GAME_DATA_PATH, 'w') as file:
        json.dump(game_state, file, indent=4)

# Route to serve the game UI
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle game data updates
@app.route('/game/api', methods=['POST'])
def game_api():
    try:
        data = request.get_json()

        # Validate input
        required_fields = {"score", "correct_steps", "wrong_steps", "interstep_times", "step_types", "level_complete"}
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing fields in the request data"}), 400

        # Update level data
        current_level_name = game_state["levels"][game_state["current_level"]]
        level_data = game_state["level_data"][current_level_name]
        level_data["score"] += data["score"]
        level_data["correct_steps"] += data["correct_steps"]
        level_data["wrong_steps"] += data["wrong_steps"]
        level_data["interstep_times"].extend(data["interstep_times"])
        level_data["step_types"].extend(data["step_types"])
        if "round_time" in data:
            level_data["round_times"].append(data["round_time"])

        # Advance to the next level or end the game
        if data["level_complete"]:
            if game_state["current_level"] < len(game_state["levels"]) - 1:
                game_state["current_level"] += 1
            else:
                game_state["game_over"] = True
                save_game_data_to_file()  # Save game state when game ends

        return jsonify({"message": "Game state updated", "game_state": game_state})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to download the game data
@app.route('/download', methods=['GET'])
def download_game_data():
    try:
        # Ensure the file exists in /tmp before serving
        if not os.path.exists(GAME_DATA_PATH):
            save_game_data_to_file()

        return send_file(GAME_DATA_PATH, as_attachment=True, download_name='game_data.json')
    except Exception as e:
        return jsonify({"error": f"Error downloading file: {str(e)}"}), 500

# Route for the thank you page
@app.route('/thankyou')
def thank_you():
    return render_template('thankyou.html')

if __name__ == '__main__':
    app.run(debug=True)
