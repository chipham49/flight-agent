FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# The API key is passed at run time:  docker run -e FLIGHT_AGENT_API_KEY=... flight-agent "LAX to NYC, Dec 10"
ENTRYPOINT ["python", "-m", "flight_agent"]
