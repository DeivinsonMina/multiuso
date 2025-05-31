from flask import Flask, render_template, request, url_for, redirect, send_file, session
import os
import secrets
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
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import io
import requests
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.debug = True
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


@app.route('/pdf-bruteforce', methods=['GET', 'POST'])
def pdf_bruteforce():
    unlocked_url = None
    error = None
    found_password = None
    # Ruta al diccionario en static
    wordlist_path = os.path.join('static', 'rockyou.txt')
    if request.method == 'POST':
        pdf_file = request.files.get('pdf_file')
        if not pdf_file or pdf_file.filename == '':
            error = "Por favor, selecciona un archivo PDF."
        elif not os.path.exists(wordlist_path):
            error = "No se encontró el diccionario de contraseñas en static/rockyou.txt."
        else:
            try:
                reader = PdfReader(pdf_file)
                if not reader.is_encrypted:
                    error = "El PDF no está protegido con contraseña."
                else:
                    with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                        passwords = [line.strip() for line in f if line.strip()]
                    for pwd in passwords:
                        if reader.decrypt(pwd):
                            found_password = pwd
                            writer = PdfWriter()
                            for page in reader.pages:
                                writer.add_page(page)
                            unlocked_filename = f"unlocked_{uuid.uuid4().hex}.pdf"
                            unlocked_path = os.path.join('static', unlocked_filename)
                            with open(unlocked_path, "wb") as f_out:
                                writer.write(f_out)
                            unlocked_url = url_for('static', filename=unlocked_filename)
                            break
                    if not found_password:
                        error = "No se encontró la contraseña en el diccionario."
            except Exception as e:
                error = f"Error al procesar el PDF: {e}"
    return render_template('pdf_bruteforce.html', unlocked_url=unlocked_url, error=error, found_password=found_password)

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
@app.route('/instagram', methods=['GET', 'POST'])
def instagram():
    filename = None
    error = None
    if request.method == 'POST':
        url = request.form['url']
        tipo = request.form.get('tipo', 'video')  # 'video' o 'audio'
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = clean_filename(info['title'])
            output_template = os.path.join('static', f'{title}.%(ext)s')
            if tipo == 'audio':
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
            if not os.path.exists(file_path):
                error = "No se pudo descargar el archivo."
        except Exception as e:
            error = f"Error: {e}"
    return render_template('instagram.html', filename=filename, error=error)

@app.route('/facebook', methods=['GET', 'POST'])
def facebook():
    filename = None
    error = None
    if request.method == 'POST':
        url = request.form['url']
        tipo = request.form.get('tipo', 'video')
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = clean_filename(info['title'])
            output_template = os.path.join('static', f'{title}.%(ext)s')
            if tipo == 'audio':
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
            if not os.path.exists(file_path):
                error = "No se pudo descargar el archivo."
        except Exception as e:
            error = f"Error: {e}"
    return render_template('facebook.html', filename=filename, error=error)



LIGAS = {
    "Premier League (Inglaterra)": {
        "url": "https://www.football-data.co.uk/mmz4281/2324/E0.csv",
        "local": "static/datos/E0.csv"
    },
    "La Liga (España)": {
        "url": "https://www.football-data.co.uk/mmz4281/2324/SP1.csv",
        "local": "static/datos/SP1.csv"
    },
    "Serie A (Italia)": {
        "url": "https://www.football-data.co.uk/mmz4281/2324/I1.csv",
        "local": "static/datos/I1.csv"
    },
    "Ligue 1 (Francia)": {
        "url": "https://www.football-data.co.uk/mmz4281/2324/F1.csv",
        "local": "static/datos/F1.csv"
    },
    "Bundesliga (Alemania)": {
        "url": "https://www.football-data.co.uk/mmz4281/2324/D1.csv",
        "local": "static/datos/D1.csv"
    },
    "Champions League": {
        "url": "https://www.football-data.co.uk/mmz4281/2324/E1.csv",
        "local": "static/datos/E1.csv"
    }
}

