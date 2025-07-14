# 🌦️ Weather Forecast App

A modern and secure Weather Forecast Web App built with **Streamlit** and **FastAPI**. Users can sign up or log in using **email**, **mobile**, or **Google OAuth**, and then search real-time weather forecasts for cities around the world.

---

## 🚀 Features

- 🔐 **User Authentication**
  - Login & Sign-up via Email or Mobile
  - Google OAuth login
  - JWT-based session handling

- 🌤️ **Weather Dashboard**
  - Real-time weather data via WeatherAPI
  - Search by city
  - Displays temperature, humidity, pressure, wind speed, and description

- 💾 **Session Persistence**
  - User state managed via `st.session_state`
  - Supports logout and rerun logic

---

## 🛠️ Tech Stack

| Layer       | Tools                     |
|-------------|----------------------------|
| Frontend    | Streamlit                 |
| Backend API | FastAPI (external)        |
| Auth        | JWT Tokens + Google OAuth |
| Weather API | [WeatherAPI.com](https://www.weatherapi.com) |
| Others      | Python, Requests, PyJWT, Pytz |

---

## 📦 Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/weather-app-streamlit.git
cd weather-app-streamlit
