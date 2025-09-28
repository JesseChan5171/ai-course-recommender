# 🎓 AI Course Recommender

A smart course recommendation system powered by IBM Watsonx AI, featuring vector search, intelligent course matching, and personalized learning paths.

![Course Recommender](https://img.shields.io/badge/AI-Powered-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white) ![IBM Watsonx](https://img.shields.io/badge/IBM-Watsonx-052FAD)

## ✨ Features

- **🔍 Intelligent Search**: Vector-based semantic search using IBM Watsonx embeddings
- **🤖 AI-Powered Recommendations**: Context-aware course suggestions with scoring
- **🛤️ Learning Paths**: Structured progression from beginner to advanced
- **💬 AI Chat Advisor**: Interactive guidance and course Q&A
- **📊 Analytics**: Course insights, skill gap analysis, and progress tracking
- **🎨 Modern UI**: Responsive design with animated elements

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- IBM Watsonx account with API access
- SQLite database (built into Python - no installation needed)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd course-recommender
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment Setup**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Database Setup** (Required before running app)
```bash
python scripts/setup_db.py
```

5. **Run the application**
```bash
streamlit run app.py
```

## ⚙️ Configuration

### Required Environment Variables

Create a `.env` file with your credentials:

```bash
# IBM Watsonx AI API
WATSONX_API_KEY=your_watsonx_api_key_here
WATSONX_PROJECT_ID=your_project_id_here

# Database (SQLite - automatically managed)
# No additional database configuration needed
# Database file: data/course_catalog.db
```

### Getting IBM Watsonx Credentials

1. Sign up for [IBM Cloud](https://cloud.ibm.com/)
2. Create a Watsonx project
3. Get your API key from the IBM Cloud console
4. Copy your project ID from Watsonx

## 📁 Project Structure

```
course-recommender/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── README.md             # This file
├── src/                  # Core backend modules
│   ├── vector_search.py  # Semantic search engine
│   ├── database_utils.py # Database operations
│   ├── course_analytics.py # AI analytics & LLM
│   └── course_details.py # Course information
├── ui/                   # User interface components
│   ├── components/       # Reusable UI components
│   └── assets/          # CSS styles
├── data/                # Sample data
└── scripts/             # Setup utilities
```

## 🔧 Usage

### Basic Search
1. Enter your learning query (e.g., "Python for data science")
2. Apply filters for skill level, duration, and price
3. View recommended courses with match scores

### AI Chat Advisor
1. Click "💬 Chat with AI Learning Advisor"
2. Ask questions about courses, career paths, or learning strategies
3. Get personalized recommendations and guidance

### Learning Paths
1. Perform a search to discover courses
2. View the "🛤️ Suggested Learning Path" section
3. See structured progression and timeline
4. Track your progress through courses

## 🎯 Core Components

### Vector Search Engine (`src/vector_search.py`)
- Semantic course matching using IBM Watsonx embeddings
- SQLite database with efficient similarity calculations
- Configurable similarity thresholds

### AI Analytics (`src/course_analytics.py`)
- IBM Watsonx LLM integration
- Learning path generation
- Skill gap analysis
- Course recommendation scoring

### Database Layer (`src/database_utils.py`)
- SQLite database with optimized schema
- Embedding storage and retrieval
- Course catalog management
- Automatic database initialization

## 🚀 Development

### Adding New Features

1. **Backend Logic**: Add to `src/` modules
2. **UI Components**: Create in `ui/components/`
3. **Styling**: Update `ui/assets/styles.css`

### Database Setup

The database setup is required during initial installation (step 4 above). This command:
- Creates the SQLite database structure
- Loads sample course data for testing
- Generates embeddings (requires valid API credentials)

```bash
python scripts/setup_db.py
```

**Note**: This step is required before running the application for the first time.

## 🔒 Security

- All API keys and sensitive data use environment variables
- `.env` file is git-ignored by default
- SQLite database stored locally with secure file permissions

## 📊 Sample Data

The system includes sample course data for testing. In production, connect to your course catalog database or import real course data.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues or questions:
1. Check the [Issues](../../issues) page
2. Review the documentation
3. Contact the development team

---

**Built with ❤️ using IBM Watsonx AI and Streamlit**