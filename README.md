# DataVision AI 🚀

**Intelligent Data Analytics & Visualization Platform**

> AI & Data Science — Final Year Major Project

## 🔗 Live Demo
Deployed on Render: *(your-link-here after deployment)*

## ✨ Features
- 📁 Upload CSV / Excel datasets (up to 50 MB)
- 📊 8 interactive chart types (Bar, Line, Scatter, Histogram, Pie, Box, Violin, Heatmap)
- 🔍 Data quality analysis — missing values, duplicates, column stats
- 📐 Descriptive statistics — mean, std, skewness, kurtosis
- 🤖 K-Means Clustering with PCA visualisation & elbow curve
- 💡 Automated AI insights on distributions, correlations & outliers

## 🛠️ Tech Stack
| Layer | Technology |
|---|---|
| Backend | Python · Flask · Gunicorn |
| Data | Pandas · NumPy · SciPy |
| ML | Scikit-learn (KMeans, PCA, StandardScaler) |
| Charts | Plotly (interactive) |
| Frontend | HTML5 · CSS3 · Vanilla JS |
| Hosting | Render.com (free tier) |

## 🚀 Run Locally
```bash
pip install -r requirements.txt
python app.py
```
Open → http://localhost:5000

## 📦 Deploy to Render
1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` and deploys ✅
