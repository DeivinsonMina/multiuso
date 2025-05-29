from flask import Flask, render_template, request, url_for, redirect, send_file
import os
import qrcode
import yt_dlp
import re
from PIL import Image, ImageDraw, ImageFont
import uuid
import smtplib
from email.message import EmailMessage
import requests
from gtts import gTTS
import random
import string
from pypdf import PdfReader, PdfWriter

app = Flask(__name__)
@app.route('/descargar-rockyou')
def descargar_rockyou():
    try:
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        rockyou_path = os.path.join(static_dir, 'rockyou.txt')

        if not os.path.exists(static_dir):
            os.makedirs(static_dir)

        if not os.path.exists(rockyou_path):
            url = "https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt"
            r = requests.get(url, stream=True)
            with open(rockyou_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return "✅ Archivo rockyou.txt descargado correctamente."
        else:
            return "ℹ️ El archivo ya existe en static/"
    except Exception as e:
        return f"❌ Error al descargar: {e}"

@app.route('/')
def main_menu():
    return render_template('index.html')

@app.route('/qr', methods=['GET'])
def qr():
    # Muestra el formulario para generar QR
    return render_template('qr_form.html')

@app.route('/generate', methods=['POST'])
def generate():
    texto = request.form['texto']
    archivo = request.form['archivo']
    ruta_archivo = os.path.join('static', archivo)
    generar_qr(texto, ruta_archivo)
    qr_url = url_for('static', filename=archivo)
    return render_template('qr.html', qr_url=qr_url)

def generar_qr(texto, archivo_salida):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(archivo_salida)


def clean_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

@app.route('/youtube-mp3', methods=['GET', 'POST'])
def youtube_mp3():
    if request.method == 'POST':
        url = request.form['url']
        # Descarga el audio con el nombre limpio
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = clean_filename(info['title'])
        output_template = os.path.join('static', f'{title}.%(ext)s')
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        filename = f"{title}.mp3"
        # Verifica que el archivo existe antes de mostrar el enlace
        file_path = os.path.join('static', filename)
        if os.path.exists(file_path):
            return render_template('youtube_mp3.html', filename=filename)
        else:
            return render_template('youtube_mp3.html', error="No se pudo descargar el archivo.")
    return render_template('youtube_mp3.html')

@app.route('/youtube-mp4', methods=['GET', 'POST'])
def youtube_mp4():
    if request.method == 'POST':
        url = request.form['url']
        # Obtén el título limpio antes de descargar
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = clean_filename(info['title'])
        output_template = os.path.join('static', f'{title}.%(ext)s')
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'quiet': True,
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        filename = f"{title}.mp4"
        file_path = os.path.join('static', filename)
        if os.path.exists(file_path):
            return render_template('youtube_mp4.html', filename=filename)
        else:
            return render_template('youtube_mp4.html', error="No se pudo descargar el archivo.")
    return render_template('youtube_mp4.html')

@app.route('/tiktok', methods=['GET', 'POST'])
def tiktok():
    if request.method == 'POST':
        url = request.form['url']
        tipo = request.form['tipo']  # 'video' o 'audio'
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = clean_filename(info['title'])
        if tipo == 'audio':
            output_template = os.path.join('static', f'{title}.%(ext)s')
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'noplaylist': True,
            }
            ext = 'mp3'
        else:
            output_template = os.path.join('static', f'{title}.%(ext)s')
            ydl_opts = {
                'format': 'mp4',
                'outtmpl': output_template,
                'quiet': True,
                'noplaylist': True,
            }
            ext = 'mp4'
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        filename = f"{title}.{ext}"
        file_path = os.path.join('static', filename)
        if os.path.exists(file_path):
            return render_template('tiktok.html', filename=filename, tipo=tipo)
        else:
            return render_template('tiktok.html', error="No se pudo descargar el archivo.")
    return render_template('tiktok.html')


