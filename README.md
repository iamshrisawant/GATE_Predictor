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
- `legacy_and_tools/`: Archived legacy scripts and debugging tools.
- `run.py`: Entry point.
