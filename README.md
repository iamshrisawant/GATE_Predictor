# GATE Score Predictor

A Flask-based application to predict GATE scores by analyzing response sheets and comparing them against the official answer keys.

## Features
- **Response Sheet Analysis:** Parses HTML response sheets to extract user answers.
- **Score Calculation:** Automatically calculates marks based on GATE schema (MCQ, MSQ, NAT) with negative marking.
- **Admin Dashboard:** Upload answer keys and manage live papers.
- **Community Contribution:** Users can contribute answer keys for verification.

## Setup

1.  **Clone the repository**
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Environment Variables:**
    Create a `.env` file in the root directory:
    ```
    SECRET_KEY=your_secret_key
    SMTP_EMAIL=your_email@gmail.com
    SMTP_PASSWORD=your_app_password
    ADMIN_PIN=GATE2025
    BASE_URL=http://localhost:5000
    ```
4.  **Run the Application:**
    ```bash
    python run.py
    ```
5.  **Access:**
    - App: `http://localhost:5000`
    - Dashboard: `http://localhost:5000/dashboard`

## Project Structure
- `app/`: Contains the application source code.
    - `services/`: Business logic (scoring, extraction, email).
    - `routes.py`: API endpoints.
- `data/`: Stores uploaded answer keys and staging data.
- `run.py`: Entry point.

## Preventing Free-Tier Cold Starts
If you are deploying this application on a free-tier hosting service (like Render) that spins down containers after a period of inactivity, you can use the built-in keep-alive mechanism to prevent lag:

1. **Using Internal Keep-Alive:** Set the `SELF_URL` environment variable to your application's public URL (e.g., `SELF_URL=https://your-app-name.onrender.com`). A background daemon will automatically ping your app every 10 minutes to keep it awake.
2. **Using UptimeRobot (Alternative):** Alternatively, set up a free monitor on [UptimeRobot](https://uptimerobot.com) to ping `https://your-app-name.onrender.com/api/ping` every 5-10 minutes.
