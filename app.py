from flask import Flask, request, render_template, send_from_directory, redirect, url_for, jsonify
import os
import moviepy.editor as mp
import math
import time

app = Flask(__name__)

# Define upload and output folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure folders exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Global variable to store progress
progress = {
    "current_part": 0,
    "total_parts": 0,
    "percentage": 0,
    "folder": "",
    "available_parts": []
}

def split_video(input_video_path, clip_duration, output_folder):
    global progress
    try:
        video = mp.VideoFileClip(input_video_path)
        video_duration = video.duration
        num_clips = math.ceil(video_duration / clip_duration)
        progress["total_parts"] = num_clips
        progress["folder"] = os.path.basename(output_folder)
        progress["available_parts"] = []

        for i in range(num_clips):
            progress["current_part"] = i + 1
            progress["percentage"] = int(((i + 1) / num_clips) * 100)
            start_time = i * clip_duration
            end_time = min((i + 1) * clip_duration, video_duration)
            subclip = video.subclip(start_time, end_time)
            output_filename = os.path.join(output_folder, f"Part_{i+1}.mp4")
            subclip.write_videofile(output_filename, codec='libx264', audio_codec='aac')
            progress["available_parts"].append(f"Part_{i+1}.mp4")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        if 'video' in locals():
            video.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['video']
        clip_duration = int(request.form['duration'])
        if file:
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(input_path)
            video = mp.VideoFileClip(input_path)
            video_duration = video.duration
            video.close()
            estimated_time = video_duration
            estimated_time_str = time.strftime("%H:%M:%S", time.gmtime(estimated_time))
            return render_template('confirm.html', filename=file.filename, duration=video_duration, estimated_time=estimated_time_str, clip_duration=clip_duration)
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if request.method == 'POST':
        filename = request.form['filename']
        clip_duration = int(request.form['clip_duration'])
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_folder = os.path.join(app.config['OUTPUT_FOLDER'], os.path.splitext(filename)[0])
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        success = split_video(input_path, clip_duration, output_folder)
        if success:
            return redirect(url_for('download', folder=os.path.basename(output_folder)))
        else:
            return "Error processing video. Please try again."

@app.route('/progress')
def get_progress():
    global progress
    return jsonify(progress)

@app.route('/preview/<folder>/<filename>')
def preview(folder, filename):
    output_folder = os.path.join(app.config['OUTPUT_FOLDER'], folder)
    return send_from_directory(output_folder, filename, mimetype='video/mp4')

@app.route('/download/<folder>')
def download(folder):
    output_folder = os.path.join(app.config['OUTPUT_FOLDER'], folder)
    if not os.path.exists(output_folder):
        return "Folder not found. Please try again."
    files = os.listdir(output_folder)
    if not files:
        return "No files found in the folder."
    return render_template('download.html', folder=folder, files=files)

@app.route('/download/<folder>/<filename>')
def download_file(folder, filename):
    output_folder = os.path.join(app.config['OUTPUT_FOLDER'], folder)
    return send_from_directory(output_folder, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=False)

