from flask import Flask, request, jsonify, send_from_directory
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter
from waitress import serve
import time

app = Flask(__name__)

RATE_LIMIT = 1  # initial delay between API calls in seconds
MAX_RETRIES = 5  # maximum number of retries after encountering an error

def fetch_transcript(video_id, lang, transcript_type):
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    transcript = None
    
    if transcript_type == 'manual':
        transcript = transcript_list.find_manually_created_transcript([lang])
    elif transcript_type == 'auto':
        transcript = transcript_list.find_generated_transcript([lang])
    
    return transcript.fetch()

@app.route('/captions')
def fetch_captions():
    video_id = request.args.get('video_id')
    format_type = request.args.get('format', 'srt')
    transcript_type = request.args.get('type', 'manual')
    lang = request.args.get('lang', 'en')

    if not video_id or not lang:
        return jsonify({"error": "Missing required parameter: 'video_id' or 'lang'."}), 400

    try:
        attempts = 0
        while attempts < MAX_RETRIES:
            try:
                time.sleep(RATE_LIMIT ** attempts)  # exponential backoff
                transcript_data = fetch_transcript(video_id, lang, transcript_type)
                
                if format_type.lower() == 'srt':
                    formatter = SRTFormatter()
                    formatted_transcript = formatter.format_transcript(transcript_data)
                else:
                    formatted_transcript = "\n".join([t['text'] for t in transcript_data])

                return jsonify({"captions": formatted_transcript})
            except YouTubeTranscriptApi.CouldNotRetrieveTranscript as e:
                attempts += 1
                if attempts == MAX_RETRIES:
                    return jsonify({"error": "Failed to retrieve captions after retries."}), 429
                continue
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/available_languages')
def fetch_available_languages():
    video_id = request.args.get('video_id')

    if not video_id:
        return jsonify({"error": "No video ID provided. Please provide a video ID with the 'video_id' parameter."}), 400

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        language_codes = {transcript.language_code for transcript in transcript_list}

        return jsonify({"available_languages": list(language_codes)})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/.well-known/ai-plugin.json')
def serve_ai_plugin():
    return send_from_directory('.well-known', 'ai-plugin.json', mimetype='application/json')

@app.route('/.well-known/openapi.yaml')
def serve_openapi_yaml():
    return send_from_directory('.well-known', 'openapi.yaml', mimetype='text/yaml')

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8080)
