# app.py
import streamlit as st
import requests
from datetime import datetime
import pytz
import jwt

API_BASE = "http://localhost:8000"
st.set_page_config(page_title="🌦️ Weather Forecast App", page_icon="🌤️", layout="centered")



st.title("🌦️ Weather Forecast App")

# ---------------- Session Setup ----------------
if "user" not in st.session_state:
    st.session_state["user"] = None
if (
    "token" in st.query_params
    and st.session_state.get("user") is None
    and not st.session_state.get("logout_flag")
):

    st.session_state["token"] = st.query_params["token"][0]
    if "email" in st.query_params:
        st.session_state["user"] = st.query_params["email"][0]
    else:
        st.session_state["user"] = "google_user"


if st.session_state.get("logout_flag"):
    st.session_state.pop("logout_flag")
    st.session_state.pop("user", None)
    st.session_state.pop("token", None)
    st.rerun()

# ---------------- Sidebar Login/Logout ----------------
with st.sidebar:
    if st.session_state["user"] is None:
        st.header("🔐 Login / Sign Up")
        auth_mode = st.selectbox("Choose Mode", ["Login", "Sign Up"])
        login_method = st.radio("Login with", ["Email", "Mobile"])

        input_value = st.text_input("Email" if login_method == "Email" else "Mobile")
        password = st.text_input("Password", type="password")

        if st.button(auth_mode):
            payload = {"username": input_value, "password": password}
            try:
                if auth_mode == "Login":
                    res = requests.post(f"{API_BASE}/token", data=payload)
                    if res.status_code == 200:
                        token = res.json()["access_token"]
                        st.session_state["token"] = token
                        st.session_state["user"] = input_value
                        st.sidebar.success("Login successful")
                        st.rerun()
                    else:
                        st.sidebar.error(res.json().get("detail", "Login failed"))
                else:
                    res = requests.post(f"{API_BASE}/signup", data={"email": input_value if login_method == "Email" else None, "mobile": input_value if login_method == "Mobile" else None, "password": password})
                    if res.status_code == 200:
                        st.sidebar.success("Signup successful. Please log in.")
                    else:
                        st.sidebar.error(res.json().get("detail", "Signup failed"))
            except Exception as e:
                st.sidebar.error(f"⚠️ Error: {str(e)}")

        st.markdown("---")
        st.markdown("[Login with Google](http://localhost:8000/auth/google)")

    else:
        st.success(f"✅ Logged in as: {st.session_state['user']}")
        if st.sidebar.button("🚪 Logout"):
            st.session_state["logout_flag"] = True
            st.rerun()
                # ✅ refresh the app to reset state


# ---------------- Main App ----------------
if st.session_state["user"]:
    st.subheader("🔍 Search Weather by City")
    col1, col2 = st.columns([4, 1])
    with col1:
        city = st.text_input("Enter City Name")
    with col2:
        search = st.button("Get Weather")

    if search and city:
        try:
            r = requests.get(f"{API_BASE}/weather", params={"city": city})
            if r.status_code == 200:
                data = r.json()
                time_zone = "Asia/Kolkata"
                now = datetime.now(pytz.timezone(time_zone)).strftime("%I:%M %p")

                st.markdown("---")
                st.markdown(f"### 🕒 {now}")
                st.markdown(f"#### 📍 {data['city']}, {data['country']}")

                col_left, col_right = st.columns([1, 3])
                with col_left:
                    st.image("https:" + data["icon"], width=100)
                with col_right:
                    st.markdown(f"""
                        <div style='padding: 10px; background-color: #f0f0f5; border-radius: 10px;'>
                            <b>🌡 Temperature:</b> {data['temp_c']}°C<br>
                            <b>💧 Humidity:</b> {data['humidity']}%<br>
                            <b>🌬 Wind Speed:</b> {data['wind_kph']} km/h<br>
                            <b>🧭 Pressure:</b> {data['pressure']} hPa<br>
                            <b>⛅ Description:</b> {data['condition']}
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown("---")
            else:
                st.error(r.json().get("detail", "City not found"))
        except:
            st.error("❌ Failed to fetch weather")
