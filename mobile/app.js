import React, { useState, useEffect, useRef } from 'react';
import { View, Button, Image, Text, StyleSheet, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { Camera, CameraType } from 'expo-camera';  // Use expo-camera
import * as ImageManipulator from 'expo-image-manipulator';  // For image resizing and manipulation
import * as FileSystem from "expo-file-system";  // To handle file system operations
import axios from 'axios';

// Configure Axios Interceptors
axios.interceptors.request.use(
  (request) => {
    console.log('Axios Request:', JSON.stringify(request, null, 2));
    return request;
  },
  (error) => {
    console.error('Axios Request Error:', error);
    return Promise.reject(error);
  }
);

axios.interceptors.response.use(
  (response) => {
    console.log('Axios Response:', JSON.stringify(response.data, null, 2));
    return response;
  },
  (error) => {
    console.error('Axios Response Error:', error);
    return Promise.reject(error);
  }
);

const App = () => {
  const [hasPermission, setHasPermission] = useState(null);
  const [imageUri, setImageUri] = useState(null);
  const [nutritionInfo, setNutritionInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isCameraVisible, setIsCameraVisible] = useState(false);
  const cameraRef = useRef(null);

  const BASE_URL = 'http://192.168.1.5:5000';  // API URL

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
      console.log("Camera permission status:", status);
      if (status !== 'granted') {
        Alert.alert("Permission Required", "Camera access is needed.");
      }
    })();
  }, []);

  const captureImage = async () => {
    if (cameraRef.current) {
      try {
        const photo = await cameraRef.current.takePictureAsync();
        console.log("Captured photo:", photo);
        const resizedPhoto = await ImageManipulator.manipulateAsync(
          photo.uri,
          [{ resize: { width: 320, height: 320 } }],  // Further reduce resolution
          { compress: 0.5, format: ImageManipulator.SaveFormat.JPEG }  // Increase compression
        );        
        console.log("Resized photo URI:", resizedPhoto.uri); 
        setImageUri(resizedPhoto.uri);
        setNutritionInfo(null);  // Clear previous result
        await recognizeFood(resizedPhoto.uri);
        setIsCameraVisible(false);
      } catch (error) {
        console.error("Error capturing image: ", error);
        Alert.alert("Error", "An error occurred while capturing the image.");
      }
    } else {
      Alert.alert("Camera Error", "Camera is not available.");
    }
  };

  const recognizeFood = async (uri) => {
    setLoading(true);
    const apiUrl = `${BASE_URL}/api/capture`;

    try {
      const base64Image = await convertImageToBase64(uri);
      console.log("Sending image to API...");

      const response = await axios.post(apiUrl, { image: base64Image }, { timeout: 20000 });
      console.log("Received response:", response.data);

      if (response.data && response.data.food_name && response.data.nutrition_info) {
        const { food_name, nutrition_info } = response.data;
        console.log('Food Name:', food_name);
        console.log('Nutrition Info:', nutrition_info);
        setNutritionInfo({ food_name, nutrition_info }); // Update state correctly
      } else {
        console.log("No valid data received from API.");
        Alert.alert("Error", "Food not recognized or nutrition data unavailable. Please try again.");
        setNutritionInfo(null);
      }
    } catch (error) {
      setLoading(false);
      console.error("Error in recognizeFood:", error);
      Alert.alert("Error", "Failed to recognize food. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const convertImageToBase64 = async (uri) => {
    try {
      console.log("Starting image conversion to Base64...");
  
      // Resize the image and compress it to reduce its size
      const resizedImage = await ImageManipulator.manipulateAsync(
        uri,
        [{ resize: { width: 640, height: 640 } }],  // Resize to a smaller size
        { compress: 0.5, format: ImageManipulator.SaveFormat.JPEG }  // Compress image
      );
  
      // Convert the resized image to Base64
      const base64 = await FileSystem.readAsStringAsync(resizedImage.uri, { encoding: FileSystem.EncodingType.Base64 });
      console.log("Base64 conversion complete, length:", base64.length);
      return base64;
    } catch (error) {
      console.log("Error converting image to Base64", error);
      throw new Error("Failed to convert image to Base64");
    }
  };

  if (hasPermission === null) {
    return <View />;  // Waiting for permission
  }
  if (hasPermission === false) {
    return <Text>No access to camera</Text>;  // No camera access
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.header}>NutraScan</Text>

      {/* Camera section */}
      {isCameraVisible && hasPermission && (
        <Camera ref={cameraRef} style={styles.camera} type={CameraType.back}>
          <View style={styles.captureButtonContainer}>
            <Button title="Capture" onPress={captureImage} color="#28a745" />
          </View>
        </Camera>
      )}

      <Button
        title={isCameraVisible ? "Close Camera" : "Open Camera"}
        onPress={() => setIsCameraVisible(!isCameraVisible)}
        color="#007bff"
      />

      {/* Loading Spinner */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#0000ff" style={styles.loading} />
          <Text style={styles.loadingText}>Processing your image...</Text>
        </View>
      )}

      {/* Display captured image */}
      {imageUri && <Image source={{ uri: imageUri }} style={styles.image} />}

      {/* Display predicted food name and nutrition info */}
      {nutritionInfo && (
        <View style={styles.nutritionContainer}>
          <Text style={styles.nutritionTitle}>Predicted Food:</Text>
          <Text style={styles.foodName}>{nutritionInfo.food_name}</Text>

          <Text style={styles.nutritionTitle}>Nutritional Information:</Text>
          {nutritionInfo.nutrition_info && Object.entries(nutritionInfo.nutrition_info).map(([key, value]) => (
            <Text key={key} style={styles.nutritionText}>
              {key}: {value}
            </Text>
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f2f2f2',
  },
  camera: {
    width: 300,
    height: 300,
    marginBottom: 20,
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    color: '#333',
  },
  captureButtonContainer: {
    flex: 1,
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  image: {
    width: 300,
    height: 300,
    marginTop: 10,
    borderRadius: 15,
    borderWidth: 1,
    borderColor: '#ccc',
  },
  nutritionContainer: {
    marginTop: 20,
    padding: 15,
    backgroundColor: '#fff',
    borderRadius: 10,
    width: '100%',
    alignItems: 'flex-start',
  },
  nutritionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
    color: '#333',
  },
  foodName: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 15,
    color: '#28a745',
  },
  nutritionText: {
    fontSize: 14,
    marginBottom: 5,
    color: '#555',
  },
  loading: {
    marginTop: 20,
  },
  loadingContainer: {
    alignItems: 'center',
    marginTop: 20,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
  },
});

export default App;
