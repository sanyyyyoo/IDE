🧭 Overview
DataExtract Pro is a production-style full-stack system that automates the extraction, cleaning, and classification of unstructured web data using a fine-tuned DistilBERT NLP model.
It combines:
🔍 Web scraping automation
🧠 Transformer-based NLP classification
⚙️ End-to-end data processing pipeline
📊 Interactive analytics dashboard (React)
⚡ Scalable Flask backend API

The system is designed to transform raw, unstructured web data into structured, actionable insights with minimal manual intervention.

🎯 Problem Statement
Web data (especially from platforms like listings, directories, and reviews) is:
❌ Unstructured and noisy
❌ Difficult to analyze at scale
❌ Time-consuming to process manually
❌ Inconsistent across sources

💡 Solution
DataExtract Pro automates the entire pipeline:
Raw Web Data → Scraping → Cleaning → NLP Classification → Structured Output → Dashboard Insights

🏗️ System Architecture
                <img width="499" height="599" alt="image" src="https://github.com/user-attachments/assets/3ed28787-53a2-4125-a41e-28384ffa06cd" />


⚙️ Key Features
🤖 AI & Machine Learning

Fine-tuned DistilBERT transformer model
Named entity-style classification (name, address, category, etc.)
Training + evaluation pipeline using HuggingFace Transformers
🔄 Automation Engine
Fully automated ETL pipeline (Extract → Transform → Load)
Batch scraping for multiple cities/categories
Auto-triggered ML inference after scraping
One-click full pipeline execution

🌐 Full-Stack System
Flask REST API backend
React-based interactive dashboard
Real-time data updates
Export-ready structured datasets

📊 Data Intelligence


Cleaned and normalized structured datasets
Export to CSV / XLSX
Dashboard insights and visualization support

⚡ Automation Workflow
<img width="384" height="304" alt="image" src="https://github.com/user-attachments/assets/df1842b6-eac7-440e-beec-8dcd46dd7877" />


🧠 Machine Learning Pipeline
Model: DistilBERT (HuggingFace Transformers)
Task: Multi-class text classification / structured field extraction
Training Data: Custom scraped dataset
Preprocessing: Tokenization + normalization + labeling
Output: Structured entity prediction

📡 API Design
MethodEndpointDescriptionGET/Health checkPOST/scrapeTrigger scraping pipelinePOST/predictRun ML inferenceGET/resultsFetch processed dataset

🧱 Project Structure
<img width="329" height="660" alt="image" src="https://github.com/user-attachments/assets/3be6952e-af75-4d1f-9058-b15d29997227" />

🚀 Getting Started
1️⃣ Clone Repository
git clone https://github.com/your-username/dataextract-pro.gitcd dataextract-pro

2️⃣ Backend Setup (Flask)
pip install -r requirements.txtpython run_server.py

3️⃣ Frontend Setup (React)
cd frontendnpm installnpm run dev

👨‍💻 Tech Stack


Python 🐍


Flask ⚡


React ⚛️


HuggingFace Transformers 🤖


PyTorch 🔥


Pandas / NumPy 📊


Scikit-learn 📈







