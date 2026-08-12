# AgriGuideAI

## AI-Powered Crop Advisory and Farming Guidance Platform

### Problem Statement

Farmers often face difficulties in selecting the most suitable crop for their land because crop growth depends on various soil and weather conditions such as nitrogen, phosphorus, potassium, temperature, humidity, pH level, and rainfall.

Traditional crop selection methods may depend mainly on experience or general agricultural information and may not consider the specific conditions of a farmer's field.

Therefore, there is a need for an intelligent crop advisory system that can analyze soil and environmental conditions and provide suitable crop recommendations.

AgriGuideAI is developed as a crop advisory and farming guidance platform that helps farmers select suitable crops based on their soil and weather conditions. The system accepts important agricultural parameters and provides a crop recommendation through an easy-to-use web interface.

### Objectives

- To provide suitable crop recommendations based on soil and weather conditions.
- To help farmers make better crop selection decisions.
- To provide a simple and user-friendly agricultural platform.
- To provide farming guidance and advisory information.
- To develop an AI-based approach for agricultural decision support.

### Main Modules

1. Home Page
2. User Registration
3. User Login
4. Dashboard
5. Crop Recommendation
6. Farming Guidance

### Crop Recommendation Module

The farmer enters:

- Nitrogen (N)
- Phosphorus (P)
- Potassium (K)
- Temperature
- Humidity
- Soil pH
- Rainfall

The system processes these values and provides a suitable crop recommendation.

### Technologies Used

- Python
- Flask
- HTML
- CSS
- SQLite
- SQLAlchemy

### Project Structure

```text
AgriGuideAI/
│
├── app.py
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── success.html
│   ├── home.html
│   ├── dashboard.html
│   └── crop_recommendation.html
│
├── .gitignore
└── README.md