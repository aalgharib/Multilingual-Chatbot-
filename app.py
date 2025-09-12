import json
import datetime
import boto3
import os
from chalice import Chalice, Response
from chalice.app import CORSConfig

app = Chalice(app_name="multilingual-chatbot")

# Configure CORS
cors_config = CORSConfig(
    allow_origin="*",
    allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"],
    max_age=600,
)

# Initialize AWS clients
lex = boto3.client("lex-runtime")
translate = boto3.client("translate")
polly = boto3.client("polly")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("ChatHistory")


@app.route("/", methods=["GET"])
def index():
    with open("templates/index.html", "r") as f:
        return Response(
            body=f.read(), headers={"Content-Type": "text/html"}, status_code=200
        )


@app.route("/chat", methods=["POST"], cors=cors_config)
def chat():
    try:
        body = app.current_request.json_body
        user_input = body.get("message", "")
        source_language = body.get("source_language", "auto")
        target_language = body.get("target_language", "en")
        session_id = body.get("session_id", "default")

        # Detect language if not specified
        if source_language == "auto":
            response = translate.detect_dominant_language(Text=user_input)
            source_language = response["Languages"][0]["LanguageCode"]

        # Translate input to English for Lex processing
        if source_language != "en":
            translation = translate.translate_text(
                Text=user_input,
                SourceLanguageCode=source_language,
                TargetLanguageCode="en",
            )
            lex_input = translation["TranslatedText"]
        else:
            lex_input = user_input

        # Process with Lex
        lex_response = lex.post_text(
            botName="MultilingualBot",
            botAlias="$LATEST",
            userId=session_id,
            inputText=lex_input,
        )

        # Get bot response
        bot_response = lex_response["message"]

        # Translate bot response to target language if needed
        if target_language != "en":
            translation = translate.translate_text(
                Text=bot_response,
                SourceLanguageCode="en",
                TargetLanguageCode=target_language,
            )
            final_response = translation["TranslatedText"]
        else:
            final_response = bot_response

        # Store conversation in DynamoDB
        table.put_item(
            Item={
                "session_id": session_id,
                "timestamp": str(datetime.datetime.now()),
                "user_input": user_input,
                "bot_response": final_response,
                "source_language": source_language,
                "target_language": target_language,
            }
        )

        return Response(
            body=json.dumps(
                {
                    "response": final_response,
                    "source_language": source_language,
                    "target_language": target_language,
                }
            ),
            status_code=200,
        )

    except Exception as e:
        return Response(body=json.dumps({"error": str(e)}), status_code=500)


@app.route("/text-to-speech", methods=["POST"], cors=cors_config)
def text_to_speech():
    try:
        body = app.current_request.json_body
        text = body.get("text", "")
        language_code = body.get("language_code", "en-US")
        voice_id = body.get("voice_id", "Joanna")

        response = polly.synthesize_speech(
            Text=text, OutputFormat="mp3", VoiceId=voice_id, LanguageCode=language_code
        )

        return Response(
            body=response["AudioStream"].read(),
            headers={"Content-Type": "audio/mpeg"},
            status_code=200,
        )

    except Exception as e:
        return Response(body=json.dumps({"error": str(e)}), status_code=500)


@app.route("/chat-history/{session_id}", methods=["GET"], cors=cors_config)
def get_chat_history(session_id):
    try:
        response = table.query(
            KeyConditionExpression="session_id = :sid",
            ExpressionAttributeValues={":sid": session_id},
        )

        return Response(body=json.dumps(response["Items"]), status_code=200)

    except Exception as e:
        return Response(body=json.dumps({"error": str(e)}), status_code=500)
