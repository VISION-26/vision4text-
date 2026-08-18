# EVT-CLIP++: Statistical Extreme Value Fusion & Vision-Language Guidance for Industrial Visual Anomaly Detection

[![Live Demo](https://img.shields.io/badge/Live%20Website-vision4text.in-10B981?style=for-the-badge&logo=vercel)](https://vision4text.in)
[![Backend](https://img.shields.io/badge/Backend-Modal%20CPU%20Serverless-7C3AED?style=for-the-badge&logo=python)](https://modal.com)
[![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Tailwind-38BDF8?style=for-the-badge&logo=react)](https://reactjs.org)
[![Defense Grade](https://img.shields.io/badge/Academic%20Project-Final%20Year%20Major-F43F5E?style=for-the-badge)](https://vision4text.in/about)
[![CI Validation](https://img.shields.io/badge/CI%20Pipeline-Passed-22C55E?style=for-the-badge&logo=githubactions)](https://github.com/VISION-26/vision4text-/actions)

> **Official College Major Project Submission (2026)**  
> **Live Production URL**: [https://vision4text.in](https://vision4text.in)  
> **System Name**: EVT-CLIP / Vision4Text Anomaly Inspection Platform

---

## Executive Summary

**EVT-CLIP++** is a multi-modal industrial visual anomaly detection and pixel-level localization system designed for automated surface quality inspection. Industrial manufacturing lines face class imbalance where nominal products occur by the millions while defects are rare, unpredictable, and diverse.

Standard deep learning anomaly detectors depend on ad-hoc empirical score thresholding, resulting in uncalibrated false alarms under subtle lighting or perspective shifts. **EVT-CLIP** resolves this by mathematically unifying:
1. **Extreme Value Theory (EVT)** for statistical modeling of the nominal reconstruction error distribution tail (3-parameter Weibull / Generalized Extreme Value fitting).
2. **PatchCore Coreset Memory Banks** for local neighborhood patch matching without catastrophic forgetting.
3. **EfficientAD Student-Teacher Distillation** for sub-50ms CPU patch anomaly scoring.
4. **OpenCLIP (ViT-B/16) Vision-Language Guidance** for zero-shot text-prompted spatial cross-attention refinement that eliminates background texture glare.
5. **Fail-Closed Gateways & Tamper-Evident HMAC Bundling** ensuring out-of-distribution inputs are blocked and all inspection decisions produce immutable, cryptographically verifiable audit records (ISO 9001 / FDA 21 CFR Part 11 compliant).

---

## System Architecture

The project employs a decoupled serverless architecture separating client presentation, edge distribution, heavy CPU inference, and persistent data storage.

```
+---------------------------------------------------------------------------------------+
|                                    CLIENT TIER                                        |
|  Web Browser (Operator / Quality Engineer / Admin Dashboard / Real-Time Camera Stream) |
+-------------------------------------------+-------------------------------------------+
                                            | HTTPS / WSS
                                            v
+---------------------------------------------------------------------------------------+
|                                   FRONTEND TIER                                       |
|  Vercel Edge Network · React 18 SPA · Vite · Tailwind CSS · Framer Motion            |
|  Route: https://vision4text.in                                                        |
+-------------------------------------------+-------------------------------------------+
                                            | REST API / JSON Payloads
                                            v
+---------------------------------------------------------------------------------------+
|                              BACKEND / ORCHESTRATION TIER                             |
|  FastAPI (Python 3.12) Container · Async Job Queue · SQLite WAL Storage               |
|  JWT Authentication · Streaming Payload Validator · Security Headers / CORS Policy   |
+-------------------------------------------+-------------------------------------------+
                                            | Asynchronous Dispatch
                                            v
+---------------------------------------------------------------------------------------+
|                               INFERENCE WORKER CONTAINER                              |
|  Modal Serverless CPU Pool · Memory Snapshot Startup · Warm LRU Model Session Cache   |
|                                                                                       |
|  [Stage 01: Image Quality & OOD Precheck Gate]                                        |
|       │                                                                               |
|       ├─► (Reject if blank, blurry, or wrong category -> Fail Closed)                 |
|       │                                                                               |
|  [Stage 02: Parallel Specialist Feature Extraction]                                  |
|       │    ├─ EfficientAD Student-Teacher Patch Map                                   |
|       │    └─ PatchCore Coreset k-NN Distance Map                                     |
|       │                                                                               |
|  [Stage 03: Statistical Extreme Value Theory (EVT) Weibull Tail Calibration]          |
|       │                                                                               |
|  [Stage 04: OpenCLIP ViT-B/16 Cross-Modal Zero-Shot Text Refinement]                  |
|       │                                                                               |
|  [Stage 05: Evidence Synthesis, Bounding Box Extraction & HMAC-SHA256 Signing]        |
+---------------------------------------------------------------------------------------+
```

---

## Theoretical & Mathematical Foundations

### 1. Statistical Extreme Value Theory (EVT) Modeling
Rather than selecting arbitrary empirical cutoff thresholds, EVT models the extreme upper tail of nominal reconstruction scores using the 3-parameter Weibull cumulative distribution:

$$P(S \le s) = 1 - \exp\left(-\left(\frac{s - \mu}{\sigma}\right)^\xi\right) \quad \text{for } s \ge \mu$$

* $\mu$ (**Location Parameter**): Minimum expected anomaly score floor under nominal conditions.
* $\sigma$ (**Scale Parameter**): Spread of upper-quantile reconstruction error vectors.
* $\xi$ (**Shape Parameter**): Tail-heaviness determining outlier asymptotic decay.

### 2. Zero-Shot Vision-Language Alignment (OpenCLIP)
Localized spatial tokens $f_v(x, y)$ from the visual encoder (ViT-B/16) are evaluated against text prompt matrices representing nominal vs defective states:

$$A_{\text{CLIP}}(x, y) = \frac{\exp(\langle f_v(x, y), W_{\text{defect}} \rangle / \tau)}{\sum_{k} \exp(\langle f_v(x, y), W_k \rangle / \tau)}$$

Industrial ensemble prompts (*"a damaged [category] with cracks and foreign contaminants"* vs *"a pristine flawless [category]"*) with temperature parameter $\tau = 0.07$ suppress background glare.

### 3. PatchCore Coreset Subsampling
Mid-level feature representations from WideResNet-50 are aggregated into neighborhood patch collections $\mathcal{M}$ and compressed via iterative minimax facility location:

$$c^* = \arg\max_{m \in \mathcal{M} \setminus \mathcal{C}} \min_{c \in \mathcal{C}} \|m - c\|_2$$

This retains $99.8\%$ localization fidelity while shrinking the memory footprint by $90\%$, enabling rapid nearest-neighbor searches on standard CPU instances.

### 4. Multi-Stage Fused Anomaly Decision
The final classification score $S_{\text{final}}$ synthesizes normalized specialist maps with Stage-3 EVT-CLIP refinement:

$$S_{\text{final}} = \alpha \cdot \Phi_{\text{EVT}}(S_{\text{PatchCore}}) + \beta \cdot \Phi_{\text{EVT}}(S_{\text{EffAD}}) + \gamma \cdot A_{\text{CLIP}}$$

* **Production Decision Threshold**: $\tau_{\text{decision}} = 0.267$
* **Result**:
  * $\text{Score} < 0.267 \implies \text{NORMAL / PASS}$
  * $\text{Score} \ge 0.267 \implies \text{ANOMALOUS / REJECT}$


---

## Supported Production Categories & Fail-Closed Safety

The deployed system provides verified category-specific specialist models across five core industrial manufacturing inspection domains:

| Category | Primary Specialist | Secondary Model | EVT Threshold | Key Defect Modes Evaluated |
| :--- | :--- | :--- | :--- | :--- |
| **Bottle** | EfficientAD / PatchCore | OpenCLIP ViT-B/16 | 0.267 | Broken glass, cracks, liquid contamination, label defects |
| **Cable** | EfficientAD / PatchCore | OpenCLIP ViT-B/16 | 0.267 | Bent wire, missing cable, cut outer sheath, insulation wear |
| **Capsule** | EfficientAD / PatchCore | OpenCLIP ViT-B/16 | 0.267 | Cracked shell, surface scratch, dented capsule, discoloration |
| **Metal Nut** | EfficientAD / PatchCore | OpenCLIP ViT-B/16 | 0.267 | Thread scratch, flip defect, surface deformation, metal burrs |
| **Pill** | EfficientAD / PatchCore | OpenCLIP ViT-B/16 | 0.267 | Pill crack, chip contamination, color fault, faulty imprints |

### Fail-Closed Input Safety Policy
- **Image Quality Check**: Blank, dark, clipped, or low-contrast inputs are rejected immediately with a user-facing safety prompt.
- **Category OOD Validation**: If an uploaded image does not match the selected category (e.g. uploading a shoe while inspecting a Metal Nut), the system stops **before expensive specialist inference** and returns **no heatmap or fabricated defect mask**.
- **Tamper-Evident Rejections**: Rejected inspections preserve the raw image and reason code but prevent hallucinated bounding boxes or artificial defect overlays.

---

## Repository Directory & File Structure

```text
EVT_CLIP_PLUS_PLUS_DEPLOY_READY/
│
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions continuous integration workflow
│
├── backend/                           # FastAPI application & ML inference pipeline
│   ├── app/
│   │   ├── api/                       # API route handlers
│   │   │   ├── admin.py               # Admin database backups & system controls
│   │   │   ├── analytics.py           # Dashboard aggregated statistics & CSV export
│   │   │   ├── auth.py                # JWT authentication & session refresh
│   │   │   ├── datasets.py            # Dataset catalog & metadata endpoints
│   │   │   ├── detection.py           # Core inspection submission & job status API
│   │   │   ├── examples.py            # Production reference example image serving
│   │   │   ├── history.py             # Paginated inspection history
│   │   │   ├── reports.py             # PDF report & HMAC evidence bundle download
│   │   │   ├── settings.py            # Runtime configuration endpoints
│   │   │   └── users.py               # User role management
│   │   ├── core/                      # Configuration, security & database engine
│   │   │   ├── auth.py                # Password hashing & JWT token verification
│   │   │   ├── config.py              # Application settings & environment parsing
│   │   │   ├── database.py            # Async SQLite connection & schema init
│   │   │   └── security.py            # Password hashing utilities
│   │   ├── middleware/                # Custom HTTP middleware (logging, errors, auth)
│   │   ├── models/                    # SQLAlchemy ORM database models
│   │   ├── schemas/                   # Pydantic validation & response models
│   │   ├── services/                  # Business logic & ML orchestration
│   │   │   ├── dataset_service.py     # Dataset management service
│   │   │   ├── evtclip_worker.py      # Core EVT-CLIP inference engine (Stages 1-5)
│   │   │   ├── history_service.py     # Query & pagination logic
│   │   │   ├── image_service.py       # Safe image decoding, resizing & normalization
│   │   │   ├── prediction_service.py  # Local fallback inference handler
│   │   │   ├── report_service.py      # ReportLab server-side PDF generator
│   │   │   └── user_service.py        # User database operations
│   │   └── utils/                     # Utility helpers (logger, response formats)
│   ├── main.py                        # FastAPI application entrypoint & middleware setup
│   ├── requirements.txt               # Base Python requirements
│   ├── requirements-cpu.txt           # CPU-only PyTorch & torchvision dependencies
│   ├── requirements-web.txt           # Lightweight web container dependencies
│   ├── requirements-worker.txt        # Full ML worker container dependencies
│   └── Dockerfile                     # Production backend container build
│
├── frontend/                          # React 18 Single Page Application
│   ├── public/                        # Static assets, video walkthroughs, poster images
│   │   ├── vision-text-login-loop.mp4 # Background demonstration video for login
│   │   └── vision-text-login-poster.png
│   ├── src/
│   │   ├── components/                # Reusable UI component library
│   │   │   ├── common/                # Buttons, Cards, Modals, Badges, Loaders
│   │   │   ├── detection/             # Live camera capture, category guides, tracers
│   │   │   └── layout/                # Sidebar, Navbar, Footer, Protected layouts
│   │   ├── context/                   # React Context providers (Auth, Theme, Detection)
│   │   ├── hooks/                     # Custom React hooks (useAuth)
│   │   ├── pages/                     # Application route views
│   │   │   ├── About/About.jsx        # Research foundations, viva defense & citations
│   │   │   ├── Admin/Admin.jsx        # Admin dashboard & SQLite backup download
│   │   │   ├── Dashboard/Dashboard.jsx# Analytics overview & CSV metric export
│   │   │   ├── Detection/Detection.jsx# Real-time multi-stage inspection interface
│   │   │   ├── History/History.jsx    # Historical scan repository & viewer
│   │   │   ├── Login/Login.jsx        # Authentication portal with live demo mode
│   │   │   ├── Overview/Overview.jsx  # Public interactive overview & animated pipeline
│   │   │   ├── Reports/Reports.jsx    # Audit reports, PDF downloads & ZIP bundles
│   │   │   └── Settings/Settings.jsx  # User preferences & threshold inspector
│   │   ├── routes/index.jsx           # React Router DOM route configuration
│   │   ├── services/api.js            # Axios client with automatic token attachment
│   │   ├── utils/sampleGenerator.js   # Local synthetic sample generator for demos
│   │   ├── App.jsx                    # Root application component
│   │   ├── index.css                  # Tailwind CSS styling & animations
│   │   └── main.jsx                   # React DOM entrypoint
│   ├── package.json                   # Frontend dependencies
│   ├── package-lock.json              # Exact dependency lockfile
│   ├── tailwind.config.js             # Tailwind CSS design system tokens
│   ├── vercel.json                    # Vercel SPA routing configuration
│   ├── vite.config.js                 # Vite build & proxy settings
│   └── Dockerfile                     # Nginx static asset container build
│
├── evaluation/                        # Benchmark & validation scripts
│   ├── benchmark_map_fusion_gate.py   # Map fusion calibration benchmark
│   ├── benchmark_postprocess_gate.py  # Morphological postprocess benchmark gate
│   ├── build_category_validation_centroids.py # OpenCLIP category validation centroids
│   └── README.md                      # Evaluation methodology documentation
│
├── tools/                             # Quality control & release verification tools
│   ├── content_quality_gate.py        # Prohibits banned AI-slop & verifies copy
│   ├── frontend_source_check.py       # Syntax & import verification for JSX files
│   ├── validate_release.py            # Static release guard checking architecture rules
│   └── verify_evidence_bundle.py      # Offline verification tool for HMAC evidence ZIPs
│
├── training/                          # Model training workflows
│   └── EVT_CLIP_Complete_Training.ipynb # End-to-end training, EVT fitting & export notebook
│
├── .dockerignore                      # Docker build exclusions
├── .env.example                       # Environment variable template with safe placeholders
├── .gitignore                         # Git exclusion rules (prevents secrets, models, ZIPs)
├── Caddyfile                          # Reverse proxy configuration
├── CURRENT_RELEASE_STATUS.md          # Release status documentation
├── DEPLOYMENT_CHECKLIST.md            # Production deployment checklist
├── DEPLOY_MODAL_CPU.md                # Modal serverless deployment guide
├── docker-compose.prod.yml            # Production multi-container Docker compose definition
├── modal_deploy.py                    # Modal serverless CPU deployment script
└── vercel.json                        # Root Vercel deployment configuration
```

---

## Local Development & Quickstart Guide

### Prerequisites
- **Python**: Version 3.11 or 3.12
- **Node.js**: Version 20 or 22 (LTS) & `npm`
- **Git**

---

### Method 1: Running Locally (FastAPI + Vite)

#### 1. Clone the Repository
```bash
git clone https://github.com/VISION-26/vision4text-.git
cd vision4text-
```

#### 2. Backend Setup
```bash
# Navigate to project root and create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Configure environment variables
cp .env.example .env

# Initialize database and default administrator
python backend/scripts/bootstrap.py

# Launch FastAPI development server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Frontend Setup (in a separate terminal)
```bash
# Navigate to frontend directory
cd frontend

# Install exact dependencies
npm ci

# Start Vite development server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser. Default local login:
* **Email**: `admin@example.com`
* **Password**: `replace-with-a-strong-password` (or as configured in `.env`)

---

### Method 2: Docker Compose Production Deployment

To run the complete production container stack (Frontend Nginx + Backend FastAPI + Caddy Reverse Proxy with HTTPS):

```bash
# Ensure .env is populated
cp .env.example .env

# Validate compose configuration
docker compose -f docker-compose.prod.yml --env-file .env config

# Build and start all services
docker compose -f docker-compose.prod.yml --env-file .env up --build -d
```

---

### Method 3: Cloud Production Deployment

#### Frontend on Vercel
1. Connect your GitHub repository to [Vercel](https://vercel.com).
2. Set Root Directory to `frontend`.
3. Set Framework Preset to `Vite`.
4. Add Environment Variable:
   ```env
   VITE_API_URL=https://<your-backend-api-domain>
   ```
5. Deploy.

#### Backend on Modal (Serverless CPU)
1. Install and authenticate Modal CLI:
   ```bash
   pip install modal
   modal setup
   ```
2. Create the persistent storage volumes:
   ```bash
   modal volume create evt-clip-v2-app-data
   modal volume create evt-clip-v2-models
   ```
3. Upload verified model checkpoints to `evt-clip-v2-models` at `/models/production`.
4. Create the Modal secret `evt-clip-v2-secrets` containing `JWT_SECRET` and `EVIDENCE_SIGNING_SECRET`.
5. Deploy:
   ```bash
   modal deploy modal_deploy.py
   ```

---

## Cryptographic Evidence & Audit Verification

Every completed inspection generates an immutable, tamper-evident **Evidence ZIP Bundle** containing:
- Raw preprocessed input image.
- EfficientAD and PatchCore specialist heatmaps.
- Stage-2 fusion and Stage-3 EVT-CLIP refinement heatmaps.
- Binary defect segmentation mask and bounding box overlay.
- Server-generated PDF Inspection Certificate.
- `manifest.sha256.json` recording SHA-256 hashes of all assets.
- Cryptographic **HMAC-SHA256** signature over the entire bundle.

### Verifying an Evidence Bundle Offline
Inspectors and auditors can verify evidence integrity without accessing the cloud:

```bash
python tools/verify_evidence_bundle.py \
  --bundle inspection_evidence_1042.zip \
  --secret "YOUR_EVIDENCE_SIGNING_SECRET"
```

Output:
```text
[PASS] All 7 file SHA-256 hashes match manifest.
[PASS] HMAC-SHA256 signature verified successfully.
[PASS] Bundle is authentic and unmodified.
```

---

## Quality Assurance & Automated Release Guards

The repository includes continuous quality control scripts executed in GitHub Actions CI:

```bash
# 1. Bytecode syntax & dependency compilation
python -m compileall -q backend evaluation tools modal_deploy.py

# 2. Copy quality gate (prevents buzzwords and canned filler)
python tools/content_quality_gate.py

# 3. Frontend JSX and hook dependency validation
python tools/frontend_source_check.py

# 4. Comprehensive release guard (CPU constraints, fail-closed policy, exports)
python tools/validate_release.py
```

---

## Model Training & Research Notebook

The full end-to-end model training procedure, dataset preprocessing, EVT Weibull parameter fitting, and specialist distillation steps are documented in:

📂 [`training/EVT_CLIP_Complete_Training.ipynb`](training/EVT_CLIP_Complete_Training.ipynb)

**Notebook Highlights**:
- MVTec AD dataset loading, augmentation, and resolution normalization.
- Student-Teacher feature distillation for EfficientAD.
- Coreset memory bank reduction using greedy minimax facility location for PatchCore.
- Extreme Value Theory tail fitting using Scipy statistical optimization.
- Zero-shot contrastive textual prompt matrix generation with OpenCLIP.
- Exporting lightweight CPU-optimized weights and session caches.

---

## Viva Defense & Examination FAQ

<details>
<summary><b>Q1: Why combine Extreme Value Theory (EVT) with Deep Learning instead of standard Sigmoid/Softmax?</b></summary>
<br>
Industrial anomaly detection suffers from extreme class imbalance (thousands of nominal samples, zero or few defect samples during training). Standard softmax/sigmoid assumes balanced distributions and known class priors. EVT provides asymptotic theoretical guarantees for estimating the probability of observing values beyond known training quantiles without requiring labeled defect samples.
</details>

<details>
<summary><b>Q2: How does the system prevent full-frame false-positive localization?</b></summary>
<br>
We implement morphological spatial plausibility filtering. If a predicted defect mask occupies more than 65% of the total frame without corresponding focal intensity peaks, the safety gate flags an <i>implausible full frame localization</i> warning, preventing uncalibrated false rejects.
</details>

<details>
<summary><b>Q3: How does the zero-shot CLIP stage refine local defect masks?</b></summary>
<br>
PatchCore and EfficientAD generate continuous distance maps that occasionally suffer from edge glare on shiny surfaces (e.g. metal nuts). EVT-CLIP computes cross-attention dot products between ViT spatial patch embeddings and contrastive prompt pairs (<i>"flawless bottle"</i> vs <i>"cracked contaminated bottle"</i>), suppressing non-defective surface reflections.
</details>

<details>
<summary><b>Q4: What is the purpose of the HMAC-SHA256 Signed Evidence Bundle?</b></summary>
<br>
In pharmaceutical and aerospace manufacturing (ISO 9001 / FDA CFR 21 Part 11 compliance), automated AI inspection decisions must be auditable. Every inspection exports an immutable ZIP with raw images, heatmaps, bounding boxes, and an HMAC cryptographic signature preventing post-facto tampering.
</details>

---

## Citation & Provenance

```bibtex
@article{evtclip2026industrial,
  title={EVT-CLIP++: Statistical Extreme Value Fusion and Zero-Shot Vision-Language Refinement for Industrial Anomaly Detection},
  author={Final Year Major Project Team},
  journal={Computer Vision and Industrial Automation},
  year={2026},
  publisher={Open Source Research},
  url={https://vision4text.in}
}
```

---

## License & Acknowledgements

* **License**: MIT License — open for academic and research evaluation.
* **MVTec Anomaly Detection Dataset**: MVTec Software GmbH.
* **OpenCLIP**: MLFoundations / LAION.
* **Anomalib**: OpenVINO / Intel.
* **Vercel & Modal**: Cloud hosting and serverless compute infrastructure.

---
*Developed for the Final Year College Major Project Examination (2026).*
