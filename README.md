# Memory Layer with new UI

An always-on memory agent built on the **Gemini Enterprise Agent Platform**, with a Streamlit dashboard for browsing, querying, and ingesting memories.

## Gemini Enterprise Agent Platform

### Configure Application Default Credentials for authentication

Set environment variables:

```bash
export GOOGLE_CLOUD_PROJECT="my-gcp-project"
```

```bash
export GOOGLE_CLOUD_LOCATION="global"
```

Verify they are set:

```bash
echo $GOOGLE_CLOUD_PROJECT
```

```bash
echo $GOOGLE_CLOUD_LOCATION
```

Authenticate using Application Default Credentials:

```bash
gcloud auth application-default login
```

## How to run the Memory Layer using uv

Setup (once):

```bash
uv venv
```

```bash
uv pip install -r requirements.txt
```

Run agent:

```bash
uv run agent.py
```

Run dashboard:

```bash
uv run streamlit run dashboard.py --server.headless true
```
