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
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import io
import requests

app = Flask(__name__)
app.secret_key = 'supersecreto123'
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

# Memoria simple para el chatbot (en memoria, se borra al reiniciar)
chatbot_memory = {
    "hola": "¡Hola! ¿En qué puedo ayudarte con Multiuso?",
    "buenos días": "¡Buenos días! ¿Listo para usar alguna herramienta?",
    "buenas tardes": "¡Buenas tardes! ¿En qué puedo ayudarte hoy?",
    "buenas noches": "¡Buenas noches! ¿Necesitas algo antes de dormir?",
    "¿qué puedes hacer?": (
        "Puedo generar códigos QR, descargar videos y audios de YouTube, TikTok, Instagram y Facebook, "
        "convertir texto a voz, enviar correos electrónicos, crear memes, acortar URLs, convertir monedas, "
        "generar contraseñas seguras, desbloquear y proteger archivos PDF, hacer pronósticos deportivos y mucho más."
    ),
    "¿dónde está el link de qr?": "Puedes acceder a la herramienta de QR aquí: <a href='/qr'>Generar QR</a>",
    "¿dónde está el link de youtube mp3?": "Aquí puedes descargar audio de YouTube: <a href='/youtube-mp3'>YouTube MP3</a>",
    "¿dónde está el link de youtube mp4?": "Aquí puedes descargar video de YouTube: <a href='/youtube-mp4'>YouTube MP4</a>",
    "¿dónde está el link de tiktok?": "Descarga videos o audios de TikTok aquí: <a href='/tiktok'>TikTok</a>",
    "¿dónde está el link de meme?": "Crea memes aquí: <a href='/meme'>Meme Generator</a>",
    "¿dónde está el link de email?": "Envía correos electrónicos aquí: <a href='/email'>Email</a>",
    "¿dónde está el link de acortar url?": "Acorta tus enlaces aquí: <a href='/shortener'>Acortar URL</a>",
    "¿dónde está el link de texto a voz?": "Convierte texto a voz aquí: <a href='/tts'>Texto a Voz</a>",
    "¿dónde está el link de conversor de monedas?": "Convierte monedas aquí: <a href='/currency'>Conversor de Monedas</a>",
    "¿dónde está el link de generar contraseña?": "Genera contraseñas seguras aquí: <a href='/password'>Generar Contraseña</a>",
    "¿dónde está el link de desbloquear pdf?": "Desbloquea PDFs aquí: <a href='/pdf-unlock'>Desbloquear PDF</a>",
    "¿dónde está el link de proteger pdf?": "Protege tus PDFs aquí: <a href='/pdf-protect'>Proteger PDF</a>",
    "¿dónde está el link de instagram?": "Descarga contenido de Instagram aquí: <a href='/instagram'>Instagram</a>",
    "¿dónde está el link de facebook?": "Descarga videos de Facebook aquí: <a href='/facebook'>Facebook</a>",
    "¿dónde está el link de pronóstico?": "Haz pronósticos deportivos aquí: <a href='/pronostico'>Pronóstico Deportivo</a>",
    "¿cómo genero un código qr?": "Ve a la sección 'Generar QR', ingresa el texto o enlace y haz clic en 'Generar'.",
    "¿cómo hago un qr con logo?": "Actualmente no soporta logos, pero puedes editar la imagen generada con un editor externo.",
    "¿cómo descargo videos de youtube?": "En la sección 'YouTube MP3' o 'YouTube MP4', pega el enlace del video y elige el formato que deseas.",
    "¿cómo descargo videos de tiktok?": "En la sección 'TikTok', pega el enlace del video y elige si quieres descargar el video o solo el audio.",
    "¿cómo descargo videos de instagram?": "En la sección 'Instagram', pega el enlace y selecciona si quieres video o audio.",
    "¿cómo descargo videos de facebook?": "En la sección 'Facebook', pega el enlace y elige el formato de descarga.",
    "¿cómo convierto texto a voz?": "En la sección 'Texto a Voz', escribe el texto, selecciona el idioma y haz clic en 'Convertir'.",
    "¿cómo envío un correo electrónico?": (
        "En la sección 'Email', ingresa tu correo, contraseña, asunto, mensaje y destinatarios. Luego haz clic en 'Enviar'."
    ),
    "¿cómo hago un meme?": (
        "En la sección 'Meme', sube una imagen y escribe el texto superior e inferior. Haz clic en 'Generar meme'."
    ),
    "¿cómo acorto una url?": "En la sección 'Acortar URL', pega la dirección y haz clic en 'Acortar'.",
    "¿cómo convierto monedas?": (
        "En la sección 'Conversor de Monedas', selecciona las monedas, ingresa el monto y haz clic en 'Convertir'."
    ),
    "¿cómo genero una contraseña segura?": (
        "En la sección 'Generar Contraseña', elige la longitud y los tipos de caracteres, luego haz clic en 'Generar'."
    ),
    "¿cómo desbloqueo un pdf?": (
        "En la sección 'Desbloquear PDF', sube el archivo y escribe la contraseña si la conoces. Si no, usa la opción de fuerza bruta."
    ),
    "¿cómo protejo un pdf con contraseña?": (
        "En la sección 'Proteger PDF', sube el archivo y escribe la contraseña que deseas ponerle."
    ),
    "¿cómo hago un pronóstico deportivo?": (
        "En la sección 'Pronosticador Deportivo', selecciona la liga, los equipos y haz clic en 'Pronosticar' para ver el resultado estimado."
    ),
    "¿qué ligas puedo pronosticar?": (
        "Puedes pronosticar partidos de Premier League, La Liga, Serie A, Ligue 1, Bundesliga, Liga Colombiana A y B, Copa Libertadores, Copa Sudamericana y Champions League (solo datos disponibles)."
    ),
    "¿cómo funciona el pronosticador?": (
        "El pronosticador usa modelos de machine learning entrenados con datos históricos para estimar resultados, goles, corners y tiros."
    ),
    "¿cómo puedo cambiar el idioma del texto a voz?": (
        "En la sección 'Texto a Voz', selecciona el idioma que prefieras antes de convertir el texto."
    ),
    "¿qué pasa si olvido mi contraseña de email?": (
        "Debes recuperarla desde el proveedor de tu correo. Multiuso no almacena contraseñas."
    ),
    "¿puedo usar multiuso en el celular?": (
        "Sí, la aplicación es responsiva y funciona bien en dispositivos móviles."
    ),
    "¿cómo reporto un error?": (
        "Puedes enviar un correo al desarrollador o dejar tu comentario en la sección de contacto si está disponible."
    ),
    "gracias": "¡De nada! Si tienes otra pregunta, aquí estoy.",
    "adiós": "¡Hasta luego! Vuelve cuando quieras.",
    "bye": "¡Hasta luego! Vuelve cuando quieras.",
    "¿cómo genero un qr para wifi?": (
        "En la sección 'Generar QR', ingresa el texto con el formato de red WiFi: WIFI:S:nombre;T:WPA;P:contraseña;;"
    ),
    "¿puedo descargar solo el audio de un video?": (
        "Sí, en las secciones de YouTube, TikTok, Instagram o Facebook, selecciona la opción de audio."
    ),
    "¿qué formatos de video soporta?": (
        "Puedes descargar videos en formato MP4 y audios en MP3."
    ),
    "¿cómo elimino la contraseña de un pdf si no la sé?": (
        "Usa la opción 'Desbloquear PDF por fuerza bruta' y sube el archivo. El sistema intentará encontrar la contraseña usando un diccionario."
    ),
    "¿qué es multiuso?": (
        "Multiuso es una aplicación web que reúne varias herramientas útiles en un solo lugar: QR, descargas, memes, email, PDF, pronósticos y más."
    ),
    "¿cómo actualizo la página?": (
        "Pulsa F5 o el botón de recargar en tu navegador."
    ),
    "¿puedo usar varias funciones a la vez?": (
        "Sí, puedes usar todas las funciones de Multiuso de manera independiente."
    ),
    "¿cómo borro mi historial de chat?": (
        "Cierra la pestaña o reinicia la sesión para borrar el historial temporalmente. El bot no almacena datos personales."
    ),
    "¿cómo puedo enseñar al bot nuevas respuestas?": (
        "Si el bot no sabe una respuesta, puedes escribir: aprende:tu respuesta aquí. El bot la recordará durante la sesión."
    ),
    "¿qué pasa si cierro la página?": (
        "Se perderá el historial de chat y las respuestas aprendidas en esta sesión."
    ),
    "¿puedo descargar archivos grandes?": (
        "Depende del tamaño y la fuente. Para videos muy largos, la descarga puede tardar más o fallar."
    ),
    "¿qué hago si una descarga falla?": (
        "Verifica el enlace, tu conexión a internet y vuelve a intentarlo. Si el problema persiste, puede ser por restricciones del sitio fuente."
    ),
    "¿cómo convierto texto a voz en inglés?": (
        "En la sección 'Texto a Voz', selecciona 'en' como idioma antes de convertir el texto."
    ),
    "¿cómo hago para que el qr tenga un logo?": (
        "Actualmente la función de QR no soporta logos, pero puedes editar la imagen generada con un editor externo."
    ),
    "¿puedo compartir los memes que hago?": (
        "Sí, puedes descargar el meme generado y compartirlo en redes sociales o por mensaje."
    ),
    "¿cómo sé si el pdf está protegido?": (
        "Al intentar desbloquearlo, la app te avisará si el PDF tiene contraseña."
    ),
    "¿puedo usar multiuso gratis?": (
        "Sí, todas las funciones de Multiuso son gratuitas."
    ),
    "¿cómo contacto al soporte?": (
        "Puedes escribir al correo del desarrollador o usar la sección de contacto si está disponible."
    ),
    "¿puedo usar multiuso sin registrarme?": (
        "Sí, no necesitas registrarte para usar las funciones."
    ),
    "¿qué hago si tengo otra pregunta?": (
        "¡Solo escríbela aquí y te responderé o aprenderé la respuesta si no la sé!"
    ),
    "¿puedo hacer una tabla?": (
        "Por ahora no tengo una función de tablas, pero puedes usar Excel o Google Sheets y subir la imagen aquí para hacer un meme."
    ),
    "¿puedo convertir imágenes a pdf?": (
        "Actualmente no, pero puedes usar herramientas externas como SmallPDF o iLovePDF."
    ),
    "¿puedo traducir texto?": (
        "Por ahora no tengo traductor integrado, pero puedes usar Google Translate y luego usar mis otras funciones."
    ),
    "¿puedo personalizar los colores del qr?": (
        "Actualmente solo genero QR en blanco y negro, pero puedes editar la imagen con un editor externo."
    ),
    "¿puedo programar envíos de email?": (
        "No, los envíos son inmediatos. Si quieres programar, puedes usar servicios como Gmail o Outlook."
    ),
    "¿puedo guardar mis memes?": (
        "Sí, después de generarlos puedes descargarlos y guardarlos donde quieras."
    ),
    "¿puedo compartir el link de multiuso?": (
        "¡Por supuesto! Comparte la dirección de la web con quien quieras."
    ),
    "¿puedo usar multiuso en varios dispositivos?": (
        "Sí, puedes acceder desde cualquier dispositivo con navegador."
    ),
    "¿puedo pedir nuevas funciones?": (
        "¡Sí! Escribe tu sugerencia y la enviaré al desarrollador."
    ),
    "¿puedo borrar archivos subidos?": (
        "Los archivos se eliminan automáticamente después de un tiempo, pero puedes pedir al desarrollador que los borre antes si es urgente."
    ),
    "¿puedo usar multiuso sin internet?": (
        "No, necesitas conexión a internet para usar la aplicación."
    ),
    "¿puedo cambiar el idioma de la app?": (
        "Por ahora solo está disponible en español."
    ),
    "¿puedo hacer varias cosas a la vez?": (
        "Sí, puedes abrir varias pestañas y usar diferentes herramientas simultáneamente."
    ),
    "¿puedo usar multiuso para trabajar?": (
        "¡Claro! Multiuso es ideal para tareas rápidas y cotidianas."
    ),
    "¿puedo usar multiuso para estudiar?": (
        "Sí, puedes generar materiales, memes educativos, convertir texto a voz y más."
    ),
    "¿puedo usar multiuso para enseñar?": (
        "¡Por supuesto! Puedes crear recursos, memes, audios y compartirlos con tus estudiantes."
    ),
    "¿puedo usar multiuso para bromas?": (
        "¡Sí! Puedes crear memes y audios divertidos para compartir con tus amigos."
    ),
    "¿puedo usar multiuso para mi negocio?": (
        "Sí, puedes generar QR para promociones, acortar enlaces y más."
    ),
    "¿puedo usar multiuso para enviar archivos grandes?": (
        "No, Multiuso no es un servicio de almacenamiento ni envío de archivos grandes."
    ),
    "¿puedo usar multiuso para editar videos?": (
        "No, solo puedes descargar videos, no editarlos."
    ),
    "¿puedo usar multiuso para editar imágenes?": (
        "Solo puedes crear memes, no editar imágenes de forma avanzada."
    ),
    "¿puedo usar multiuso para hacer presentaciones?": (
        "No, pero puedes crear imágenes y memes para usarlas en tus presentaciones."
    ),
    "¿puedo usar multiuso para hacer encuestas?": (
        "No, pero puedes generar QR que lleven a formularios de Google Forms o similares."
    ),
    "¿puedo usar multiuso para hacer sorteos?": (
        "No tengo una función de sorteos, pero puedes usar generadores de números aleatorios externos."
    ),
    "¿puedo usar multiuso para hacer listas?": (
        "No tengo una función de listas, pero puedes usar la sección de texto a voz para leer tus listas."
    ),
    "¿puedo usar multiuso para hacer recordatorios?": (
        "No, Multiuso no tiene recordatorios integrados."
    ),
    "¿puedo usar multiuso para hacer calendarios?": (
        "No, pero puedes generar imágenes o QR con enlaces a calendarios de Google."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación?": (
        "Puedes generar un QR con tus datos de contacto y compartirlo como tarjeta digital."
    ),
    "¿puedo usar multiuso para hacer invitaciones?": (
        "Puedes crear un QR con el enlace a tu evento o una imagen personalizada como meme."
    ),
    "¿puedo usar multiuso para hacer stickers?": (
        "No tengo una función de stickers, pero puedes descargar tus memes y usarlos como stickers en WhatsApp."
    ),
    "¿puedo usar multiuso para hacer logos?": (
        "No, Multiuso no tiene un generador de logos."
    ),
    "¿puedo usar multiuso para hacer banners?": (
        "No, pero puedes crear memes y usarlos como banners sencillos."
    ),
    "¿puedo usar multiuso para hacer flyers?": (
        "No, pero puedes crear imágenes y compartirlas como flyers."
    ),
    "¿puedo usar multiuso para hacer posters?": (
        "No, pero puedes crear memes y usarlos como posters."
    ),
    "¿puedo usar multiuso para hacer tarjetas de cumpleaños?": (
        "Puedes crear un meme personalizado como tarjeta de cumpleaños."
    ),
    "¿puedo usar multiuso para hacer invitaciones digitales?": (
        "Sí, puedes crear un QR con el enlace a tu evento o una imagen personalizada."
    ),
    "¿puedo usar multiuso para hacer anuncios?": (
        "Puedes crear memes o imágenes y compartirlas como anuncios."
    ),
    "¿puedo usar multiuso para hacer portadas?": (
        "No, pero puedes crear memes y usarlos como portadas sencillas."
    ),
    "¿puedo usar multiuso para hacer memes animados?": (
        "No, solo puedes crear memes estáticos."
    ),
    "¿puedo usar multiuso para hacer gifs?": (
        "No, Multiuso no tiene un generador de GIFs."
    ),
    "¿puedo usar multiuso para hacer videos cortos?": (
        "No, solo puedes descargar videos, no crearlos."
    ),
    "¿puedo usar multiuso para hacer podcasts?": (
        "Puedes usar la función de texto a voz para crear audios, pero no para grabar podcasts completos."
    ),
    "¿puedo usar multiuso para hacer audiolibros?": (
        "Puedes convertir texto a voz y descargar el audio, pero no dividirlo en capítulos automáticamente."
    ),
    "¿puedo usar multiuso para hacer resúmenes?": (
        "No tengo una función de resúmenes automáticos, pero puedes copiar y pegar el texto que quieras convertir a voz."
    ),
    "¿puedo usar multiuso para hacer tareas escolares?": (
        "Puedes usar varias herramientas para ayudarte, pero recuerda hacer tus tareas tú mismo."
    ),
    "¿puedo usar multiuso para hacer tareas universitarias?": (
        "Puedes usar las herramientas para complementar tu trabajo, pero no para hacer tareas completas."
    ),
    "¿puedo usar multiuso para hacer exámenes?": (
        "No, Multiuso no tiene funciones para exámenes."
    ),
    "¿puedo usar multiuso para hacer juegos?": (
        "No, pero puedes crear memes divertidos para compartir con tus amigos."
    ),
    "¿puedo usar multiuso para hacer retos?": (
        "No, pero puedes usar la función de memes para crear imágenes de retos."
    ),
    "¿puedo usar multiuso para hacer preguntas y respuestas?": (
        "Puedes usar el chat para aprender y enseñar nuevas respuestas."
    ),
    "¿puedo usar multiuso para hacer encuestas rápidas?": (
        "No, pero puedes generar un QR que lleve a una encuesta externa."
    ),
    "¿puedo usar multiuso para hacer formularios?": (
        "No, pero puedes compartir enlaces a formularios usando QR o acortador de URL."
    ),
    "¿puedo usar multiuso para hacer listas de compras?": (
        "Puedes escribir tu lista y convertirla a audio con la función de texto a voz."
    ),
    "¿puedo usar multiuso para hacer recetas?": (
        "Puedes escribir tu receta y convertirla a audio o compartirla como imagen."
    ),
    "¿puedo usar multiuso para hacer notas de voz?": (
        "Puedes convertir texto a voz y descargar el audio."
    ),
    "¿puedo usar multiuso para hacer mensajes motivacionales?": (
        "¡Claro! Escribe tu mensaje y conviértelo en meme o audio."
    ),
    "¿puedo usar multiuso para hacer frases célebres?": (
        "Sí, puedes crear memes o audios con tus frases favoritas."
    ),
    "¿puedo usar multiuso para hacer tarjetas navideñas?": (
        "Puedes crear un meme personalizado como tarjeta navideña."
    ),
    "¿puedo usar multiuso para hacer tarjetas de amor?": (
        "Puedes crear un meme romántico o un audio con tu mensaje."
    ),
    "¿puedo usar multiuso para hacer tarjetas de agradecimiento?": (
        "Sí, crea un meme o un audio para dar las gracias."
    ),
    "¿puedo usar multiuso para hacer tarjetas de invitación?": (
        "Sí, puedes crear un QR con el enlace a tu evento o una imagen personalizada."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación digitales?": (
        "Sí, genera un QR con tus datos de contacto."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación físicas?": (
        "Puedes imprimir el QR generado y pegarlo en tu tarjeta física."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación animadas?": (
        "No, solo puedes generar QR estáticos."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con foto?": (
        "No, pero puedes agregar tu foto a un meme y compartirlo."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con logo?": (
        "No, pero puedes agregar tu logo a un meme y compartirlo."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con QR?": (
        "¡Sí! Esa es una de las funciones principales."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con enlace?": (
        "Sí, puedes generar un QR con el enlace a tu web o perfil."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con redes sociales?": (
        "Sí, puedes generar un QR con el enlace a tus redes sociales."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con número de teléfono?": (
        "Sí, puedes generar un QR con tu número de teléfono."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con dirección?": (
        "Sí, puedes generar un QR con tu dirección."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con email?": (
        "Sí, puedes generar un QR con tu correo electrónico."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con vcard?": (
        "Sí, puedes generar un QR con formato vCard."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con texto personalizado?": (
        "Sí, puedes generar un QR con cualquier texto que desees."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con código de barras?": (
        "No, solo genero códigos QR."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con NFC?": (
        "No, Multiuso no soporta NFC."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con audio?": (
        "Puedes generar un audio con tu presentación usando la función de texto a voz."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con video?": (
        "No, solo puedes generar QR y memes."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con animaciones?": (
        "No, solo puedes generar QR y memes estáticos."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con efectos especiales?": (
        "No, solo puedes generar QR y memes sencillos."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con fondo personalizado?": (
        "No, pero puedes editar la imagen generada con un editor externo."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con colores personalizados?": (
        "No, solo genero QR en blanco y negro."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con tipografía personalizada?": (
        "No, la tipografía es estándar."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con diseño profesional?": (
        "No, pero puedes usar la herramienta para crear una base y luego mejorarla con un diseñador."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con plantilla?": (
        "No, pero puedes crear tu propio diseño usando memes."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato PDF?": (
        "Puedes descargar la imagen y convertirla a PDF con otra herramienta."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato imagen?": (
        "Sí, puedes descargar el QR o meme como imagen."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital?": (
        "Sí, puedes compartir el QR o meme digitalmente."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato físico?": (
        "Sí, puedes imprimir el QR o meme generado."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato web?": (
        "Puedes generar un QR con el enlace a tu web."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato móvil?": (
        "Sí, la aplicación es responsiva y funciona en móviles."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato social?": (
        "Sí, puedes compartir el QR o meme en redes sociales."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato empresarial?": (
        "Sí, puedes personalizar el texto del QR para tu empresa."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato personal?": (
        "Sí, puedes personalizar el texto del QR para ti."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato familiar?": (
        "Sí, puedes personalizar el texto del QR para tu familia."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato escolar?": (
        "Sí, puedes personalizar el texto del QR para tu escuela."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato universitario?": (
        "Sí, puedes personalizar el texto del QR para tu universidad."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato institucional?": (
        "Sí, puedes personalizar el texto del QR para tu institución."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato profesional?": (
        "Sí, puedes personalizar el texto del QR para tu profesión."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato creativo?": (
        "Sí, puedes personalizar el texto del QR de forma creativa."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato innovador?": (
        "Sí, puedes experimentar con los textos y memes."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato divertido?": (
        "¡Sí! Usa memes y textos originales."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato elegante?": (
        "Puedes usar textos formales y descargar el QR en alta calidad."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato sencillo?": (
        "Sí, la herramienta es fácil de usar y los resultados son simples y efectivos."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato rápido?": (
        "Sí, puedes generar tu QR o meme en segundos."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato gratuito?": (
        "¡Sí! Todas las funciones de Multiuso son gratis."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato ilimitado?": (
        "Sí, puedes generar tantas como quieras."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato seguro?": (
        "Sí, tus datos no se almacenan y los archivos se eliminan periódicamente."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato privado?": (
        "Sí, solo tú tienes acceso a los archivos que generas."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato confidencial?": (
        "Sí, tus datos no se comparten con terceros."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato personalizado?": (
        "Sí, puedes escribir el texto que desees en el QR."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato editable?": (
        "Puedes editar el texto antes de generar el QR."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato exportable?": (
        "Sí, puedes descargar la imagen y usarla donde quieras."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato imprimible?": (
        "Sí, puedes imprimir la imagen generada."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato compartible?": (
        "Sí, puedes compartir la imagen o el enlace generado."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato accesible?": (
        "Sí, la aplicación es accesible desde cualquier dispositivo."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato universal?": (
        "Sí, puedes usarla desde cualquier parte del mundo."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital avanzado?": (
        "Puedes experimentar con los textos y QR para lograr resultados únicos."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital básico?": (
        "Sí, la herramienta es sencilla y directa."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital profesional?": (
        "Puedes personalizar el texto para tu empresa o profesión."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital creativo?": (
        "¡Sí! Usa textos originales y memes para destacar."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital divertido?": (
        "¡Sí! Usa memes y textos graciosos."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital elegante?": (
        "Puedes usar textos formales y descargar el QR en alta calidad."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital sencillo?": (
        "Sí, la herramienta es fácil de usar y los resultados son simples y efectivos."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital rápido?": (
        "Sí, puedes generar tu QR o meme en segundos."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital gratuito?": (
        "¡Sí! Todas las funciones de Multiuso son gratis."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital ilimitado?": (
        "Sí, puedes generar tantas como quieras."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital seguro?": (
        "Sí, tus datos no se almacenan y los archivos se eliminan periódicamente."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital privado?": (
        "Sí, solo tú tienes acceso a los archivos que generas."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital confidencial?": (
        "Sí, tus datos no se comparten con terceros."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital personalizado?": (
        "Sí, puedes escribir el texto que desees en el QR."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital editable?": (
        "Puedes editar el texto antes de generar el QR."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital exportable?": (
        "Sí, puedes descargar la imagen y usarla donde quieras."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital imprimible?": (
        "Sí, puedes imprimir la imagen generada."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital compartible?": (
        "Sí, puedes compartir la imagen o el enlace generado."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital accesible?": (
        "Sí, la aplicación es accesible desde cualquier dispositivo."
    ),
    "¿puedo usar multiuso para hacer tarjetas de presentación con formato digital universal?": (
        "Sí, puedes usarla desde cualquier parte del mundo."
    ),
    # Puedes seguir agregando más preguntas y respuestas imaginativas aquí...
}

