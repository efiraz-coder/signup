import os
from flask import Flask, render_template, request, send_from_directory
from pdf2image import convert_from_path
from PIL import Image
import base64
from io import BytesIO

app = Flask(__name__)

# נתיב לתיקיית bin (ודא שזה נתיב מדויק לתיקייה שיש בה את pdftoppm.exe)
POPPLER_PATH = os.path.join(os.getcwd(), 'bin')
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/', methods=['GET'])
def index():
    return '''<form action="/upload" method="post" enctype="multipart/form-data">
              <input type="file" name="pdf_file"><button type="submit">העלה</button></form>'''

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['pdf_file']
    path = os.path.join(UPLOAD_FOLDER, "original.pdf")
    file.save(path)
    try:
        images = convert_from_path(path, poppler_path=POPPLER_PATH)
        images[-1].save(os.path.join(UPLOAD_FOLDER, "page.png"), "PNG")
        return 'הקובץ הועלה. <a href="/sign">לחץ לחתימה</a>'
    except Exception as e:
        return f"שגיאת המרה: {str(e)}"

@app.route('/sign')
def sign():
    return render_template('sign.html')

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    sig_data = base64.b64decode(data['sig'].split(',')[1])
    x, y = int(data['x']), int(data['y'])
    
    img = Image.open(os.path.join(UPLOAD_FOLDER, "page.png")).convert("RGBA")
    sig = Image.open(BytesIO(sig_data)).convert("RGBA")
    
    img.paste(sig, (x, y), sig)
    img.convert("RGB").save(os.path.join(UPLOAD_FOLDER, "signed.pdf"), "PDF")
    return {"status": "ok"}

@app.route('/<filename>')
def get_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)