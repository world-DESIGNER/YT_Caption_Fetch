from flask import Flask, request, jsonify, send_from_directory
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter
from waitress import serve

app = Flask(__name__)

@app.route('/captions')
def fetch_captions():
    video_id = request.args.get('video_id')
    format_type = request.args.get('format', 'srt')
    transcript_type = request.args.get('type', 'manual')
    lang = request.args.get('lang', 'en')  # Default to English if no language is provided

    if not lang:
        return jsonify({"error": "No language provided. Please provide a language code with the 'lang' parameter."}), 400
    if not video_id:
        return jsonify({"error": "No video ID provided. Please provide a video ID with the 'video_id' parameter."}), 400

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        
        # Selecting the transcript type
        if transcript_type == 'manual':
            transcript = transcript_list.find_manually_created_transcript([lang])
        elif transcript_type == 'auto':
            transcript = transcript_list.find_generated_transcript([lang])
        
        # Fetch the transcript data
        transcript_data = transcript.fetch()

        # Format the transcript data according to the format_type
        if format_type.lower() == 'srt':
            formatter = SRTFormatter()
            formatted_transcript = formatter.format_transcript(transcript_data)
        else:
            formatted_transcript = "\n".join([t['text'] for t in transcript_data])

        return jsonify({"captions": formatted_transcript})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

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
