"""
DataVision AI — Intelligent Data Analytics and Visualization Platform
AI & Data Science Major Project
"""

import os, io, json, uuid, warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

warnings.filterwarnings("ignore")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "datavision-ai-2024-secret")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def load_dataframe(filepath):
    ext = filepath.rsplit(".", 1)[1].lower()
    if ext == "csv":
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                return pd.read_csv(filepath, encoding=enc)
            except UnicodeDecodeError:
                continue
    return pd.read_excel(filepath)

def df_to_session(df):
    session["df"] = df.to_json(orient="split", date_format="iso")

def df_from_session():
    raw = session.get("df")
    if raw is None:
        return None
    return pd.read_json(io.StringIO(raw), orient="split")

def num_cols(df):
    return df.select_dtypes(include=[np.number]).columns.tolist()

def cat_cols(df):
    return df.select_dtypes(include=["object", "category"]).columns.tolist()

def fig_json(fig):
    return json.dumps(fig, cls=PlotlyJSONEncoder)

TEMPLATE = "plotly_dark"
COLORS   = px.colors.qualitative.Vivid


# ── Insights Engine ───────────────────────────────────────────────────────────

def generate_insights(df):
    insights = []
    num = num_cols(df)
    cat = cat_cols(df)

    insights.append({"icon":"📊","cat":"Overview","title":"Dataset Overview",
        "text":f"Your dataset has <strong>{df.shape[0]:,} rows</strong> and "
               f"<strong>{df.shape[1]} columns</strong> ({len(num)} numeric, {len(cat)} categorical)."})

    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(1)
    hi = missing_pct[missing_pct > 20]
    if not hi.empty:
        cols_str = ", ".join([f"<em>{c}</em> ({missing_pct[c]}%)" for c in hi.index[:5]])
        insights.append({"icon":"⚠️","cat":"Data Quality","title":"High Missing Values",
            "text":f"Columns with >20% missing: {cols_str}. Consider imputation or removal."})
    else:
        total = int(missing.sum())
        insights.append({"icon":"✅","cat":"Data Quality","title":"Good Data Completeness",
            "text":f"Total missing cells: <strong>{total:,}</strong> ({total/df.size*100:.1f}%). Data quality looks healthy."})

    dupes = int(df.duplicated().sum())
    if dupes:
        insights.append({"icon":"🔁","cat":"Data Quality","title":"Duplicate Records",
            "text":f"<strong>{dupes:,} duplicate rows</strong> detected ({dupes/len(df)*100:.1f}%). Remove before analysis."})

    for col in num[:4]:
        s = df[col].dropna()
        if len(s) < 5: continue
        skew = s.skew()
        direction = "right-skewed" if skew>0.5 else "left-skewed" if skew<-0.5 else "approximately symmetric"
        Q1,Q3 = s.quantile(.25), s.quantile(.75)
        outs = int(((s < Q1-1.5*(Q3-Q1))|(s > Q3+1.5*(Q3-Q1))).sum())
        insights.append({"icon":"📈","cat":"Statistics","title":f"Distribution: {col}",
            "text":f"Mean=<strong>{s.mean():.2f}</strong>, Median=<strong>{s.median():.2f}</strong>, "
                   f"Std=<strong>{s.std():.2f}</strong>. Distribution is <strong>{direction}</strong> "
                   f"(skew={skew:.2f}). Outliers (IQR): <strong>{outs}</strong>."})

    if len(num) >= 2:
        corr = df[num].corr().abs()
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        stack = upper.stack()
        if not stack.empty:
            pair = stack.idxmax()
            val  = stack.max()
            strength = "strong" if val>.7 else "moderate" if val>.4 else "weak"
            insights.append({"icon":"🔗","cat":"Correlation","title":"Strongest Correlation",
                "text":f"<em>{pair[0]}</em> & <em>{pair[1]}</em> show a "
                       f"<strong>{strength} correlation</strong> (r={val:.2f})."})

    for col in cat[:3]:
        vc  = df[col].value_counts()
        top = vc.index[0]
        pct = vc.iloc[0]/len(df)*100
        insights.append({"icon":"🏷️","cat":"Categorical","title":f"Top Category: {col}",
            "text":f"Most frequent: <strong>'{top}'</strong> ({pct:.1f}%). "
                   f"Total unique values: <strong>{df[col].nunique()}</strong>."})

    return insights


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("No file part.", "danger"); return redirect(url_for("index"))
    f = request.files["file"]
    if f.filename == "":
        flash("No file selected.", "danger"); return redirect(url_for("index"))
    if not allowed_file(f.filename):
        flash("Only CSV and Excel files are supported.", "danger"); return redirect(url_for("index"))

    fname = secure_filename(f.filename)
    uname = f"{uuid.uuid4().hex}_{fname}"
    fpath = os.path.join(app.config["UPLOAD_FOLDER"], uname)
    f.save(fpath)

    try:
        df = load_dataframe(fpath)
    except Exception as e:
        flash(f"Could not read file: {e}", "danger")
        os.remove(fpath); return redirect(url_for("index"))

    if len(df) > 100_000:
        df = df.sample(100_000, random_state=42).reset_index(drop=True)
        flash("Dataset sampled to 100,000 rows for performance.", "warning")

    df_to_session(df)
    session["filename"] = fname
    session["filepath"] = fpath
    return redirect(url_for("dashboard"))

