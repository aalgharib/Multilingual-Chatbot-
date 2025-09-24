# Deployment Guide

Welcome to the deployment wiki for the Multilingual Support Chatbot. This guide collects the operational runbooks that the team follows to promote the service from a local prototype into production. Each section is self-contained and can be shared with stakeholders who manage specific deployment stages.

---

## 📚 Table of contents

1. [Local developer environment](#local-developer-environment)

2. [Deploying the Flask API](#deploying-the-flask-api)

3. [Publishing the React prototype](#publishing-the-react-prototype)
4. [Post-deployment validation](#post-deployment-validation)

---

## Local developer environment

This runbook spins up the entire stack on a laptop for rapid iteration.

### Prerequisites

- Python 3.8 or newer
- Node.js 18+ and npm
- AWS CLI configured with developer credentials

### Steps

1. **Clone the repository and install Python dependencies.**
   ```bash
   git clone <repo-url>
   cd Multilingual-Chatbot-
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Start the Flask API locally.**
   ```bash
   flask --app app run --port 8000
   ```
   The endpoints are now reachable at `http://localhost:8000`.

3. **Install and run the React prototype.**
   ```bash
   cd frontend
   npm install
   npm run dev -- --host
   ```

   `npm install` is required even if you already ran `pip install -r requirements.txt`; the two commands manage different dependency sets. Vite exposes the UI on `http://localhost:5173` and proxies requests to the Flask API. Update `VITE_API_BASE_URL` in a `.env` file to target a different backend.

4. **Run the automated tests.**
   ```bash
   pytest
   ```

---


## Deploying the Flask API

This runbook packages the Flask service for environments such as AWS Elastic Beanstalk, ECS, or any container platform.

| Step | Action | Notes |
| ---- | ------ | ----- |
| 1 | **Build a production image.** | Create a Dockerfile that installs `requirements.txt` and exposes port `8000` via Gunicorn: `gunicorn --bind 0.0.0.0:8000 app:app`. |
| 2 | **Publish the image.** | Push to Amazon ECR, GitHub Container Registry, or your preferred registry. |
| 3 | **Provision the runtime.** | Create an ECS service, Fargate task, or other container host referencing the pushed image. |
| 4 | **Configure environment variables.** | Set `FINE_TUNED_MODEL_PATH` and `ORCHESTRATOR_GENERATION_CONFIG` as required. |
| 5 | **Expose networking.** | Attach a load balancer or API Gateway HTTP integration that forwards traffic to port `8000`. |

> ℹ️ **Tip:** The Flask app defaults to port 8000 so it remains compatible with the React prototype configuration. Override the `PORT` environment variable if your platform requires a different port.

### Rolling back

1. Re-deploy the last known good container image.
2. Redeploy infrastructure templates (ECS service, Beanstalk environment, etc.) with the stable image reference if configuration drift is suspected.


---

## Publishing the React prototype

This runbook converts the Vite-based prototype into static assets that can be hosted alongside the API or on a CDN.

1. **Set the API base URL** in `frontend/.env.production` before building:
   ```bash
   echo "VITE_API_BASE_URL=https://api.example.com" > frontend/.env.production
   ```
2. **Create an optimized build.**
   ```bash
   cd frontend
   npm install
   npm run build
   ```
   The compiled assets live in `frontend/dist` and can be uploaded to S3, CloudFront, or any static host.
3. **Upload the build artifacts.**
   - **S3:** `aws s3 sync dist/ s3://your-bucket-name --acl public-read`
   - **GitHub Pages:** Push `dist` to the `gh-pages` branch with your preferred automation.

4. **Connect the UI to the API.** Ensure CORS is enabled on the Flask deployment (already configured to allow all origins) and update DNS records if hosting on a custom domain.


---

## Post-deployment validation

Use this checklist to ensure the system is healthy after any deployment:

- [ ] Call `POST /chat` with sample input and verify the response is localized.
- [ ] Confirm `GET /chat-history/{session_id}` returns the conversation transcripts.
- [ ] Load the React prototype and send at least one end-to-end message.
- [ ] Review AWS CloudWatch logs for errors during the smoke test window.
- [ ] Snapshot the deployment details (API URL, build hash) in the project wiki.

Once each checkbox is complete, the deployment can be marked as **Verified** in your release tracker.