@app.route('/meme', methods=['GET', 'POST'])
def meme():
    meme_url = None
    error = None
    if request.method == 'POST':
        if 'imagen' not in request.files:
            error = "No se subió ninguna imagen."
        else:
            imagen = request.files['imagen']
            texto_superior = request.form.get('texto_superior', '')
            texto_inferior = request.form.get('texto_inferior', '')
            if imagen.filename == '':
                error = "No se seleccionó ninguna imagen."
            else:
                try:
                    img = Image.open(imagen).convert("RGB")
                    draw = ImageDraw.Draw(img)
                    # Usa una fuente estándar de Linux, ajusta la ruta si es necesario
                    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                    font_size = int(img.height * 0.08)
                    font = ImageFont.truetype(font_path, font_size)
                    # Texto superior
                    if texto_superior:
                        bbox = draw.textbbox((0, 0), texto_superior, font=font)
                        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                        draw.text(
                            ((img.width-w)/2, 10),
                            texto_superior,
                            font=font,
                            fill="white",
                            stroke_width=2,
                            stroke_fill="black"
                        )
                    # Texto inferior
                    if texto_inferior:
                        bbox = draw.textbbox((0, 0), texto_inferior, font=font)
                        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                        draw.text(
                            ((img.width-w)/2, img.height-h-10),
                            texto_inferior,
                            font=font,
                            fill="white",
                            stroke_width=2,
                            stroke_fill="black"
                        )
                    # Guarda el meme con un nombre único
                    meme_filename = f"meme_{uuid.uuid4().hex}.jpg"
                    meme_path = os.path.join('static', meme_filename)
                    img.save(meme_path)
                    meme_url = url_for('static', filename=meme_filename)
                except Exception as e:
                    error = f"Error al generar el meme: {e}"
    return render_template('meme.html', meme_url=meme_url, error=error)


@app.route('/email', methods=['GET', 'POST'])
def email():
    enviado = False
    error = None
    if request.method == 'POST':
        remitente = request.form['remitente']
        password = request.form['password']
        asunto = request.form['asunto']
        mensaje = request.form['mensaje']
        destinatarios = request.form['destinatarios'].splitlines()
        try:
            msg = EmailMessage()
            msg['Subject'] = asunto
            msg['From'] = remitente
            msg['To'] = ", ".join(destinatarios)
            msg.set_content(mensaje)
            # Conexión SMTP (Gmail)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(remitente, password)
                smtp.send_message(msg)
            enviado = True
        except Exception as e:
            error = f"Error al enviar: {e}"
    return render_template('email.html', enviado=enviado, error=error)



@app.route('/shortener', methods=['GET', 'POST'])
def shortener():
    short_url = None
    error = None
    if request.method == 'POST':
        url = request.form['url']
        try:
            response = requests.get(f'https://tinyurl.com/api-create.php?url={url}')
            if response.status_code == 200 and response.text.startswith('http'):
                short_url = response.text
            else:
                error = "No se pudo acortar la URL. Verifica que sea válida."
        except Exception as e:
            error = f"Error al acortar la URL: {e}"
    return render_template('shortener.html', short_url=short_url, error=error)



@app.route('/tts', methods=['GET', 'POST'])
def tts():
    audio_url = None
    error = None
    if request.method == 'POST':
        texto = request.form.get('texto', '').strip()
        idioma = request.form.get('idioma', 'es')
        if not texto:
            error = "Por favor, ingresa un texto."
        else:
            try:
                tts = gTTS(text=texto, lang=idioma)
                filename = f"tts_{uuid.uuid4().hex}.mp3"
                filepath = os.path.join('static', filename)
                tts.save(filepath)
                audio_url = url_for('static', filename=filename)
            except Exception as e:
                error = f"Error al generar el audio: {e}"
    return render_template('tts.html', audio_url=audio_url, error=error)

@app.route('/currency', methods=['GET', 'POST'])
def currency():
    resultado = None
    error = None
    amount = None
    from_currency = None
    to_currency = None
    # Lista de monedas populares (puedes agregar más)
    monedas = [
        ('USD', 'Dólar estadounidense'),
        ('EUR', 'Euro'),
        ('COP', 'Peso colombiano'),
        ('ARS', 'Peso argentino'),
        ('MXN', 'Peso mexicano'),
        ('BRL', 'Real brasileño'),
        ('CLP', 'Peso chileno'),
        ('GBP', 'Libra esterlina'),
        ('JPY', 'Yen japonés'),
        ('PEN', 'Sol peruano'),
    ]
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            from_currency = request.form['from_currency']
            to_currency = request.form['to_currency']
            url = f"https://open.er-api.com/v6/latest/{from_currency}"
            response = requests.get(url)
            data = response.json()
            if data['result'] == 'success' and to_currency in data['rates']:
                resultado = float(amount) * data['rates'][to_currency]
            else:
                error = "No se pudo obtener la tasa de cambio."
        except Exception as e:
            error = f"Error: {e}"
    return render_template(
        'currency.html',
        resultado=resultado,
        error=error,
        amount=amount,
        from_currency=from_currency,
        to_currency=to_currency,
        monedas=monedas
    )