def cargar_modelo(liga_info):
    import os
    os.makedirs(os.path.dirname(liga_info["local"]), exist_ok=True)
    try:
        df = pd.read_csv(liga_info["local"])
    except Exception:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(liga_info["url"], headers=headers, timeout=10)
            r.raise_for_status()
            with open(liga_info["local"], "wb") as f:
                f.write(r.content)
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        except Exception as e:
            raise Exception(f"No se pudo obtener los datos: {e}")

    # Usar solo partidos jugados y columnas disponibles
    columnas = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'HS', 'AS', 'HC', 'AC', 'HST', 'AST']
    columnas_existentes = [col for col in columnas if col in df.columns]
    df = df[columnas_existentes].dropna()
    equipos = pd.concat([df['HomeTeam'], df['AwayTeam']]).unique()
    equipo2id = {e: i for i, e in enumerate(equipos)}
    df['local_id'] = df['HomeTeam'].map(equipo2id)
    df['visitante_id'] = df['AwayTeam'].map(equipo2id)
    X = df[['local_id', 'visitante_id']]

    # Modelos
    modelo_resultado = RandomForestClassifier(n_estimators=200, random_state=42)
    modelo_resultado.fit(X, df['FTR'])
    precision = modelo_resultado.score(X, df['FTR'])

    modelo_goles_local = RandomForestClassifier(n_estimators=150, random_state=42)
    modelo_goles_local.fit(X, df['FTHG'])

    modelo_goles_visitante = RandomForestClassifier(n_estimators=150, random_state=42)
    modelo_goles_visitante.fit(X, df['FTAG'])

    modelo_corners_local = modelo_corners_visitante = None
    if 'HC' in df and 'AC' in df:
        modelo_corners_local = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo_corners_local.fit(X, df['HC'])
        modelo_corners_visitante = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo_corners_visitante.fit(X, df['AC'])

    modelo_shots_local = modelo_shots_visitante = None
    if 'HS' in df and 'AS' in df:
        modelo_shots_local = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo_shots_local.fit(X, df['HS'])
        modelo_shots_visitante = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo_shots_visitante.fit(X, df['AS'])

    modelo_shots_on_target_local = modelo_shots_on_target_visitante = None
    if 'HST' in df and 'AST' in df:
        modelo_shots_on_target_local = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo_shots_on_target_local.fit(X, df['HST'])
        modelo_shots_on_target_visitante = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo_shots_on_target_visitante.fit(X, df['AST'])

    return (
        modelo_resultado, modelo_goles_local, modelo_goles_visitante,
        modelo_corners_local, modelo_corners_visitante,
        modelo_shots_local, modelo_shots_visitante,
        modelo_shots_on_target_local, modelo_shots_on_target_visitante,
        equipo2id, equipos, precision
    )

# En tu ruta pronostico, usa así:
@app.route('/pronostico', methods=['GET', 'POST'])
def pronostico():
    resultado = None
    goles = None
    corners = None
    tiros = None
    tiros_puerta = None
    probabilidad = None
    precision = None
    error = None
    equipos_lista = []
    liga_seleccionada = request.form.get('liga') if request.method == 'POST' else None

    if liga_seleccionada and liga_seleccionada in LIGAS:
        liga_info = LIGAS[liga_seleccionada]
        try:
            (modelo_resultado, modelo_goles_local, modelo_goles_visitante,
             modelo_corners_local, modelo_corners_visitante,
             modelo_shots_local, modelo_shots_visitante,
             modelo_shots_on_target_local, modelo_shots_on_target_visitante,
             equipo2id, equipos, precision) = cargar_modelo(liga_info)
            equipos_lista = sorted(list(equipo2id.keys()))
        except Exception as e:
            error = f"Error cargando datos de la liga: {e}"
    else:
        equipos_lista = []

    if request.method == 'POST' and not error and equipos_lista:
        local = request.form.get('local')
        visitante = request.form.get('visitante')
        if not local or not visitante:
            error = "Selecciona ambos equipos."
        elif local == visitante:
            error = "Elige equipos diferentes."
        else:
            try:
                entrada = [[equipo2id[local], equipo2id[visitante]]]
                pred_resultado = modelo_resultado.predict(entrada)[0]
                proba = modelo_resultado.predict_proba(entrada)[0]
                clases = modelo_resultado.classes_
                proba_dict = {clase: round(100*p,2) for clase, p in zip(clases, proba)}
                probabilidad = f"Probabilidades: Local {proba_dict.get('H',0)}% | Empate {proba_dict.get('D',0)}% | Visitante {proba_dict.get('A',0)}%"
                pred_goles_local = modelo_goles_local.predict(entrada)[0]
                pred_goles_visitante = modelo_goles_visitante.predict(entrada)[0]
                resultado = {
                    'H': f"Gana {local}",
                    'A': f"Gana {visitante}",
                    'D': "Empate"
                }.get(pred_resultado, "Empate")
                goles = f"{local} {pred_goles_local} - {pred_goles_visitante} {visitante}"

                # Corners
                if modelo_corners_local and modelo_corners_visitante:
                    pred_corners_local = modelo_corners_local.predict(entrada)[0]
                    pred_corners_visitante = modelo_corners_visitante.predict(entrada)[0]
                    corners = f"Corners: {local} {pred_corners_local} - {pred_corners_visitante} {visitante}"

                # Tiros totales
                if modelo_shots_local and modelo_shots_visitante:
                    pred_shots_local = modelo_shots_local.predict(entrada)[0]
                    pred_shots_visitante = modelo_shots_visitante.predict(entrada)[0]
                    tiros = f"Tiros totales: {local} {pred_shots_local} - {pred_shots_visitante} {visitante}"

                # Tiros a puerta
                if modelo_shots_on_target_local and modelo_shots_on_target_visitante:
                    pred_shots_on_target_local = modelo_shots_on_target_local.predict(entrada)[0]
                    pred_shots_on_target_visitante = modelo_shots_on_target_visitante.predict(entrada)[0]
                    tiros_puerta = f"Tiros a puerta: {local} {pred_shots_on_target_local} - {pred_shots_on_target_visitante} {visitante}"

            except Exception as e:
                error = f"Error: {e}"

    return render_template(
        'pronostico.html',
        ligas=LIGAS.keys(),
        liga_seleccionada=liga_seleccionada,
        equipos=equipos_lista,
        resultado=resultado,
        goles=goles,
        corners=corners,
        tiros=tiros,
        tiros_puerta=tiros_puerta,
        probabilidad=probabilidad,
        precision=precision,
        error=error
    )