@app.route("/demo")
def demo():
    np.random.seed(42)
    n = 600
    regions    = ["North","South","East","West"]
    categories = ["Electronics","Clothing","Groceries","Sports","Books"]
    df = pd.DataFrame({
        "Region":      np.random.choice(regions, n),
        "Category":    np.random.choice(categories, n),
        "Month":       np.random.randint(1, 13, n),
        "Units_Sold":  np.random.randint(10, 500, n),
        "Unit_Price":  np.round(np.random.uniform(5, 500, n), 2),
        "Discount_Pct":np.round(np.random.uniform(0, 30, n), 1),
        "Customer_Age":np.random.randint(18, 70, n),
        "Rating":      np.round(np.random.uniform(1, 5, n), 1),
        "Return_Flag": np.random.choice([0,1], n, p=[0.85,0.15]),
    })
    df["Revenue"] = np.round(df["Units_Sold"]*df["Unit_Price"]*(1-df["Discount_Pct"]/100), 2)
    for col in ["Discount_Pct","Rating"]:
        idx = np.random.choice(df.index, size=18, replace=False)
        df.loc[idx, col] = np.nan

    df_to_session(df)
    session["filename"] = "demo_sales_dataset.csv"
    session["filepath"] = ""
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    df = df_from_session()
    if df is None:
        flash("Please upload a dataset first.", "warning")
        return redirect(url_for("index"))

    num = num_cols(df)
    cat = cat_cols(df)
    stats = {
        "rows": f"{df.shape[0]:,}", "cols": df.shape[1],
        "numeric": len(num), "categorical": len(cat),
        "missing": int(df.isnull().sum().sum()),
        "duplicates": int(df.duplicated().sum()),
        "memory": f"{df.memory_usage(deep=True).sum()/1024:.1f} KB",
    }
    return render_template("dashboard.html",
        filename=session.get("filename","dataset"),
        stats=stats,
        columns=df.columns.tolist(),
        numeric_cols=num,
        categorical_cols=cat,
        preview=df.head(10).to_html(
            classes="table table-sm table-striped table-hover align-middle",
            index=False, border=0),
    )

# ── API: column info ──────────────────────────────────────────────────────────

@app.route("/api/columns")
def api_columns():
    df = df_from_session()
    if df is None: return jsonify({"error":"No dataset"}), 400
    return jsonify({"all": df.columns.tolist(),
                    "numeric": num_cols(df),
                    "categorical": cat_cols(df)})

# ── API: data quality ─────────────────────────────────────────────────────────

@app.route("/api/quality")
def api_quality():
    df = df_from_session()
    if df is None: return jsonify({"error":"No dataset"}), 400
    missing = df.isnull().sum()
    qdf = pd.DataFrame({
        "Column":        df.columns,
        "Data Type":     df.dtypes.astype(str).values,
        "Non-Null Count":(len(df)-missing).values,
        "Missing Count": missing.values,
        "Missing %":     (missing/len(df)*100).round(2).values,
        "Unique Values": df.nunique().values,
    })
    return jsonify({"table": qdf.to_html(
        classes="table table-sm table-hover align-middle", index=False, border=0),
        "duplicates": int(df.duplicated().sum())})