import unicodedata
from markupsafe import Markup

# Diccionario de links de funciones
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

def normalizar(texto):
    # Quita tildes y pasa a minúsculas
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )

def buscar_respuesta(mensaje):
    mensaje_norm = normalizar(mensaje)
    for pregunta in chatbot_memory:
        if normalizar(pregunta) in mensaje_norm or mensaje_norm in normalizar(pregunta):
            return chatbot_memory[pregunta]
    return None

def buscar_link(mensaje):
    mensaje_norm = normalizar(mensaje)
    for key, link in chatbot_links.items():
        if key in mensaje_norm:
            return link, key
    return None, None

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if 'chat_history' not in session:
        session['chat_history'] = []
    if 'ultima_pregunta' not in session:
        session['ultima_pregunta'] = None
    respuesta = ""
    if request.method == 'POST':
        mensaje = request.form.get('mensaje', '').strip()
        session['chat_history'].append(("Tú", mensaje))
        mensaje_norm = normalizar(mensaje)

        # Aprendizaje
        if mensaje_norm.startswith("aprende:"):
            partes = mensaje.split(":", 1)
            if len(partes) == 2 and session.get('ultima_pregunta'):
                pregunta = session['ultima_pregunta']
                chatbot_memory[pregunta] = partes[1].strip()
                respuesta = f"He aprendido que '{pregunta}' se responde: {partes[1].strip()}"
            else:
                respuesta = "Primero hazme una pregunta, luego enséñame la respuesta usando: aprende:tu respuesta aquí"
        else:
            # Buscar link si pregunta por link
            if "link" in mensaje_norm or "enlace" in mensaje_norm or "ir a" in mensaje_norm:
                link, nombre = buscar_link(mensaje)
                if link:
                    respuesta = Markup(f"Puedes acceder a <b>{nombre.title()}</b> aquí: <a href='{link}'>Ir a {nombre.title()}</a>")
                else:
                    respuesta = "No encontré el link que buscas. ¿Puedes especificar mejor la función?"
            else:
                # Buscar respuesta flexible
                respuesta_encontrada = buscar_respuesta(mensaje)
                if respuesta_encontrada:
                    respuesta = respuesta_encontrada
                else:
                    respuesta = "No sé la respuesta. ¿Quieres enseñarme? Escribe: aprende:tu respuesta aquí"
            # Guarda la última pregunta para aprendizaje
            session['ultima_pregunta'] = mensaje
        session['chat_history'].append(("Bot", respuesta))
    return render_template('chatbot.html', chat_history=session['chat_history'])
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
