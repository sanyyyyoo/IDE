# DataExtract Pro - Project Summary

## 📋 Project Overview

**DataExtract Pro** is an AI-powered web application that automatically scrapes, classifies, and extracts structured business data from Google Maps. It combines web scraping, machine learning, and rule-based NLP to create a clean, structured dataset containing business names, addresses, phone numbers, and categories.

### Key Features
- **Automated Web Scraping**: Extracts business listings from Google Maps using Playwright
- **Hybrid AI Classification**: Uses DistilBERT, SpaCy, and Regex for accurate field classification
- **Real-time Progress Tracking**: Live activity logs and status updates
- **Data Visualization**: Interactive charts and analytics dashboard
- **Export Capabilities**: Download data as CSV or Excel files
- **Theme Support**: Light and dark mode with professional UI

---

## 🛠️ Technology Stack

### Backend Technologies

#### Core Framework
- **Flask 3.0+**: Python web framework for REST API
- **Flask-CORS**: Cross-Origin Resource Sharing support

#### Web Scraping
- **Playwright**: Browser automation for Google Maps scraping
- **asyncio**: Asynchronous programming for concurrent operations

#### Machine Learning & NLP
- **PyTorch 2.1+**: Deep learning framework
- **Transformers 4.44+**: Hugging Face library for DistilBERT model
- **SpaCy 3.7+**: Natural Language Processing for entity recognition
- **scikit-learn 1.5+**: Machine learning utilities

#### Data Processing
- **pandas 2.2+**: Data manipulation and analysis
- **numpy 1.26+**: Numerical computing
- **openpyxl 3.1+**: Excel file handling

#### Utilities
- **python-dotenv**: Environment variable management
- **joblib**: Model serialization
- **tqdm**: Progress bars

### Frontend Technologies

#### Core
- **HTML5**: Semantic markup
- **CSS3**: Styling with CSS variables for theming
- **Vanilla JavaScript (ES6+)**: No framework dependencies

#### Visualization
- **Chart.js 4.4.0**: Interactive charts (bar, pie)
- **Chart.js Plugin Datalabels**: Chart annotations

#### Styling
- **Custom CSS**: Professional dashboard theme
- **CSS Variables**: Dynamic theming (light/dark mode)
- **Responsive Design**: Mobile-first approach

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Frontend      │
│  (HTML/CSS/JS)  │
│                 │
│  - Scraper UI   │
│  - Data Explorer│
│  - Insights     │
└────────┬────────┘
         │ HTTP/REST
         │
┌────────▼────────┐
│   Flask API     │
│   (Backend)     │
│                 │
│  - /scrape      │
│  - /status      │
│  - /data        │
│  - /export      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────┐
│Scraper│ │   ML    │
│Engine │ │Pipeline │
└───┬───┘ └──┬──────┘
    │        │
┌───▼────────▼───┐
│  Google Maps   │
│  (Playwright)  │
└────────────────┘
```

### Component Breakdown

#### 1. Frontend Layer
- **Scraper Page**: City input, category selection, field selection, start/stop controls
- **Data Explorer**: Table view with search, filter, sort, export
- **Insights Dashboard**: Analytics with charts and metrics
- **Activity Log**: Real-time scraping progress and logs

#### 2. Backend API Layer
- **Flask Application**: RESTful API server
- **Job Management**: In-memory job status tracking
- **Logging Handler**: Custom logger for real-time log streaming
- **File Management**: Excel/CSV file handling

#### 3. Scraping Engine
- **Playwright Browser**: Automated Google Maps navigation
- **Data Extraction**: DOM parsing for business information
- **Deduplication**: JSON-based duplicate removal
- **Validation**: Text filtering and cleaning

#### 4. ML Classification Pipeline
- **Hybrid Classifier**: Ensemble of three classifiers
  - **DistilBERT**: Fine-tuned transformer model (40% weight)
  - **Regex Classifier**: Pattern-based rules (40% weight)
  - **SpaCy NER**: Named Entity Recognition (20% weight)
- **Data Processor**: Field classification and normalization
- **Confidence Scoring**: Weighted ensemble decisions

---

## 🔄 Workflow

### 1. User Initiates Scraping

```
User Input → Frontend → POST /scrape
  ├─ City name
  ├─ Selected categories (e.g., "Grocery store", "Chemist shop")
  └─ Fields to extract (name, address, phone, category)
```

### 2. Backend Processing

```
Flask API receives request
  ├─ Creates job ID
  ├─ Starts background thread
  └─ Returns job_id to frontend