# ── API: descriptive stats ────────────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    df = df_from_session()
    if df is None: return jsonify({"error":"No dataset"}), 400
    num = num_cols(df)
    if not num: return jsonify({"error":"No numeric columns"}), 400
    desc = df[num].describe().T.round(3)
    desc["skewness"] = df[num].skew().round(3)
    desc["kurtosis"] = df[num].kurtosis().round(3)
    desc.index.name = "Column"
    return jsonify({"table": desc.reset_index().to_html(
        classes="table table-sm table-hover align-middle", index=False, border=0)})

# ── API: chart ────────────────────────────────────────────────────────────────

@app.route("/api/chart", methods=["POST"])
def api_chart():
    df = df_from_session()
    if df is None: return jsonify({"error":"No dataset"}), 400
    d = request.get_json()
    ctype = d.get("type","bar")
    x  = d.get("x"); y = d.get("y")
    col= d.get("color"); agg = d.get("agg","mean")
    fig = None
    try:
        if ctype == "bar" and x and y:
            grp = df.groupby(x)[y]
            ops = {"mean":grp.mean,"sum":grp.sum,"count":grp.count,"max":grp.max,"min":grp.min}
            adf = ops.get(agg, grp.mean)().reset_index()
            adf.columns = [x, y]
            fig = px.bar(adf, x=x, y=y, color=x, template=TEMPLATE,
                color_discrete_sequence=COLORS,
                title=f"{agg.capitalize()} of {y} by {x}", text_auto=".2s")
            fig.update_traces(textposition="outside")

        elif ctype == "line" and x and y:
            cols = [x, y] + ([col] if col and col in df.columns else [])
            pdf  = df[cols].dropna().sort_values(x)
            fig  = px.line(pdf, x=x, y=y, template=TEMPLATE, markers=True,
                color=col if col and col in df.columns else None,
                color_discrete_sequence=COLORS, title=f"{y} over {x}")

        elif ctype == "scatter" and x and y:
            fig = px.scatter(df, x=x, y=y, template=TEMPLATE, trendline="ols",
                color=col if col and col in df.columns else None,
                color_discrete_sequence=COLORS, opacity=0.7, title=f"{y} vs {x}")

        elif ctype == "histogram" and x:
            fig = px.histogram(df, x=x, nbins=d.get("bins",30), template=TEMPLATE,
                color_discrete_sequence=["#6366f1"], marginal="box",
                title=f"Distribution of {x}")

        elif ctype == "pie" and x:
            vc = df[x].value_counts().head(12).reset_index()
            vc.columns = [x,"count"]
            fig = px.pie(vc, names=x, values="count", template=TEMPLATE,
                color_discrete_sequence=COLORS, hole=0.35, title=f"Distribution of {x}")

        elif ctype == "box" and x and y:
            fig = px.box(df, x=x, y=y, color=x, template=TEMPLATE,
                color_discrete_sequence=COLORS, points="outliers", title=f"{y} by {x}")

        elif ctype == "violin" and x and y:
            fig = px.violin(df, x=x, y=y, color=x, template=TEMPLATE,
                color_discrete_sequence=COLORS, box=True, points="outliers",
                title=f"{y} by {x}")

        elif ctype == "heatmap":
            nc = num_cols(df)
            if len(nc)<2: return jsonify({"error":"Need ≥2 numeric columns"}), 400
            corr = df[nc].corr().round(2)
            fig  = go.Figure(go.Heatmap(z=corr.values, x=corr.columns.tolist(),
                y=corr.index.tolist(), colorscale="RdBu", zmid=0,
                text=corr.values, texttemplate="%{text:.2f}", showscale=True))
            fig.update_layout(template=TEMPLATE, title="Correlation Heatmap",
                height=max(400, len(nc)*55))

        elif ctype == "bubble" and x and y:
            sz = d.get("size")
            kw = {}
            if sz and sz in num_cols(df): kw["size"] = sz
            if col and col in df.columns:  kw["color"] = col
            fig = px.scatter(df.dropna(subset=[x,y]), x=x, y=y, template=TEMPLATE,
                color_discrete_sequence=COLORS, opacity=0.7, title=f"Bubble: {y} vs {x}", **kw)

        if fig is None:
            return jsonify({"error":"Could not generate chart — check column selections."}), 400

        fig.update_layout(margin=dict(l=40,r=40,t=60,b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        return jsonify({"chart": fig_json(fig)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── API: clustering ───────────────────────────────────────────────────────────

@app.route("/api/cluster", methods=["POST"])
def api_cluster():
    df = df_from_session()
    if df is None: return jsonify({"error":"No dataset"}), 400
    d   = request.get_json()
    nc  = num_cols(df)
    sel = [c for c in d.get("columns", nc[:5]) if c in nc]
    k   = int(d.get("k", 3))
    if len(sel)<2: return jsonify({"error":"Select ≥2 numeric columns"}), 400

    sub = df[sel].dropna()
    if len(sub)<k: return jsonify({"error":"Not enough rows after dropping NaN"}), 400

    scaler = StandardScaler()
    X = scaler.fit_transform(sub)

    max_k = min(10, len(sub))
    inertias, sils = [], []
    for ki in range(2, max_k+1):
        km = KMeans(n_clusters=ki, random_state=42, n_init=10)
        lb = km.fit_predict(X)
        inertias.append(km.inertia_)
        try: sils.append(silhouette_score(X, lb))
        except: sils.append(0)

    km_f = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km_f.fit_predict(X)
    sil    = silhouette_score(X, labels)

    pca   = PCA(n_components=2)
    X2d   = pca.fit_transform(X)
    pdf   = pd.DataFrame({"PC1":X2d[:,0],"PC2":X2d[:,1],
                          "Cluster":[f"Cluster {l+1}" for l in labels]})

    fig_s = px.scatter(pdf, x="PC1", y="PC2", color="Cluster",
        template=TEMPLATE, title=f"K-Means (k={k}) — PCA 2D Projection",
        color_discrete_sequence=px.colors.qualitative.Bold, opacity=0.8)
    fig_s.update_layout(margin=dict(l=40,r=40,t=60,b=40))

    fig_e = go.Figure()
    ks = list(range(2, max_k+1))
    fig_e.add_trace(go.Scatter(x=ks, y=inertias, mode="lines+markers",
        name="Inertia", line=dict(color="#6366f1", width=2), marker=dict(size=8)))
    fig_e.add_trace(go.Scatter(x=ks, y=sils, mode="lines+markers",
        name="Silhouette Score", line=dict(color="#f59e0b", width=2, dash="dot"),
        marker=dict(size=8), yaxis="y2"))
    fig_e.update_layout(template=TEMPLATE, title="Elbow Curve & Silhouette Scores",
        xaxis_title="k", yaxis_title="Inertia",
        yaxis2=dict(title="Silhouette", overlaying="y", side="right"),
        margin=dict(l=40,r=60,t=60,b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02))

    sub2 = sub.copy(); sub2["Cluster"] = [f"Cluster {l+1}" for l in labels]
    summary = sub2.groupby("Cluster").agg(["mean","count"]).round(2)
    summary.columns = [" ".join(c) for c in summary.columns]

    return jsonify({
        "scatter": fig_json(fig_s), "elbow": fig_json(fig_e),
        "silhouette": round(float(sil),4),
        "variance_explained": [round(float(v)*100,1) for v in pca.explained_variance_ratio_],
        "cluster_summary": summary.to_html(
            classes="table table-sm table-hover align-middle", border=0),
        "k": k,
    })

# ── API: insights ─────────────────────────────────────────────────────────────

@app.route("/api/insights")
def api_insights():
    df = df_from_session()
    if df is None: return jsonify({"error":"No dataset"}), 400
    return jsonify({"insights": generate_insights(df)})

# ── Reset ─────────────────────────────────────────────────────────────────────

@app.route("/reset")
def reset():
    fp = session.get("filepath","")
    if fp and os.path.exists(fp):
        try: os.remove(fp)
        except: pass
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