@app.route('/password', methods=['GET', 'POST'])
def password():
    password_generada = None
    error = None
    if request.method == 'POST':
        try:
            longitud = int(request.form.get('longitud', 12))
            usar_mayus = 'mayusculas' in request.form
            usar_minus = 'minusculas' in request.form
            usar_num = 'numeros' in request.form
            usar_esp = 'especiales' in request.form

            caracteres = ''
            if usar_mayus:
                caracteres += string.ascii_uppercase
            if usar_minus:
                caracteres += string.ascii_lowercase
            if usar_num:
                caracteres += string.digits
            if usar_esp:
                caracteres += string.punctuation

            if not caracteres:
                error = "Selecciona al menos un tipo de carácter."
            else:
                password_generada = ''.join(random.choice(caracteres) for _ in range(longitud))
        except Exception as e:
            error = f"Error: {e}"
    return render_template('password.html', password_generada=password_generada, error=error)


@app.route('/pdf-unlock', methods=['GET', 'POST'])
def pdf_unlock():
    unlocked_url = None
    error = None
    if request.method == 'POST':
        if 'pdf_file' not in request.files or request.files['pdf_file'].filename == '':
            error = "Por favor, selecciona un archivo PDF."
        else:
            pdf_file = request.files['pdf_file']
            password = request.form.get('password', '')
            try:
                reader = PdfReader(pdf_file)
                if reader.is_encrypted:
                    if not reader.decrypt(password):
                        error = "Contraseña incorrecta o el PDF no se puede desbloquear."
                    else:
                        writer = PdfWriter()
                        for page in reader.pages:
                            writer.add_page(page)
                        unlocked_filename = f"unlocked_{uuid.uuid4().hex}.pdf"
                        unlocked_path = os.path.join('static', unlocked_filename)
                        with open(unlocked_path, "wb") as f:
                            writer.write(f)
                        unlocked_url = url_for('static', filename=unlocked_filename)
                else:
                    error = "El PDF no está protegido con contraseña."
            except Exception as e:
                error = f"Error al procesar el PDF: {e}"
    return render_template('pdf_unlock.html', unlocked_url=unlocked_url, error=error)


def try_passwords(pdf_path, wordlist_path, max_attempts=1000):
    with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
        for i, password in enumerate(f):
            if i >= max_attempts:
                return "No se encontró la contraseña en los primeros 1000 intentos"
            pwd = password.strip()
            try:
                with open(pdf_path, "rb") as file:
                    reader = PyPDF2.PdfReader(file)
                    if reader.decrypt(pwd):
                        return f"Contraseña encontrada: {pwd}"
            except Exception:
                pass
    return "Contraseña no encontrada"

@app.route("/pdf-bruteforce", methods=["POST"])
def pdf_bruteforce():
    pdf = request.files["pdf"]
    pdf_path = os.path.join("uploads", pdf.filename)
    pdf.save(pdf_path)

    # Asegúrate que esta ruta sea correcta
    wordlist_path = os.path.join("static", "rockyou.txt")

    resultado = try_passwords(pdf_path, wordlist_path)
    return resultado

@app.route('/pdf-protect', methods=['GET', 'POST'])
def pdf_protect():
    protected_url = None
    error = None
    if request.method == 'POST':
        if 'pdf_file' not in request.files or request.files['pdf_file'].filename == '':
            error = "Por favor, selecciona un archivo PDF."
        else:
            pdf_file = request.files['pdf_file']
            password = request.form.get('password', '').strip()
            if not password:
                error = "Por favor, ingresa una contraseña."
            else:
                try:
                    reader = PdfReader(pdf_file)
                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)
                    writer.encrypt(password)
                    protected_filename = f"protected_{uuid.uuid4().hex}.pdf"
                    protected_path = os.path.join('static', protected_filename)
                    with open(protected_path, "wb") as f:
                        writer.write(f)
                    protected_url = url_for('static', filename=protected_filename)
                except Exception as e:
                    error = f"Error al proteger el PDF: {e}"
    return render_template('pdf_protect.html', protected_url=protected_url, error=error)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
