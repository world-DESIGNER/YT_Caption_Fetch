from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter
from flask import Flask, request, jsonify
from waitress import serve

app = Flask(__name__)

@app.route('/captions', methods=['GET'])
def fetch_captions():
    video_id = request.args.get('video_id')
    format_type = request.args.get('format', 'text')
    transcript_type = request.args.get('type', 'manual')
    lang = request.args.get('lang')

    if not lang:
        return jsonify({"error": "No language provided. Please provide a language code with the 'lang' parameter."}), 400
    if not video_id:
        return jsonify({"error": "No video ID provided. Please provide a video ID with the 'video_id' parameter."}), 400

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcripts = {}

        for transcript in transcript_list:
            if (transcript_type == 'auto' and not transcript.is_generated) or (transcript_type == 'manual' and transcript.is_generated):
                continue

            if transcript.language_code != lang:
                continue

            lang_transcript = transcript.fetch()

            if format_type.lower() == 'srt':
                formatter = SRTFormatter()
                formatted_transcript = formatter.format_transcript(lang_transcript)
            else:
                formatted_transcript = [t['text'] for t in lang_transcript]

            transcripts[transcript.language_code] = formatted_transcript

        return jsonify({"captions": transcripts})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/available_languages', methods=['GET'])
def fetch_available_languages():
    video_id = request.args.get('video_id')

    if not video_id:
        return jsonify({"error": "No video ID provided. Please provide a video ID with the 'video_id' parameter."}), 400

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        language_codes = set()

        for transcript in transcript_list:
            language_codes.add(transcript.language_code)

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
