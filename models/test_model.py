import os
import numpy as np
import tensorflow as tf
from PIL import Image

# Load the model
save_dir = 'models/trained_model'
checkpoint_path = os.path.join(save_dir, 'fine_tuned_model.keras')
loaded_model = tf.keras.models.load_model(checkpoint_path)
print('Model loaded successfully.')

class_indices = {
    0: 'apple_pie', 1: 'baby_back_ribs', 2: 'baklava', 3: 'beef_carpaccio',
    4: 'beef_tartare', 5: 'beet_salad', 6: 'beignets', 7: 'bibimbap',
    8: 'bread_pudding', 9: 'breakfast_burrito', 10: 'bruschetta', 
    11: 'caesar_salad', 12: 'cannoli', 13: 'caprese_salad', 14: 'carrot_cake',
    15: 'ceviche', 16: 'cheesecake', 17: 'cheese_plate', 18: 'chicken_curry',
    19: 'chicken_quesadilla', 20: 'chicken_wings', 21: 'chocolate_cake',
    22: 'chocolate_mousse', 23: 'churros', 24: 'clam_chowder', 
    25: 'club_sandwich', 26: 'crab_cakes', 27: 'creme_brulee',
    28: 'croque_madame', 29: 'cup_cakes', 30: 'deviled_eggs', 31: 'donuts',
    32: 'dumplings', 33: 'edamame', 34: 'eggs_benedict', 35: 'escargots',
    36: 'falafel', 37: 'filet_mignon', 38: 'fish_and_chips', 39: 'foie_gras',
    40: 'french_fries', 41: 'french_onion_soup', 42: 'french_toast',
    43: 'fried_calamari', 44: 'fried_rice', 45: 'frozen_yogurt',
    46: 'garlic_bread', 47: 'gnocchi', 48: 'greek_salad',
    49: 'grilled_cheese_sandwich', 50: 'grilled_salmon', 51: 'guacamole',
    52: 'gyoza', 53: 'hamburger', 54: 'hot_and_sour_soup', 55: 'hot_dog',
    56: 'huevos_rancheros', 57: 'hummus', 58: 'ice_cream', 59: 'lasagna',
    60: 'lobster_bisque', 61: 'lobster_roll_sandwich',
    62: 'macaroni_and_cheese', 63: 'macarons', 64: 'miso_soup', 65: 'mussels',
    66: 'nachos', 67: 'omelette', 68: 'onion_rings', 69: 'oysters',
    70: 'pad_thai', 71: 'paella', 72: 'pancakes', 73: 'panna_cotta',
    74: 'peking_duck', 75: 'pho', 76: 'pizza', 77: 'pork_chop', 78: 'poutine',
    79: 'prime_rib', 80: 'pulled_pork_sandwich', 81: 'ramen', 82: 'ravioli',
    83: 'red_velvet_cake', 84: 'risotto', 85: 'samosa', 86: 'sashimi',
    87: 'scallops', 88: 'seaweed_salad', 89: 'shrimp_and_grits',
    90: 'spaghetti_bolognese', 91: 'spaghetti_carbonara', 92: 'spring_rolls',
    93: 'steak', 94: 'strawberry_shortcake', 95: 'sushi', 96: 'tacos',
    97: 'takoyaki', 98: 'tiramisu', 99: 'tuna_tartare', 100: 'waffles'
}

def preprocess_image(image_path):
    # Load and preprocess the image using MobileNetV2's preprocessing
    img = tf.keras.preprocessing.image.load_img(image_path, target_size=(224, 224))
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)
    img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
    
    return img_array

def predict_food_names(images):
    for img_path in images:
        filename = os.path.basename(img_path)
        
        processed_image = preprocess_image(img_path)
        
        # Get predictions
        predictions = loaded_model.predict(processed_image, verbose=0)
        
        # Get top 3 predictions
        top_indices = np.argsort(predictions[0])[-3:][::-1]
        
        print(f'\nPredictions for {filename}:')
        for idx in top_indices:
            confidence = predictions[0][idx] * 100
            class_name = class_indices.get(idx, "Unknown")
            print(f'{class_name}: {confidence:.2f}%')

# Path to the models directory
image_dir = os.path.join(os.getcwd(), 'models', 'test_model')

# List of images to predict
images = [
    os.path.join(image_dir, 'pizza_image.jpg'),
    os.path.join(image_dir, 'steak_image.jpg'),
    os.path.join(image_dir, 'sushi_image.jpg'),
    #os.path.join(image_dir, 'icecream_image.jpg')
]

# Call the prediction function
predict_food_names(images)