from flask import session
import mysql.connector
import re
import unicodedata
from markupsafe import Markup
import openai
import difflib
# Configura tu API Key de OpenAI
# Cargar variables de entorno desde .env


# Configura tu API Key de OpenAI de forma segura
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- FUNCIÓN PARA NORMALIZAR TEXTO ---
def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )

# --- FUNCIÓN PARA OBTENER RESPUESTA DE OPENAI ---
def obtener_respuesta_openai(mensaje):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente útil."},
                {"role": "user", "content": mensaje}
            ],
            max_tokens=150,
            temperature=0.7,
            n=1
        )
        if response.choices and response.choices[0].message:
            return response.choices[0].message['content'].strip()
        else:
            return "Lo siento, no pude generar una respuesta válida."
    except Exception as e:
        print("Error al llamar a OpenAI:", e)
        return "Lo siento, tuve un problema al procesar tu solicitud."

# --- CONEXIÓN Y FUNCIONES MYSQL ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def guardar_respuesta_db(pregunta, respuesta):
    if respuesta:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO chatbot_respuestas (pregunta, respuesta) VALUES (%s, %s)",
            (pregunta, respuesta)
        )
        conn.commit()
        cur.close()
        conn.close()

def cargar_respuestas_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT pregunta, respuesta FROM chatbot_respuestas")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return {preg: resp for preg, resp in data}

def guardar_historial_db(usuario, mensaje, respuesta):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chatbot_historial (usuario, mensaje, respuesta) VALUES (%s, %s, %s)",
        (usuario, mensaje, respuesta)
    )
    conn.commit()
    cur.close()
    conn.close()

# --- MEMORIA EN RAM Y CARGA DESDE MYSQL ---
chatbot_memory = {
    "hola": "¡Hola! ¿En qué puedo ayudarte con Multiuso?"
}
try:
    chatbot_memory.update(cargar_respuestas_db())
except Exception as e:
    print("No se pudo cargar la base de datos:", e)

# --- ENLACES ---
chatbot_links = {
    "qr": "/qr",
    "youtube mp3": "/youtube-mp3",
    "youtube mp4": "/youtube-mp4",
    "tiktok": "/tiktok",
    "meme": "/meme",
    "email": "/email",
    "acortar url": "/shortener",
    "texto a voz": "/tts",
    "conversor de monedas": "/currency",
    "generar contraseña": "/password",
    "desbloquear pdf": "/pdf-unlock",
    "proteger pdf": "/pdf-protect",
    "instagram": "/instagram",
    "facebook": "/facebook",
    "pronóstico": "/pronostico"
}

# --- FUNCIONES DE RESPUESTA ---
def buscar_respuesta(mensaje, umbral=0.6):
    mensaje_norm = normalizar(mensaje)
    preguntas = list(chatbot_memory.keys())
    coincidencias = difflib.get_close_matches(mensaje_norm, preguntas, n=1, cutoff=umbral)
    if coincidencias:
        return chatbot_memory[coincidencias[0]]
    return None

def buscar_link(mensaje):
    mensaje_norm = normalizar(mensaje)
    for key, link in chatbot_links.items():
        if key in mensaje_norm:
            return link, key
    return None, None

def resolver_operacion(mensaje):
    match = re.match(r'^\s*(\d+)\s*([\+\-\*/])\s*(\d+)\s*$', mensaje)
    if match:
        a, op, b = match.groups()
        a, b = int(a), int(b)
        if op == '+': return f"{a} + {b} = {a + b}"
        if op == '-': return f"{a} - {b} = {a - b}"
        if op == '*': return f"{a} * {b} = {a * b}"
        if op == '/': return f"{a} / {b} = {a / b if b != 0 else 'indefinido'}"
    return None

