#!/bin/bash

# Stop on errors
set -e

# Set Variables
PROJECT_ID="drs-nlp-chatbot"
REGION="us-east1"
IMAGE_TAG=$(git rev-parse --short HEAD)  # Git commit hash as tag

# Authenticate Docker with GCR (one time only)
#gcloud auth login
#gcloud config set project $PROJECT_ID
#gcloud auth configure-docker
#gcloud services enable containerregistry.googleapis.com storage.googleapis.com
#gcloud config get-value project

# Build and push Rasa Chatbot image
echo "Building and pushing Rasa Chatbot image..."
docker build -t gcr.io/$PROJECT_ID/rasa-chatbot:$IMAGE_TAG -f Dockerfile.rasa .
docker push gcr.io/$PROJECT_ID/rasa-chatbot:$IMAGE_TAG

# Build and push Action Server image
#echo "Building and pushing Action Server image..."
#docker build -t gcr.io/$PROJECT_ID/rasa-actions:$IMAGE_TAG -f Dockerfile.actions .
#docker push gcr.io/$PROJECT_ID/rasa-actions:$IMAGE_TAG

# Build and push Frontend image
#echo "Building and pushing Frontend image..."
#docker build -t gcr.io/$PROJECT_ID/frontend:$IMAGE_TAG -f Dockerfile.frontend .
#docker push gcr.io/$PROJECT_ID/frontend:$IMAGE_TAG

# Deploy Rasa Chatbot to Cloud Run
echo "Deploying Rasa Chatbot to Cloud Run..."
gcloud run deploy rasa-chatbot \
  --image gcr.io/$PROJECT_ID/rasa-chatbot:$IMAGE_TAG \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory=4000Mi

# Deploy Action Server to Cloud Run
#echo "Deploying Action Server to Cloud Run..."
#gcloud run deploy rasa-actions \
#  --image gcr.io/$PROJECT_ID/rasa-actions:$IMAGE_TAG \
#  --platform managed \
#  --region $REGION \
#  --allow-unauthenticated \
#  --port 5055

# Deploy Frontend to Cloud Run
#echo "Deploying Frontend to Cloud Run..."
#gcloud run deploy frontend \
#  --image gcr.io/$PROJECT_ID/frontend:$IMAGE_TAG \
#  --platform managed \
#  --region $REGION \
#  --allow-unauthenticated \
#  --port 80

# Update services
echo "Clearing cached containers..."
#gcloud run services update-traffic frontend --to-latest --region=$REGION
gcloud run services update-traffic rasa-chatbot --to-latest --region=$REGION
#gcloud run services update-traffic rasa-actions --to-latest --region=$REGION

echo "Deployment complete!"
