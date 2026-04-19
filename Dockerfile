FROM python:3.13-alpine

RUN groupadd -r streamlit && useradd -r -g streamlit streamlit

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY web_ui/. .

RUN chown -R streamlit:streamlit /app

USER streamlit

EXPOSE 8501

CMD [ "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]