import os
import base64
import logging
import time
import requests
import numpy as np
import tensorflow as tf
from flask import Flask, request, jsonify
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

# Initialize Flask app
app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO)

# FoodData Central API key
FD_CENTRAL_API_KEY = 'wH2MGeO7wecJWKEiKFMPBDMrzrnKiT1pty5q1yqD'

# Load the pre-trained CNN model
model = tf.keras.models.load_model('models/trained_model/fine_tuned_model.keras')

# Load the Food-101 class labels
with open('C:/Users/skyra/FoodAnalyzer/datasets/real_food101_dataset/food-101/meta/classes.txt') as f:
    food101_labels = [line.strip() for line in f.readlines()]

# Path for the images folder
IMAGES_FOLDER = os.path.join(os.path.dirname(__file__), 'images')
if not os.path.exists(IMAGES_FOLDER):
    os.makedirs(IMAGES_FOLDER)

def process_image(food_name):
    """Query FoodData Central API for nutritional information based on food name."""
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={food_name}&api_key={FD_CENTRAL_API_KEY}"
    
    logging.info(f"Sending query to USDA API: {url}")
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            logging.error(f"API request failed with status code {response.status_code}")
            return {"error": "API request failed"}

        search_results = response.json()
        logging.info(f"USDA API response: {search_results}")
        
        if 'foods' not in search_results or not search_results['foods']:
            logging.warning(f"No food items found for the given name: {food_name}")
            return {"error": "No food items found"}

        # Iterate through search results to find valid nutrition data
        for food in search_results['foods']:
            fdc_id = food.get('fdcId')
            if not fdc_id:
                logging.warning(f"Invalid fdcId for food: {food_name}")
                continue  # Try the next food item

            # Fetch detailed nutritional data using fdcId
            nutrition_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={FD_CENTRAL_API_KEY}"
            nutrition_response = requests.get(nutrition_url)
            
            if nutrition_response.status_code != 200:
                logging.error(f"Nutrition request failed with status code {nutrition_response.status_code} for fdcId {fdc_id}")
                continue  # Try the next food item
            
            nutrition_data = nutrition_response.json()
            logging.info(f"Nutrition data fetched for {food_name} (fdcId: {fdc_id}): {nutrition_data}")

            # Check if nutrition data exists
            if 'foodNutrients' not in nutrition_data or not nutrition_data['foodNutrients']:
                logging.warning(f"No nutrition data found for {food_name} (fdcId: {fdc_id})")
                continue  # Try the next food item

            # Extract relevant label nutrients
            relevant_nutrients = [
                'Energy', 'Protein', 'Carbohydrate, by difference', 'Total lipid (fat)',
                'Fiber, total dietary', 'Sodium, Na', 'Vitamin A', 'Vitamin C, total ascorbic acid',
                'Calcium, Ca', 'Iron, Fe'
            ]
            label_nutrients = {}
            
            for nutrient in nutrition_data['foodNutrients']:
                nutrient_name = nutrient.get('nutrient', {}).get('name', '')
                if nutrient_name in relevant_nutrients:
                    value = nutrient.get('amount', 'N/A')
                    unit = nutrient.get('nutrient', {}).get('unitName', '')
                    if value != 'N/A' and nutrient_name:
                        label_nutrients[nutrient_name] = f"{value} {unit}"

            if label_nutrients:
                logging.info(f"Label nutrients extracted for {food_name}: {label_nutrients}")
                return {
                    "food_name": food_name,
                    "nutrition_info": label_nutrients  # Return filtered nutrients
                }
            else:
                logging.warning(f"No valid label nutrients found for {food_name} (fdcId: {fdc_id})")
        
        return {"error": "No valid label nutrients found"}

    except requests.exceptions.RequestException as err:
        logging.error(f"Error fetching nutrition info: {err}")
        return {"error": "Unable to fetch nutrition information"}

def predict_food(image_path):
    """Run the captured image through the CNN model to get food prediction."""
    start_time = time.time()

    try:
        img = image.load_img(image_path, target_size=(224, 224))
        logging.info("Image loaded successfully.")
    except Exception as e:
        logging.error("Error loading image: %s", str(e))
        raise

    x = image.img_to_array(img)
    x = preprocess_input(x)
    x = np.expand_dims(x, axis=0)

    preds = model.predict(x)
    logging.info(f"Prediction result: {preds}")

    class_index = np.argmax(preds, axis=1)[0]
    food_item = food101_labels[class_index]

    logging.info("Predicted food item: %s", food_item)
    logging.info("Total processing time: %s seconds", time.time() - start_time)

    return food_item

@app.route('/api/capture', methods=['POST'])
def capture_endpoint():
    logging.info("Received image capture request.")
    
    # Get the image data from the request
    data = request.json
    image_base64 = data.get('image')

    # Log the length of the base64 string to verify it's being received properly
    if image_base64:
        logging.info(f"Received Base64 image data length: {len(image_base64)}")  # Log length of the base64 string
        logging.info(f"Base64 image (first 3000 characters): {image_base64[:3000]}")
    else:
        logging.warning("No image data received")
        return jsonify({"error": "Image data is required"}), 400

    # Remove potential base64 header (e.g., 'data:image/jpeg;base64,')
    if ',' in image_base64:
        image_base64 = image_base64.split(',')[1]

    os.makedirs(IMAGES_FOLDER, exist_ok=True)

    # Create a unique image name to prevent overwriting
    image_path = os.path.join(IMAGES_FOLDER, f'received_image_{int(time.time())}.jpg')
    logging.info("Saving image to path: %s", image_path)

    try:
        with open(image_path, "wb") as img_file:
            img_file.write(base64.b64decode(image_base64))
        logging.info("Image saved successfully: %s", image_path)
    except Exception as e:
        logging.error("Error saving image: %s", str(e))
        return jsonify({"error": "Failed to save image"}), 500

    try:
        food_name = predict_food(image_path)
    except Exception as e:
        logging.error("Error predicting food: %s", str(e))
        return jsonify({"error": "Food prediction failed"}), 500

    logging.info(f"Predicted food item: {food_name}")

    result = process_image(food_name)

    if "error" in result:
        return jsonify(result), 500  

    return jsonify({
        "food_name": result["food_name"], 
        "nutrition_info": result["nutrition_info"]
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
