from flask import Flask, request, send_file
import os
import time
import glob
import shutil
from modify_conf import download_ini_and_modify

UPLOAD_DIR = 'uploads'
MODIFIED_FOLDER = 'modified'
LATEST_FILE = os.path.join(UPLOAD_DIR, 'conf_latest.conf')
MAX_BACKUPS = 10

app = Flask(__name__)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(MODIFIED_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_conf():
    uploaded_file = request.files.get('file')
    if not uploaded_file:
        return "No file uploaded", 400

    content = uploaded_file.read().decode('utf-8').strip()
    if not content:
        return "Uploaded file is empty", 400

    # 获取上传内容的去除首行版本
    content_lines = content.splitlines()
    content_body = '\n'.join(content_lines[1:]).strip() if len(content_lines) > 1 else ''

    # 如果没有 conf_latest.conf，就找最近的文件创建一个
    if not os.path.exists(LATEST_FILE):
        recent_files = sorted(
            [f for f in glob.glob(os.path.join(UPLOAD_DIR, 'conf_*.conf')) if 'latest' not in f],
            reverse=True
        )
        if recent_files:
            shutil.copy(recent_files[0], LATEST_FILE)

    # 如果此时有 latest 文件，则进行内容比较
    if os.path.exists(LATEST_FILE):
        with open(LATEST_FILE, 'r', encoding='utf-8') as f:
            latest_lines = f.read().splitlines()
            latest_body = '\n'.join(latest_lines[1:]).strip() if len(latest_lines) > 1 else ''
        if content_body == latest_body:
            return "Same as latest (ignoring first line), not saved", 200

    # 内容不同，保存新文件
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f'conf_{timestamp}.conf'
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    # 复制为最新文件
    shutil.copy(filepath, LATEST_FILE)

    # 清理旧版本，保留最近 MAX_BACKUPS 个
    files = sorted(glob.glob(os.path.join(UPLOAD_DIR, 'conf_*.conf')))
    if len(files) > MAX_BACKUPS:
        for old_file in files[:-MAX_BACKUPS]:
            if os.path.basename(old_file) != 'conf_latest.conf':
                os.remove(old_file)

    return f"New config uploaded as {filename}", 200


@app.route('/download', methods=['GET'])
def download_conf():
    output_path = os.path.join(MODIFIED_FOLDER, 'shadow-modified.conf')
    # 确保存在可处理的文件
    if not os.path.exists(LATEST_FILE):
        # 尝试找到最近的备份作为 latest
        backups = sorted(glob.glob(os.path.join(UPLOAD_DIR, 'conf_*.conf')), reverse=True)
        for f in backups:
            if os.path.basename(f) != 'conf_latest.conf':
                shutil.copy(f, LATEST_FILE)
                break
        else:
            return "No uploaded file found", 404

    try:
        download_ini_and_modify(
            input_path=LATEST_FILE,
            output_path=output_path
        )
    except Exception as e:
        return f'处理配置失败：{str(e)}', 500

    return send_file(output_path, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)