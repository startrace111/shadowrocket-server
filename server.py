from flask import Flask, request, send_file
import os
from modify_conf import download_ini_and_modify

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
MODIFIED_FOLDER = 'modified'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODIFIED_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part in request', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    input_path = os.path.join(UPLOAD_FOLDER, 'shadow-original.conf')
    file.save(input_path)

    return '配置文件上传成功，稍后在下载时处理。'

@app.route('/download')
def download_conf():
    input_path = os.path.join(UPLOAD_FOLDER, 'shadow-original.conf')
    output_path = os.path.join(MODIFIED_FOLDER, 'shadow-modified.conf')

    if not os.path.exists(input_path):
        return '未找到上传的配置文件，请先上传。', 404

    try:
        download_ini_and_modify(
            input_path=input_path,
            output_path=output_path
        )
    except Exception as e:
        return f'处理配置失败：{str(e)}', 500

    return send_file(output_path, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)