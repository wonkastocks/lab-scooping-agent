# Lab Survey Application

A Streamlit-based web application for collecting and managing lab setup requirements.

## Features

- Multi-step form for collecting lab requirements
- Summary page with edit functionality
- MongoDB integration for data storage
- Responsive design for all devices

## Prerequisites

- Python 3.8+
- MongoDB Atlas account or local MongoDB instance
- Streamlit

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd lab-scooping-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the MongoDB connection string in `.env`

## Running Locally

1. Start the Streamlit app:
   ```bash
   streamlit run lab_survey_app.py
   ```

2. Open your browser and navigate to `http://localhost:8501`

## Deployment

### Streamlit Cloud

1. Push your code to a GitHub repository
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Click "New app" and connect your repository
4. Set the main file path to `lab_survey_app.py`
5. Add your MongoDB connection string as a secret in the Advanced settings:
   - Key: `mongo.uri`
   - Value: Your MongoDB connection string
6. Click "Deploy"

## Project Structure

```
.
├── .gitignore
├── .gitattributes
├── README.md
├── requirements.txt
├── lab_survey_app.py     # Main application file
├── .env.example          # Example environment variables
└── src/                  # Source code directory
    └── main.py           # Main module
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
MONGODB_URI=your_mongodb_connection_string
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Running Tests
- Run tests with pytest:
  pytest tests/
