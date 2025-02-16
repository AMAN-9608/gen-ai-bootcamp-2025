## Docker Commands
$env:LLM_ENDPOINT_PORT=9000; $env:LLM_MODEL_ID="llama3.2:1b"; $env:host_ip='127.0.0.1'; docker-compose up

curl http://localhost:9000/api/pull -d '{"model":"llama3.2:1b"}'