# --- RUTA DEL CHATBOT COMPLETA Y MEJORADA ---

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if 'chat_history' not in session:
        session['chat_history'] = []
    if 'ultima_pregunta' not in session:
        session['ultima_pregunta'] = None
    if 'esperando_respuesta' not in session:
        session['esperando_respuesta'] = False
    if 'ultima_no_sabida' not in session:
        session['ultima_no_sabida'] = None

    respuesta = ""

    if request.method == 'POST':
        mensaje = request.form.get('mensaje', '').strip()
        session['chat_history'].append(("Tú", mensaje))
        mensaje_norm = normalizar(mensaje)

        # --- Modo aprendizaje ---
        if session.get('esperando_respuesta') and not mensaje.endswith("?"):
            pregunta = session.get('ultima_pregunta')
            if pregunta:
                if len(mensaje.strip()) < 3:
                    respuesta = "La respuesta es muy corta. Por favor, proporciona una respuesta más completa."
                else:
                    pregunta_norm = normalizar(pregunta)
                    chatbot_memory[pregunta_norm] = mensaje.strip()
                    guardar_respuesta_db(pregunta_norm, mensaje.strip())
                    respuesta = f"He aprendido que '{pregunta}' se responde: {mensaje.strip()}"
                    session['esperando_respuesta'] = False
                    session['ultima_no_sabida'] = None
            else:
                respuesta = "No tengo ninguna pregunta pendiente para aprender."

        elif mensaje_norm.startswith("aprende:"):
            partes = mensaje.split(":", 1)
            if len(partes) == 2 and session.get('ultima_pregunta'):
                pregunta = session['ultima_pregunta']
                if len(partes[1].strip()) < 3:
                    respuesta = "La respuesta es muy corta. Por favor, proporciona una respuesta más completa."
                else:
                    pregunta_norm = normalizar(pregunta)
                    chatbot_memory[pregunta_norm] = partes[1].strip()
                    guardar_respuesta_db(pregunta_norm, partes[1].strip())
                    respuesta = f"He aprendido que '{pregunta}' se responde: {partes[1].strip()}"
                    session['esperando_respuesta'] = False
                    session['ultima_no_sabida'] = None
            else:
                respuesta = "Primero hazme una pregunta, luego enséñame la respuesta usando: aprende:tu respuesta aquí"

        # --- Operaciones matemáticas ---
        else:
            operacion = resolver_operacion(mensaje_norm)
            if operacion:
                respuesta = operacion
                session['esperando_respuesta'] = False
                session['ultima_no_sabida'] = None

            # --- Buscar enlaces ---
            elif any(x in mensaje_norm for x in ["link", "enlace", "ir a"]):
                link, nombre = buscar_link(mensaje)
                if link:
                    respuesta = Markup(f"Puedes acceder a <b>{nombre.title()}</b> aquí: <a href='{link}'>Ir a {nombre.title()}</a>")
                else:
                    respuesta = "No encontré el link que buscas. ¿Puedes especificar mejor la función?"
                session['esperando_respuesta'] = False
                session['ultima_no_sabida'] = None

            # --- Respuesta basada en memoria o IA ---
            else:
                respuesta_encontrada = buscar_respuesta(mensaje)
                if respuesta_encontrada:
                    respuesta = respuesta_encontrada
                    session['esperando_respuesta'] = False
                    session['ultima_no_sabida'] = None
                else:
                    pregunta_norm = normalizar(mensaje)
                    if session.get('ultima_no_sabida') != pregunta_norm:
                        session['ultima_pregunta'] = mensaje
                        respuesta = obtener_respuesta_openai(mensaje)

                        if respuesta and not respuesta.lower().startswith("lo siento"):
                            chatbot_memory[pregunta_norm] = respuesta
                            guardar_respuesta_db(pregunta_norm, respuesta)
                            session['esperando_respuesta'] = False
                            session['ultima_no_sabida'] = None
                        else:
                            respuesta = "No tengo una respuesta en este momento. ¿Quieres enseñármela tú?"
                            session['esperando_respuesta'] = True
                            session['ultima_no_sabida'] = pregunta_norm
                    else:
                        respuesta = "Sigo sin saber la respuesta. Puedes enseñármela escribiéndola o usando: aprende:respuesta"

        # --- Guardar historial y mostrar ---
        session['chat_history'].append(("Bot", respuesta))
        guardar_historial_db("usuario", mensaje, respuesta)

    return render_template('chatbot.html', chat_history=session['chat_history'])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
