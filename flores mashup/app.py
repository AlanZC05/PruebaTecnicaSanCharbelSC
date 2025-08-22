import os
import re
import requests
import mysql.connector
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, session, flash, g
)
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import wikipediaapi
from unidecode import unidecode
from functools import wraps


load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")


app.secret_key = os.getenv("SECRET_KEY", "mondongo")
app.permanent_session_lifetime = timedelta(days=7)

bcrypt = Bcrypt(app)


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "bloomhub"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "auth_plugin": os.getenv("DB_AUTH_PLUGIN", "mysql_native_password")
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    """
    Crea la tabla de usuarios si no existe.
    Puedes ejecutar esto al arrancar el servidor si quieres.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(120) NOT NULL,
            correo VARCHAR(190) NOT NULL UNIQUE,
            contrasena VARCHAR(255) NOT NULL,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()
    cur.close()
    conn.close()

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped

wiki_wiki = wikipediaapi.Wikipedia(
    language='es',
    user_agent='BloomHub/3.0',
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

APIS = {
    'perenual': {
        'key': os.getenv('PERENUAL_API_KEY', ''),
        'url': 'https://perenual.com/api/species-list',
        'params': {
            'edible': False,
            'indoor': False,
            'page': 1
        }
    },
    'pixabay': {
        'key': os.getenv('PIXABAY_API_KEY', ''),
        'url': 'https://pixabay.com/api/',
        'params': {
            'image_type': 'photo',
            'category': 'nature',
            'safesearch': 'true',
            'per_page': 3
        }
    },
    'unsplash': {
        'key': os.getenv('UNSPLASH_API_KEY', ''),
        'url': 'https://api.unsplash.com/search/photos',
        'params': {
            'content_filter': 'high',
            'per_page': 3
        }
    }
}

FLOWER_KEYWORDS = {
    'rosa', 'rosas', 'rose', 'roses',
    'tulipán', 'tulipanes', 'tulip', 'tulips',
    'girasol', 'girasoles', 'sunflower', 'sunflowers',
    'orquídea', 'orquídeas', 'orchid', 'orchids',
    'margarita', 'margaritas', 'daisy', 'daisies',
    'lirio', 'lirios', 'lily', 'lilies',
    'clavel', 'claveles', 'carnation', 'carnations',
    'hortensia', 'hortensias', 'hydrangea', 'hydrangeas',
    'jazmín', 'jazmines', 'jasmine',
    'lavanda', 'lavandas', 'lavender',
    'amapola', 'amapolas', 'poppy', 'poppies',
    'peonía', 'peonías', 'peony', 'peonies',
    'dalia', 'dalias', 'dahlia', 'dahlias',
    'crisantemo', 'crisantemos', 'chrysanthemum', 'chrysanthemums',
    'narciso', 'narcisos', 'daffodil', 'daffodils',
    'buganvilla', 'buganvillas', 'bougainvillea',
    'hibisco', 'hibiscos', 'hibiscus',
    'pensamiento', 'pensamientos', 'pansy',
    'geranio', 'geranios', 'geranium',
    'azucena', 'azucenas',
    'petunia', 'petunias',
    'gladiolo', 'gladiolos', 'gladiolus',
    'nardo', 'nardos',
    'alhelí', 'alhelíes',
    'violeta', 'violetas', 'violet',
    'caléndula', 'caléndulas', 'marigold',
    'dedalera', 'dedaleras', 'foxglove',
    'lupino', 'lupinos', 'lupine',
    'malva', 'malvas', 'mallow',
    'nomeolvides', 'forget-me-not',
    'primavera', 'primrose',
    'rododendro', 'rododendros', 'rhododendron',
    'verbena', 'verbenas',
    'zinnia', 'zinnias',
    'anémona', 'anémonas', 'anemone',
    'campanilla', 'campanillas', 'bluebell',
    'diente de león', 'dandelion',
    'jazmín estrella', 'star jasmine',
    'flor de nochebuena', 'poinsettia',
    'flor de cempasúchil', 'marigold',
    'flor de loto', 'lotus flower',
    'alcatraz', 'cala'
}

SCIENTIFIC_NAMES = {
    'jazmín': 'Jasminum officinale',
    'jasmine': 'Jasminum officinale',
    'jazmín estrella': 'Trachelospermum jasminoides',
    'rosa': 'Rosa',
    'tulipán': 'Tulipa',
    'girasol': 'Helianthus annuus',
    'orquídea': 'Orchidaceae',
    'margarita': 'Bellis perennis',
    'lirio': 'Lilium',
    'clavel': 'Dianthus caryophyllus',
    'hortensia': 'Hydrangea',
    'lavanda': 'Lavandula',
    'amapola': 'Papaver',
    'peonía': 'Paeonia',
    'dalia': 'Dahlia',
    'crisantemo': 'Chrysanthemum',
    'narciso': 'Narcissus',
    'buganvilla': 'Bougainvillea',
    'hibisco': 'Hibiscus',
    'pensamiento': 'Viola tricolor',
    'geranio': 'Pelargonium',
    'azucena': 'Lilium candidum',
    'petunia': 'Petunia',
    'gladiolo': 'Gladiolus',
    'nardo': 'Polianthes tuberosa',
    'alhelí': 'Matthiola incana',
    'violeta': 'Viola',
    'caléndula': 'Calendula officinalis',
    'dedalera': 'Digitalis purpurea',
    'lupino': 'Lupinus',
    'malva': 'Malva sylvestris',
    'nomeolvides': 'Myosotis',
    'primavera': 'Primula vulgaris',
    'rododendro': 'Rhododendron',
    'verbena': 'Verbena officinalis',
    'zinnia': 'Zinnia elegans',
    'anémona': 'Anemone',
    'campanilla': 'Campanula',
    'diente de león': 'Taraxacum officinale',
    'flor de nochebuena': 'Euphorbia pulcherrima',
    'flor de cempasúchil': 'Tagetes erecta',
    'flor de loto': 'Nelumbo nucifera',
    'alcatraz': 'Zantedeschia aethiopica',
    'cala': 'Zantedeschia aethiopica'
}

FLOWER_SYNONYMS = {
    'jazmines': 'jazmín',
    'jazmin': 'jazmín',
    'jasmines': 'jasmine',
    'rosas': 'rosa',
    'tulipanes': 'tulipán',
    'orquideas': 'orquídea',
    'margaritas': 'margarita',
    'lirios': 'lirio',
    'claveles': 'clavel',
    'hortensias': 'hortensia',
    'lavandas': 'lavanda',
    'amapolas': 'amapola',
    'peonias': 'peonía',
    'dalias': 'dalia',
    'crisantemos': 'crisantemo',
    'narcisos': 'narciso',
    'buganvillas': 'buganvilla',
    'hibiscos': 'hibisco',
    'pensamientos': 'pensamiento',
    'geranios': 'geranio',
    'azucenas': 'azucena',
    'petunias': 'petunia',
    'gladiolos': 'gladiolo',
    'nardos': 'nardo',
    'alhelies': 'alhelí',
    'violetas': 'violeta',
    'calendulas': 'caléndula',
    'dedaleras': 'dedalera',
    'lupinos': 'lupino',
    'malvas': 'malva',
    'nomeolvides': 'nomeolvides',
    'primulas': 'primavera',
    'rododendros': 'rododendro',
    'verbenas': 'verbena',
    'zinnias': 'zinnia',
    'anemonas': 'anémona',
    'campanillas': 'campanilla',
    'dientes de leon': 'diente de león',
    'cala': 'alcatraz'
}

def normalize_flower_name(name):
    if not name:
        return None

    normalized = unidecode(name.lower().strip())

    if normalized.endswith('es'):
        normalized = normalized[:-2]
    elif normalized.endswith('s'):
        normalized = normalized[:-1]

    return FLOWER_SYNONYMS.get(normalized, normalized)

def is_flower_related(text):
    if not text:
        return False

    normalized = normalize_flower_name(text)

    if any(
        keyword == normalized or
        normalized in keyword or
        keyword in normalized
        for keyword in FLOWER_KEYWORDS
    ):
        return True

    
    patterns = [
        r'jazm[ií]n', r'jasmine', r'rose', r'rosa',
        r'orqu[ií]dea', r'orchid', r'tulip', r'tulip[aá]n',
        r'flor', r'flower', r'blossom', r'bloom',
        r'girasol', r'sunflower', r'dalia', r'hibisco',
        r'peon[ií]a', r'azucena', r'alcatraz', r'cala'
    ]

    return any(re.search(pattern, normalized) for pattern in patterns)

def get_scientific_name(common_name):
    
    normalized = normalize_flower_name(common_name)
    return SCIENTIFIC_NAMES.get(normalized, common_name)


def get_perenual_data(query):

    try:
        params = {
            'key': APIS['perenual']['key'],
            'q': query,
            **APIS['perenual']['params']
        }

        response = requests.get(
            APIS['perenual']['url'],
            params=params,
            timeout=15
        )

        if response.status_code == 429:
            app.logger.warning("Límite de solicitudes excedido en Perenual API")
            return None
        if response.status_code == 401:
            app.logger.error("Clave API de Perenual no válida")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('data'):
            for plant in data['data']:
                common_name = (plant.get('common_name') or '').lower()
                if is_flower_related(common_name):
                    return {
                        'name': plant.get('common_name'),
                        'scientific_name': (plant.get('scientific_name') or [None])[0] if isinstance(plant.get('scientific_name'), list) else plant.get('scientific_name'),
                        'watering': plant.get('watering'),
                        'sunlight': plant.get('sunlight'),
                        'care_level': plant.get('care_level'),
                        'cycle': plant.get('cycle'),
                        'description': plant.get('description', ''),
                        'growth_rate': plant.get('growth_rate'),
                        'hardiness': plant.get('hardiness'),
                        'flowers': plant.get('flowers'),
                        'foliage': plant.get('foliage')
                    }
        return None
    except Exception as e:
        app.logger.error(f"Error en Perenual API: {str(e)}")
        return None

def get_pixabay_images(query):
    """Obtiene imágenes de flores de Pixabay"""
    try:
        params = {
            'key': APIS['pixabay']['key'],
            'q': f"{query} flower",
            **APIS['pixabay']['params']
        }

        response = requests.get(
            APIS['pixabay']['url'],
            params=params,
            timeout=10
        )

        if response.status_code == 429:
            app.logger.warning("Límite de solicitudes excedido en Pixabay")
            return []

        response.raise_for_status()
        data = response.json()

        return [img.get('webformatURL') for img in data.get('hits', []) if img.get('webformatURL')]
    except Exception as e:
        app.logger.error(f"Error en Pixabay API: {str(e)}")
        return []

def get_unsplash_images(query):
    """Obtiene imágenes de flores de Unsplash"""
    try:
        headers = {
            'Authorization': f'Client-ID {APIS["unsplash"]["key"]}',
            'Accept-Version': 'v1'
        }
        params = {
            'query': f"{query} flower",
            **APIS['unsplash']['params']
        }

        response = requests.get(
            APIS['unsplash']['url'],
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code == 403:
            app.logger.error("Clave API de Unsplash no válida o límite excedido")
            return []

        response.raise_for_status()
        data = response.json()

        return [img['urls']['regular'] for img in data.get('results', []) if img.get('urls', {}).get('regular')]
    except Exception as e:
        app.logger.error(f"Error en Unsplash API: {str(e)}")
        return []

def get_wikipedia_data(query):
    """Obtiene información de Wikipedia"""
    try:
       
        page = wiki_wiki.page(f"{query} (flor)")

        if not page.exists():
           
            page = wiki_wiki.page(query)

            if not page.exists():
               
                sci_name = get_scientific_name(query)
                if sci_name != query:
                    page = wiki_wiki.page(sci_name)
                    if not page.exists():
                        return None

       
        if not is_flower_related(page.summary or '') and not is_flower_related(page.title or ''):
            return None

        return {
            'title': page.title,
            'summary': (page.summary[:500] + '...') if page.summary else None,
            'url': page.fullurl,
            'extract': page.text[:1000] if page.text else None
        }
    except Exception as e:
        app.logger.error(f"Error en Wikipedia API: {str(e)}")
        return None

def generate_suggestions(query):
    """Genera sugerencias relevantes basadas en la consulta"""
    suggestions = set()

    for synonym, canonical in FLOWER_SYNONYMS.items():
        if query in synonym:
            suggestions.add(canonical)

    for flower in FLOWER_KEYWORDS:
        if query in flower or flower in query:
            suggestions.add(flower)

    prefix = query[:3] if query else ''
    for flower in FLOWER_KEYWORDS:
        if prefix and flower.startswith(prefix):
            suggestions.add(flower)

    if len(suggestions) < 3:
        suggestions.update(['rosa', 'tulipán', 'girasol', 'orquídea', 'jazmín'])

    return sorted(suggestions)[:10]

def enhance_plant_data(plant_data, wiki_data, query):
    """Combina y mejora datos de plantas"""
    if not plant_data:
        plant_data = {'name': query.capitalize()}

    if wiki_data:
        if not plant_data.get('scientific_name'):
            plant_data['scientific_name'] = wiki_data.get('title')

        if wiki_data.get('summary'):
            if plant_data.get('description'):
                if wiki_data['summary'] not in plant_data['description']:
                    plant_data['description'] += "\n\n" + wiki_data['summary']
            else:
                plant_data['description'] = wiki_data['summary']


    if not plant_data.get('scientific_name'):
        plant_data['scientific_name'] = get_scientific_name(query)

    return plant_data

@app.before_request
def load_user():
    g.user = session.get("usuario")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        contrasena = request.form.get("contrasena", "")

        if not correo or not contrasena:
            flash("Completa correo y contraseña", "error")
            return redirect(url_for("login"))

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and bcrypt.check_password_hash(user["contrasena"], contrasena):
            session.permanent = True
            session["usuario"] = user["nombre"]
            session["correo"] = user["correo"]
            return redirect(url_for("index"))
        else:
            flash("Correo o contraseña incorrectos", "error")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        contrasena_raw = request.form.get("contrasena", "")

        if not nombre or not correo or not contrasena_raw:
            flash("Todos los campos son obligatorios", "error")
            return redirect(url_for("register"))

        contrasena = bcrypt.generate_password_hash(contrasena_raw).decode("utf-8")

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO usuarios (nombre, correo, contrasena) VALUES (%s, %s, %s)",
                (nombre, correo, contrasena)
            )
            conn.commit()
            flash("Usuario creado correctamente. Ahora inicia sesión", "success")
            return redirect(url_for("login"))
        except mysql.connector.Error as e:
            app.logger.error(f"MySQL error: {str(e)}")
            flash("Ese correo ya está registrado", "error")
            return redirect(url_for("register"))
        finally:
            cur.close()
            conn.close()

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():

    return render_template("index.html", usuario=session.get("usuario"))


@app.route("/search", methods=["POST"])
@login_required
def search():
    query = request.form.get('query', '').strip()

    if not query or len(query) < 2:
        return jsonify({'error': 'Ingresa al menos 2 caracteres', 'suggestions': []}), 400

    normalized_query = normalize_flower_name(query)

    if not is_flower_related(normalized_query):
        suggestions = generate_suggestions(normalized_query)
        return jsonify({
            'error': f'No encontramos "{query}"',
            'suggestions': suggestions
        }), 400

    try:
        with ThreadPoolExecutor() as executor:
            perenual_future = executor.submit(get_perenual_data, normalized_query)
            pixabay_future = executor.submit(get_pixabay_images, normalized_query)
            unsplash_future = executor.submit(get_unsplash_images, normalized_query)
            wikipedia_future = executor.submit(get_wikipedia_data, normalized_query)

            perenual_data = perenual_future.result()
            pixabay_data = pixabay_future.result()
            unsplash_data = unsplash_future.result()
            wikipedia_data = wikipedia_future.result()

        images = (pixabay_data + unsplash_data) if (pixabay_data or unsplash_data) else []

        combined_data = {
            'plant_info': enhance_plant_data(perenual_data, wikipedia_data, query),
            'images': images[:6],
            'wikipedia': wikipedia_data,
            'query': query,
            'normalized_query': normalized_query,
            'sources': {
                'perenual': bool(perenual_data),
                'pixabay': bool(pixabay_data),
                'unsplash': bool(unsplash_data),
                'wikipedia': bool(wikipedia_data)
            }
        }

        
        if not any([perenual_data, pixabay_data, unsplash_data, wikipedia_data]):
            sci_name = get_scientific_name(normalized_query)
            if sci_name and sci_name != normalized_query:
                normalized_sci = normalize_flower_name(sci_name)
                with ThreadPoolExecutor() as executor:
                    perenual_future = executor.submit(get_perenual_data, normalized_sci)
                    pixabay_future = executor.submit(get_pixabay_images, normalized_sci)
                    unsplash_future = executor.submit(get_unsplash_images, normalized_sci)
                    wikipedia_future = executor.submit(get_wikipedia_data, normalized_sci)

                    perenual_data2 = perenual_future.result()
                    pixabay_data2 = pixabay_future.result()
                    unsplash_data2 = unsplash_future.result()
                    wikipedia_data2 = wikipedia_future.result()

                images2 = (pixabay_data2 + unsplash_data2) if (pixabay_data2 or unsplash_data2) else []

                if any([perenual_data2, pixabay_data2, unsplash_data2, wikipedia_data2]):
                    combined_data = {
                        'plant_info': enhance_plant_data(perenual_data2, wikipedia_data2, sci_name),
                        'images': images2[:6],
                        'wikipedia': wikipedia_data2,
                        'query': query,
                        'normalized_query': normalized_sci,
                        'sources': {
                            'perenual': bool(perenual_data2),
                            'pixabay': bool(pixabay_data2),
                            'unsplash': bool(unsplash_data2),
                            'wikipedia': bool(wikipedia_data2)
                        }
                    }
                    return jsonify(combined_data)

            return jsonify({
                'error': 'No se encontraron resultados para flores con ese nombre',
                'suggestions': generate_suggestions(normalized_query)
            }), 404

        return jsonify(combined_data)

    except Exception as e:
        app.logger.error(f"Error en la búsqueda: {str(e)}")
        return jsonify({'error': 'Ocurrió un error al buscar información sobre la flor'}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
   
    try:
        init_db()
    except Exception as e:
        print("Aviso init_db:", e)
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
