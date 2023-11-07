from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter
from flask import Flask, request, jsonify, send_from_directory
from waitress import serve
import re

app = Flask(__name__)

@app.route('/captions', methods=['GET'])
def fetch_captions():
    url = request.args.get('url')
    format_type = request.args.get('format', 'text')  # default to 'text' if no format is provided
    transcript_type = request.args.get('type', 'manual')  # default to 'manual' if no type is provided
    lang = request.args.get('lang')  # no default value

    # Check if lang parameter is provided
    if not lang:
        return jsonify({"error": "No language provided. Please provide a language code with the 'lang' parameter."}), 400

    try:
        video_id = re.search(r"(?<=v=)[^&#]+|(?<=be/)[^&#]+", url)
        video_id = video_id.group()

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcripts = {}

        for transcript in transcript_list:
            if (transcript_type == 'auto' and not transcript.is_generated) or (transcript_type == 'manual' and transcript.is_generated):
                continue

            if transcript.language_code != lang:  # Skip if the transcript's language does not match the requested language
                continue

            lang_transcript = transcript.fetch()

            if format_type.lower() == 'srt':
                formatter = SRTFormatter()
                formatted_transcript = formatter.format_transcript(lang_transcript)
            else:  # if format is not 'srt', just return the captions
                formatted_transcript = [t['text'] for t in lang_transcript]

            transcripts[transcript.language_code] = formatted_transcript

        return jsonify({"captions": transcripts})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/available_languages', methods=['GET'])
def fetch_available_languages():
    url = request.args.get('url')

    try:
        video_id = re.search(r"(?<=v=)[^&#]+|(?<=be/)[^&#]+", url)
        video_id = video_id.group()

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Create a set to ensure no duplicate language codes
        language_codes = set()

        for transcript in transcript_list:
            language_codes.add(transcript.language_code)

        return jsonify({"available_languages": list(language_codes)})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/.well-known/ai-plugin.json')
def serve_ai_plugin():
    return send_from_directory('.', 'ai-plugin.json', mimetype='application/json')

@app.route('/.well-known/openapi.yaml')
def serve_openapi_yaml():
    return send_from_directory('.', 'openapi.yaml', mimetype='text/yaml')

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8080)