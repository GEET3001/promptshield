# Hugging Face Docker Space running Streamlit.
FROM python:3.11-slim

# HF Spaces runs containers as uid 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH \
    DB_PATH=/tmp/promptshield.db \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
# CPU-only torch first (much smaller image), then everything else
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

EXPOSE 8501
CMD ["streamlit", "run", "app/Home.py", "--server.port=8501", "--server.address=0.0.0.0", \
     "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