```

### 3. Scraping Process (Background Thread)

```
For each category:
  ├─ Launch Playwright browser
  ├─ Navigate to Google Maps search
  ├─ Scroll and extract listings
  │   ├─ Extract name, address, phone
  │   ├─ Validate and filter data
  │   └─ Deduplicate entries
  └─ Collect all results
```

### 4. ML Classification

```
Raw scraped data → GoogleMapsDataProcessor
  ├─ For each entry:
  │   ├─ Extract text fields (name, address, phone)
  │   ├─ Run Hybrid Classifier
  │   │   ├─ DistilBERT prediction
  │   │   ├─ Regex pattern matching
  │   │   └─ SpaCy NER extraction
  │   ├─ Ensemble decision (weighted voting)
  │   ├─ Confidence scoring
  │   └─ Field assignment
  └─ Post-processing validation
```

### 5. Data Normalization

```
Classified data → Normalization
  ├─ Phone number formatting
  ├─ Address cleaning
  ├─ Name validation
  ├─ Category assignment (from search)
  └─ Duplicate removal (name + phone)
```

### 6. Export & Storage

```
Processed data → pandas DataFrame
  ├─ Filter entries with phone numbers
  ├─ Remove duplicates
  ├─ Save to Excel/CSV in /output folder
  └─ Update job status to "completed"
```

### 7. Frontend Updates

```
Frontend polls /status/<job_id> every 2 seconds
  ├─ Receives logs in real-time
  ├─ Updates activity log
  ├─ Shows progress
  └─ On completion:
      ├─ Loads data via /data endpoint
      ├─ Updates insights dashboard
      └─ Displays charts and metrics
```

---

## 📊 Data Flow

```
Google Maps
    ↓
Playwright Scraper
    ↓
Raw Data (unstructured)
    ↓
Hybrid Classifier
    ├─ DistilBERT (semantic understanding)
    ├─ Regex (pattern matching)
    └─ SpaCy (entity recognition)
    ↓
Classified Data (structured)
    ↓
Normalization & Validation
    ↓
Clean DataFrame
    ↓
Excel/CSV Export
    ↓
