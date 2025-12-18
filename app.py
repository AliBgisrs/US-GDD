import requests
from flask import Flask, render_template, jsonify, request
from datetime import datetime

app = Flask(__name__)
server = app # Critical for Gunicorn/Render

def calculate_fire_risk(temp, humidity, wind, soil_temp):
    # Simplified Fire Risk Index
    # Risk increases with Temp, Wind, and Soil Temp; decreases with Humidity
    risk = (temp * 0.3) + (wind * 0.3) + (soil_temp * 0.2) + (100 - humidity) * 0.2
    return min(100, max(0, risk))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_risk_data', methods=['POST'])
def get_risk_data():
    try:
        data = request.json
        lat, lon = data['lat'], data['lon']
        
        # Using Open-Meteo for real-time weather + soil data
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,soil_temperature_0cm",
            "timezone": "auto"
        }
        
        res = requests.get(url, params=params).json()
        curr = res['current']
        
        score = calculate_fire_risk(
            curr['temperature_2m'],
            curr['relative_humidity_2m'],
            curr['wind_speed_10m'],
            curr['soil_temperature_0cm']
        )
        
        return jsonify({
            "risk": round(score, 1),
            "temp": curr['temperature_2m'],
            "humidity": curr['relative_humidity_2m'],
            "wind": curr['wind_speed_10m'],
            "soil_temp": curr['soil_temperature_0cm']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)