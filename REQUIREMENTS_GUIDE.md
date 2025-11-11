# Requirements Files Guide

This project uses multiple requirements files optimized for different environments:

## 📦 Files Overview

### 1. `requirements-academic.txt` (Local Development - Full Features)
**Use for**: Local development with all ML capabilities
**Includes**: PyTorch, Transformers, BERT, all ML libraries
**Size**: ~3-5 GB
**Installation time**: 10-30 minutes

```bash
pip install -r requirements-academic.txt
```

**Features**:
- ✅ Full BERT classification
- ✅ Local Transformer models
- ✅ All ML training capabilities
- ✅ Complete research environment

---

### 2. `requirements-streamlit.txt` (Streamlit Cloud - Production)
**Use for**: Streamlit Cloud deployment
**Includes**: Lightweight dependencies without PyTorch/Transformers
**Size**: ~100-200 MB
**Installation time**: 2-5 minutes

```bash
pip install -r requirements-streamlit.txt
```

**Features**:
- ✅ Streamlit app fully functional
- ✅ Mistral AI via Ollama API
- ✅ OpenAI/Anthropic API support
- ✅ Rule-based classification
- ❌ No local BERT (uses API instead)

**Streamlit Cloud Configuration**:
1. Go to app settings
2. Set Python file: `streamlit_app/app.py`
3. Set Requirements file: `requirements-streamlit.txt`

---

### 3. `requirements-ci.txt` (GitHub Actions - Testing)
**Use for**: CI/CD pipeline automated testing
**Includes**: Testing tools + lightweight app dependencies
**Size**: ~100 MB
**Installation time**: 1-3 minutes

**Used by**: `.github/workflows/ci-cd.yml`

**Features**:
- ✅ Fast pipeline execution
- ✅ All unit/integration tests
- ✅ Code quality checks
- ✅ Security scanning
- ❌ No ML model training

---

### 4. `streamlit_app/requirements.txt` (Legacy - Deprecated)
**Status**: To be removed/replaced
**Redirect to**: Use `requirements-streamlit.txt` instead

---

## 🚀 Quick Start

### Local Development (Full ML)
```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements-academic.txt
streamlit run streamlit_app/app.py
```

### Streamlit Cloud Deployment
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Configure:
   - Main file: `streamlit_app/app.py`
   - Requirements: `requirements-streamlit.txt`
4. Deploy!

### Run Tests Locally
```bash
pip install -r requirements-ci.txt
pytest tests/ -v
```

---

## 📊 Comparison

| Feature | Academic | Streamlit Cloud | CI/CD |
|---------|----------|-----------------|-------|
| **Size** | 3-5 GB | 100-200 MB | 100 MB |
| **Install Time** | 10-30 min | 2-5 min | 1-3 min |
| **PyTorch** | ✅ | ❌ | ❌ |
| **Transformers** | ✅ | ❌ | ❌ |
| **BERT Local** | ✅ | ❌ | ❌ |
| **API LLMs** | ✅ | ✅ | ❌ |
| **Streamlit** | ✅ | ✅ | ✅ |
| **Testing Tools** | ❌ | ❌ | ✅ |
| **Best For** | Research | Production | CI/CD |

---

## 🔧 Troubleshooting

### GitHub Actions Timeout
**Problem**: Pipeline fails installing dependencies
**Solution**: Already fixed! Uses `requirements-ci.txt` (no PyTorch)

### Streamlit Cloud Build Fails
**Problem**: Out of memory during build
**Solution**: Use `requirements-streamlit.txt` instead of `requirements-academic.txt`

### Local Development Missing Features
**Problem**: BERT classification not working
**Solution**: Install full dependencies with `requirements-academic.txt`

---

## 📝 Maintenance

When adding new dependencies:

1. **Core dependencies** → Add to ALL files
2. **ML/Training only** → Add ONLY to `requirements-academic.txt`
3. **Testing tools** → Add ONLY to `requirements-ci.txt`
4. **API libraries** → Add to `academic` AND `streamlit`

---

**Last Updated**: 2025-11-11
**Maintained by**: FreeMobilaChat Team
