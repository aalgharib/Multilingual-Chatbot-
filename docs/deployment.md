# Deployment Guide

Welcome to the deployment wiki for the Multilingual Support Chatbot. This guide collects the operational runbooks that the team follows to promote the service from a local prototype into production. Each section is self-contained and can be shared with stakeholders who manage specific deployment stages.

---

## 📚 Table of contents

1. [Local developer environment](#local-developer-environment)
2. [Deploying the Chalice API to AWS](#deploying-the-chalice-api-to-aws)
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
2. **Start the Chalice API locally.**
   ```bash
   chalice local --port 8000
   ```
   The OpenAPI style endpoints are now reachable at `http://localhost:8000`.
3. **Install and run the React prototype.**
   ```bash
   cd frontend
   npm install
   npm run dev -- --host
   ```
   Vite exposes the UI on `http://localhost:5173` and proxies requests to the Chalice API. Update `VITE_API_BASE_URL` in a `.env` file to target a different backend.
4. **Run the automated tests.**
   ```bash
   pytest
   ```

---

## Deploying the Chalice API to AWS

This runbook publishes the serverless backend to AWS Lambda behind an API Gateway.

| Step | Action | Notes |
| ---- | ------ | ----- |
| 1 | **Package the application.** | Ensure `FINE_TUNED_MODEL_PATH` is set if you plan to ship a custom model. |
| 2 | **Deploy with Chalice.** | `chalice deploy --stage prod` creates the Lambda function and API Gateway. |
| 3 | **Record outputs.** | The command prints the deployed URL; copy it to your team wiki or secrets manager. |
| 4 | **Configure environment variables.** | Update the Lambda function with `FINE_TUNED_MODEL_PATH` or `ORCHESTRATOR_GENERATION_CONFIG` as required. |

> ℹ️ **Tip:** Chalice maintains deployment state in `.chalice/deployed`. Commiting this directory is optional but helps track historical releases in smaller teams.

### Rolling back

1. Run `chalice delete --stage prod` to remove the current stack.
2. Re-run `chalice deploy --stage prod --profile <profile>` pointing to the last known good commit.

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
4. **Connect the UI to the API.** Ensure CORS is enabled on the Chalice deployment (already configured to allow all origins) and update DNS records if hosting on a custom domain.

---

## Post-deployment validation

Use this checklist to ensure the system is healthy after any deployment:

- [ ] Call `POST /chat` with sample input and verify the response is localized.
- [ ] Confirm `GET /chat-history/{session_id}` returns the conversation transcripts.
- [ ] Load the React prototype and send at least one end-to-end message.
- [ ] Review AWS CloudWatch logs for errors during the smoke test window.
- [ ] Snapshot the deployment details (API URL, build hash) in the project wiki.

Once each checkbox is complete, the deployment can be marked as **Verified** in your release tracker.
