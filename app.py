import os
import io
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)
server = app 

CROP_THRESHOLDS = {
    "Corn": {"base": 50, "upper": 86},
    "Soybeans": {"base": 50, "upper": 86},
    "Wheat": {"base": 40, "upper": 77},
    "Cotton": {"base": 60, "upper": 100},
    "Barley": {"base": 32, "upper": 77},
    "Oats": {"base": 40, "upper": 77},
    "Sugarbeet": {"base": 37, "upper": 86},
    "Potatoes": {"base": 45, "upper": 86},
    "Dry Peas": {"base": 40, "upper": 77},
    "Chickpea": {"base": 45, "upper": 86},
    "Beans": {"base": 50, "upper": 86}
}

def fetch_weather(lat, lon, sowing_date):
    end_date = datetime.now().strftime('%Y-%m-%d')
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": sowing_date, "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit", "timezone": "auto"
    }
    res = requests.get(url, params=params)
    data = res.json()
    return pd.DataFrame(data["daily"])

def calculate_gdd(df, base, upper):
    t_max = df["temperature_2m_max"].clip(upper=upper)
    t_min = df["temperature_2m_min"].clip(lower=base)
    daily_gdd = ((t_max + t_min) / 2) - base
    return daily_gdd.clip(lower=0).cumsum()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate_gdd', methods=['POST'])
def get_gdd_data():
    req = request.json
    lat, lon, sowing_date = req['lat'], req['lon'], req['sowing_date']
    try:
        df = fetch_weather(lat, lon, sowing_date)
        df['time'] = pd.to_datetime(df['time'])
        results = {}
        plt.figure(figsize=(10, 5))
        for crop, limits in CROP_THRESHOLDS.items():
            gdd_series = calculate_gdd(df, limits['base'], limits['upper'])
            plt.plot(df['time'], gdd_series, label=crop, linewidth=1.5)
            results[crop] = int(gdd_series.iloc[-1])

        plt.title(f"Accumulated GDD since {sowing_date}")
        plt.ylabel("GDD (°F-day)")
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.grid(True, alpha=0.3)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        import base64
        plot_url = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        return jsonify({"plot": plot_url, "totals": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