Frontend Visualization
```

---

## 🎯 Key Components

### Backend Components

#### `src/core/api/app.py`
- Flask application with REST endpoints
- Job management and status tracking
- Custom logging handler for real-time logs
- File serving and export functionality

#### `src/core/scraping/scrape_and_classify.py`
- Main scraping orchestration
- Playwright browser automation
- Data collection and deduplication
- Integration with ML pipeline

#### `src/core/ml/hybrid_classifier.py`
- HybridClassifier: Ensemble model
- GoogleMapsDataProcessor: Data processing pipeline
- Confidence-weighted decision making
- Field validation and swapping logic

#### `src/core/ml/distilbert_classifier.py`
- DistilBERT model loading and inference
- Batch processing for efficiency
- Probability distribution output

#### `src/core/ml/regex_classifier.py`
- Pattern-based classification
- Phone number validation
- Address pattern recognition
- Name pattern matching

#### `src/core/ml/spacy_classifier.py`
- Named Entity Recognition
- Entity type classification (PERSON, GPE, ORG)
- Business pattern detection

### Frontend Components

#### `frontend/index.html`
- Main HTML structure
- Navigation, hero section, footer
- Three main sections: Scraper, Data Explorer, Insights

#### `frontend/app.js`
- State management
- API communication
- Real-time polling
- Chart rendering (Chart.js)
- Theme toggle functionality

#### `frontend/styles.css`
- Professional dashboard theme
- Light/dark mode support
- Responsive design
- Card-based layout

---

## 🔌 API Endpoints

### POST `/scrape`
Start a new scraping job
- **Request Body**: `{ city, categories, fields }`
- **Response**: `{ job_id, message }`

### GET `/status/<job_id>`
Get job status and logs
- **Response**: `{ status, logs[], output_file, error }`
- **Status values**: `running`, `completed`, `failed`

### GET `/data`
Get most recent scraped data
- **Response**: `Array<{ name, address, phone, category }>`

### GET `/export/<filename>`
Download a file
- **Response**: File download (CSV or Excel)

### GET `/health`
Health check endpoint
- **Response**: `{ status: "ok" }`

---

## 📈 ML Model Details

### DistilBERT Fine-Tuned Model
- **Base Model**: DistilBERT (distilbert-base-uncased)
- **Task**: Multi-class classification (name, address, phone, category)
- **Training**: Fine-tuned on labeled business data
- **Location**: `models/distilbert_finetuned/`

### Hybrid Ensemble Approach
- **DistilBERT**: 40% weight (semantic understanding)
- **Regex**: 40% weight (pattern matching)
- **SpaCy**: 20% weight (entity recognition)
- **Decision Logic**: Weighted voting with confidence thresholds

### Classification Confidence
- **High Threshold**: 0.9 (very confident)
- **Medium Threshold**: 0.7 (moderately confident)
- **Low Confidence**: < 0.7 (needs review)

---

## 🎨 UI/UX Features

### Design System
- **Theme**: Professional analytics dashboard (Power BI inspired)
- **Color Modes**: Light (white base) and Dark (navy base with neon accents)
- **Typography**: Inter font family
- **Layout**: Card-based grid system
- **Responsive**: Mobile, tablet, desktop support

### Key UI Components
- **Navigation Bar**: Sticky top navigation
- **Hero Section**: Welcome message and branding
- **Config Panel**: City input, category/field selection
- **Status Panel**: Real-time job status
- **Activity Log**: Scrollable log viewer with timestamps
- **Data Table**: Sortable, filterable, searchable
- **Insights Dashboard**: Metrics cards and charts
- **Theme Toggle**: Light/dark mode switcher

---

## 📁 Project Structure

```
IDE/
├── frontend/              # Frontend application
│   ├── index.html        # Main HTML
│   ├── app.js            # JavaScript logic
│   └── styles.css        # Styling
├── src/
│   └── core/
│       ├── api/          # Flask backend
│       │   └── app.py
│       ├── scraping/     # Scraping engine
│       │   └── scrape_and_classify.py
│       └── ml/           # ML pipeline
│           ├── hybrid_classifier.py
│           ├── distilbert_classifier.py
│           ├── regex_classifier.py
│           ├── spacy_classifier.py
│           └── utils.py
├── models/               # ML models
│   └── distilbert_finetuned/
├── output/               # Scraped data output
├── notebooks/            # Jupyter notebooks
│   ├── 01_preprocessing.ipynb
│   ├── 02_training.ipynb
│   └── 03_evaluation.ipynb
├── requirements.txt      # Python dependencies
├── run_server.py         # Server startup script
└── README.md
```

---

## 🚀 Deployment & Usage

### Prerequisites
- Python 3.8+
- Node.js (optional, for development)
- Playwright browsers installed

### Setup
1. Install Python dependencies: `pip install -r requirements.txt`
2. Install Playwright browsers: `playwright install chromium`
3. Start backend: `python run_server.py`
4. Open frontend: `frontend/index.html` in browser or use HTTP server

### Running the Application
1. **Start Backend**: `python run_server.py` (runs on http://localhost:8000)
2. **Open Frontend**: Navigate to `frontend/index.html`
3. **Configure Scraping**: Select city, categories, and fields
4. **Start Scraping**: Click "Start Scraping" button
5. **Monitor Progress**: Watch activity log for real-time updates
6. **View Results**: Check Data Explorer and Insights tabs

---

## 🔒 Key Features & Capabilities

### Scraping Features
- ✅ Unlimited entries per category (no limit)
- ✅ Real-time progress tracking
- ✅ Automatic deduplication
- ✅ Data validation and cleaning
- ✅ Support for 26+ business categories

### ML Features
- ✅ Hybrid AI classification (3-model ensemble)
- ✅ Confidence scoring
- ✅ Field validation and correction
- ✅ Name/address swap detection
- ✅ Phone number normalization

### Frontend Features
- ✅ Real-time activity logs
- ✅ Interactive data visualization
- ✅ Export to CSV/Excel
- ✅ Search, filter, and sort
- ✅ Theme switching (light/dark)
- ✅ Responsive design

---

## 📊 Performance Considerations

- **Scraping**: Asynchronous operations for efficiency
- **ML Inference**: Batch processing for speed
- **Frontend**: Polling every 2 seconds for status updates
- **Data Export**: Pandas for efficient file handling
- **Memory**: In-memory job status (consider Redis for production)

---

## 🔮 Future Enhancements

- Database integration (PostgreSQL/MongoDB)
- User authentication and multi-user support
- Scheduled scraping jobs
- Advanced analytics and reporting
- API rate limiting and caching
- Docker containerization
- Cloud deployment (AWS, GCP, Azure)

---

## 📝 License & Credits

- **Project**: DataExtract Pro
- **ML Model**: Fine-tuned DistilBERT
- **Libraries**: Open source (see requirements.txt)
- **Design**: Inspired by Power BI and modern admin dashboards

---

*Last Updated: 2024*

