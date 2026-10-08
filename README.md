# 🎵 Mini Spotify — Music Recommendation & User Behaviour Analysis

Mini Spotify is a full-stack music streaming and recommendation application developed as a **Data Warehousing and Data Mining (DWM) project**. The system combines a Spotify-like music platform with a data warehouse and data mining techniques to analyze user listening behaviour and generate meaningful insights.

## 🚀 Features

### 👤 User Features

* User registration and login
* JWT-based authentication
* User profile management
* Search for songs, artists and genres
* Play songs through YouTube
* Like and unlike songs
* Create and manage playlists
* View listening history
* Personalized recommendations

### 📊 Data Warehousing

The project uses a **Star Schema** for organizing analytical data.

The warehouse contains:

* **Fact Table**

  * `fact_listening`

* **Dimension Tables**

  * `dim_user`
  * `dim_song`
  * `dim_artist`
  * `dim_genre`
  * `dim_date`

The ETL process extracts data from the application/database, transforms it into an analytical format, and loads it into the data warehouse.

### 🤖 Data Mining

Two major data mining techniques are implemented:

#### K-Means Clustering

K-Means is used to group users according to their listening behaviour and activity patterns.

Current analysis:

* **199 users**
* **4 clusters**
* Silhouette Score: **0.1893**
* Davies-Bouldin Index: **2.2760**
* Calinski-Harabasz Score: **30.7586**

#### Apriori Association Rule Mining

Apriori is used to identify relationships between songs that users frequently listen to together.

Current analysis:

* **100 songs selected**
* **114 transactions**
* **1,737 frequent itemsets**
* **2,606 association rules**
* Minimum support: **0.01**
* Minimum confidence: **0.20**

## 🛠️ Technology Stack

### Frontend

* React.js
* HTML
* CSS
* JavaScript

### Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* JWT Authentication

### Database

* PostgreSQL

### Data Mining & Analytics

* Python
* Pandas
* NumPy
* Scikit-learn
* MLxtend
* K-Means Clustering
* Apriori Algorithm

### Music & External Services

* YouTube playback
* SMTP email notifications

## 🏗️ System Architecture

```text
                   ┌─────────────────────┐
                   │   React Frontend    │
                   │                     │
                   │ Search • Player     │
                   │ Playlist • Profile  │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │    FastAPI Backend  │
                   │                     │
                   │ Auth • Songs • User  │
                   │ Playlist • History  │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │     PostgreSQL      │
                   │   Application DB    │
                   └──────────┬──────────┘
                              │
                         ETL Process
                              │
                              ▼
                   ┌─────────────────────┐
                   │   Data Warehouse    │
                   │                     │
                   │ Fact + Dimensions   │
                   └──────────┬──────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
             ┌──────────────┐    ┌──────────────┐
             │ K-Means      │    │   Apriori    │
             │ Clustering   │    │ Association  │
             └──────────────┘    └──────────────┘
```

## 📚 Dataset

The music catalogue is based on the **Free Music Archive (FMA)** dataset.

The project uses approximately:

* **106,573 songs**
* **16,341 artists**

A synthetic listening-activity dataset is generated for analytical processing to simulate user interactions such as song plays and listening behaviour.

## 📈 Current Dataset Statistics

| Metric                 |       Value |
| ---------------------- | ----------: |
| Total Users            |         205 |
| Active Warehouse Users |         199 |
| Total Songs            |     106,573 |
| Songs Currently Played |       8,026 |
| Total Plays            |      11,838 |
| Listening Time         | 540.7 hours |
| Total Likes            |       3,246 |
| Artists                |      16,341 |

## 🔄 Data Processing Workflow

```text
Music Catalogue
      ↓
Application Database
      ↓
User Listening Activity
      ↓
ETL
      ↓
Data Warehouse
      ↓
OLAP Analysis
      ↓
Data Mining
      ↓
K-Means + Apriori
      ↓
Insights & Recommendations
```

## 📁 Project Structure

```text
mini_spotify/
│
├── frontend/
│   └── React application
│
├── backend/
│   ├── main.py
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   └── database/
│
├── dwm/
│   ├── warehouse/
│   ├── etl/
│   ├── mining/
│   │   ├── kmeans/
│   │   └── apriori/
│   └── synthetic_activity.csv
│
├── requirements.txt
└── README.md
```

> Folder names may vary depending on the final project structure.

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd mini_spotify
```

### 2. Backend Setup

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file and add the required configuration:

```env
DATABASE_URL=your_postgresql_database_url
SECRET_KEY=your_secret_key
```

Add any additional API or SMTP credentials required by the application.

### 4. Run the Backend

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

### 5. Run the Frontend

Navigate to the frontend directory:

```bash
cd frontend
npm install
npm run dev
```

The frontend will normally run at:

```text
http://localhost:5173
```

## 🔐 Authentication

The application uses **JWT-based authentication**.

The authentication flow is:

```text
Register
   ↓
Login
   ↓
JWT Token
   ↓
Authenticated Requests
   ↓
Protected Features
```

Protected features include playlists, likes, listening history and user-specific recommendations.

## 📊 Data Warehouse Design

The warehouse follows a **star schema**.

```text
                  dim_user
                     │
                     │
dim_song ───── fact_listening ───── dim_date
                     │
                     │
                dim_artist
                     │
                     │
                 dim_genre
```

The fact table stores listening events, while dimension tables provide descriptive information about users, songs, artists, genres and dates.

## 🧠 Recommendation Approach

The recommendation component uses user behaviour as the basis for discovering potentially relevant songs.

The system analyzes:

* Listening history
* Song interactions
* Likes
* Frequently associated songs
* User activity patterns
* User clusters

The mining results can then be used to support personalized recommendations.

## 📌 Purpose of the Project

The main objective of Mini Spotify is to demonstrate how a music streaming application can be combined with **Data Warehousing and Data Mining** techniques.

The project demonstrates:

1. Full-stack application development
2. Database management
3. Data warehouse design
4. ETL processing
5. OLAP analysis
6. User behaviour analysis
7. K-Means clustering
8. Apriori association-rule mining
9. Recommendation-system concepts

## 👩‍💻 Team Project

**Project:** Mini Spotify — Music Recommendation & User Behaviour Analysis

**Course:** Data Warehousing and Data Mining (DWM)

Developed as an academic project demonstrating the integration of full-stack development, data warehousing and data mining.

## 📄 License

This project is developed for academic and educational purposes.
