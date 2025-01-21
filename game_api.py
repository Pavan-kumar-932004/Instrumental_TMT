from flask import Flask, render_template, jsonify, request, send_file
import json
import os

app = Flask(__name__)

# Initial game state
game_state = {
    "current_level": 0,  # 0: Easy, 1: Medium, 2: Hard
    "levels": ["easy", "medium", "hard"],  # Level names for mapping
    "level_config": {
        "easy": {"use_color_hints": True, "labels": ['A', '1', 'B', '2', 'C', '3', 'D', '4', 'E', '5']},
        "medium": {"use_color_hints": False, "labels": ['A', '1', 'B', '2', 'C', '3', 'D', '4']},
        "hard": {"use_color_hints": False, "labels": ['A', '1', 'B', '2', 'C', '3', 'D', '4', 'E', '5', 'F', '6', 'G', '7', 'H', '8']},
    },
    "level_data": {  # Stores data for all levels
        "easy": {"score": 0, "correct_steps": 0, "wrong_steps": 0, "round_times": [], "interstep_times": [], "step_types": []},
        "medium": {"score": 0, "correct_steps": 0, "wrong_steps": 0, "round_times": [], "interstep_times": [], "step_types": []},
        "hard": {"score": 0, "correct_steps": 0, "wrong_steps": 0, "round_times": [], "interstep_times": [], "step_types": []},
    },
    "game_over": False  # Indicates if all levels are completed
}

@app.route('/thankyou')
def thank_you():
    return render_template('thankyou.html')

# Function to save the game state to a file
def save_game_data_to_file():
    with open('game_data.json', 'w') as file:
        json.dump(game_state, file, indent=4)

# Function to advance to the next level
def advance_to_next_level():
    if game_state["current_level"] < len(game_state["levels"]) - 1:
        game_state["current_level"] += 1
    else:
        game_state["game_over"] = True  # Mark the game as completed

# Route to serve the game UI
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle game data updates from the client
@app.route('/game/api', methods=['POST'])
def game_api():
    try:
        data = request.get_json()

        # Validate input data
        required_fields = {"score", "correct_steps", "wrong_steps", "interstep_times", "step_types", "level_complete"}
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing fields in the request data"}), 400

        # Ensure valid data (e.g., no negative scores or steps)
        if data["score"] < 0 or data["correct_steps"] < 0 or data["wrong_steps"] < 0:
            return jsonify({"error": "Invalid data received"}), 400

        current_level_name = game_state["levels"][game_state["current_level"]]
        post_data_file = f'level_{current_level_name}_data.json'

        # Ensure the JSON file exists
        if not os.path.exists(post_data_file):
            with open(post_data_file, 'w') as file:
                json.dump([], file)

        # Load existing data from the file
        with open(post_data_file, 'r') as file:
            existing_data = json.load(file)

        # Append the new POST data
        existing_data.append(data)

        # Save the updated data back to the file
        with open(post_data_file, 'w') as file:
            json.dump(existing_data, file, indent=4)

        # Update the current level's data
        level_data = game_state["level_data"][current_level_name]
        level_data["score"] += data["score"]
        level_data["correct_steps"] += data["correct_steps"]
        level_data["wrong_steps"] += data["wrong_steps"]
        level_data["interstep_times"].extend(data["interstep_times"])
        level_data["step_types"].extend(data["step_types"])
        if "round_time" in data:
            level_data["round_times"].append(data["round_time"])

        # Advance level if complete
        if data["level_complete"]:
            advance_to_next_level()

        # Save the updated game state to a file
        save_game_data_to_file()

        return jsonify({
            "message": f"Data successfully dumped to {post_data_file} and game state updated.",
            "game_state": game_state,
            "current_level_name": current_level_name,
            "level_config": game_state["level_config"].get(current_level_name, {})
        })
    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Log the error
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)
