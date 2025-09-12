# Multilingual Support Chatbot

A serverless multilingual chatbot using AWS AI services to facilitate communication between users who speak different languages.

## Team Members

- Keshav Anand Singh (300988081)
- Blessing Akintonde (301264139)
- Cole Ramsey (301333287)
- Nicholas Laprade (301266745)
- Ali Al-gharibawi (301238399)

## Project Overview

This project implements a multilingual chatbot that integrates Amazon Lex, Amazon Translate, and Amazon Polly to provide text and speech translation capabilities. The system is built using a serverless architecture for cost-effectiveness and scalability.

## Features

- Real-time multilingual text translation
- Text-to-speech conversion
- Natural language understanding
- Secure data storage
- Scalable serverless architecture

## Technical Stack

- AWS Lambda
- Amazon Lex
- Amazon Translate
- Amazon Polly
- AWS DynamoDB
- AWS CloudWatch
- AWS Chalice

## Prerequisites

- AWS Account with appropriate permissions
- Python 3.8+
- AWS CLI configured
- Chalice framework

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure AWS credentials
4. Deploy the application:
   ```bash
   chalice deploy
   ```

## Project Structure

```
├── README.md
├── requirements.txt
├── app.py
├── chalice.json
├── tests/
└── docs/
```

## Estimated Costs

- AWS Lambda: $0.20 per 1 million requests
- Amazon Lex: $4 per 1,000 speech requests / $0.75 per 1,000 text requests
- Amazon Translate: $15 per 1 million characters
- Amazon Polly: $4 per 1 million characters
- AWS DynamoDB: Free tier includes 25GB, then ~$0.25 per GB/month
- AWS CloudWatch: ~$0.50 per GB of log storage

## License

This project is part of COMP 264: Cloud Machine Learning course at Ryerson University.
