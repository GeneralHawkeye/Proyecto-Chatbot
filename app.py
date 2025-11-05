from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import json
import os

app = Flask(__name__, static_url_path='')
CORS(app)

@app.route('/')
def home():
    return send_file('chatbot.html')

@app.route('/CSS/<path:path>')
def send_css(path):
    return send_from_directory('CSS', path)

@app.route('/img/<path:path>')
def send_img(path):
    return send_from_directory('img', path)

@app.route('/video/<path:path>')
def send_video(path):
    return send_from_directory('video', path)


# Carga del dataset desde archivo JSON
DATA_FILE = os.path.join(os.path.dirname(__file__), 'dataset.json')

def load_dataset():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

DATASET = load_dataset()


# Menú principal estructurado
MAIN_MENU = {
    "1": {"name": "Reservas y precios", "intent": "reserva_info"},
    "2": {"name": "Habitaciones", "intent": "habitacion_info"},
    "3": {"name": "Servicios del hotel", "intent": "servicios_info"},
    "4": {"name": "Check-in / Check-out", "intent": "checkin_info"},
    "5": {"name": "Ubicación y contacto", "intent": "ubicacion_info"},
    "6": {"name": "Promociones y políticas", "intent": "promociones_info"},
    "7": {"name": "Actividades y alrededores", "intent": "sugerencias"},
    "8": {"name": "Reportar un problema", "intent": "quejas"}
}


# Contexto temporal de usuario (por sesión)

USER_CONTEXT = {}  # { session_id: { "intent": str, "submenu": list } }


# Funciones auxiliares
def show_main_menu():
    menu_text = "🏖️ *Bienvenido al Hotel Paraíso Azul*\n\n"
    menu_text += "Selecciona una opción:\n"
    
    for key, item in MAIN_MENU.items():
        menu_text += f"{key}. {item['name']}\n"
    
    menu_text += "\nEscribe el número de la opción o 'salir' para terminar."
    return menu_text

def show_submenu(intent):
    items = [it for it in DATASET if it.get('intent') == intent]
    if not items:
        return "No hay información disponible para esta sección."
    submenu_text = f"Has seleccionado '{intent}'. Estas son las opciones disponibles:\n"
    for idx, it in enumerate(items, start=1):
        submenu_text += f"{idx}. {it['question']}\n"
    submenu_text += "\nEscribe el número de la pregunta para ver la respuesta o 'menu' para regresar al inicio."
    return submenu_text


# Lógica principal del chatbot
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    session_id = data.get('session', 'default')
    msg = user_message.lower()

    context = USER_CONTEXT.get(session_id, {})

    # Si el usuario pide salir
    if msg in ['salir', 'adios', 'gracias']:
        USER_CONTEXT.pop(session_id, None)
        return jsonify({'reply': "👋 ¡Gracias por visitar el Hotel Paraíso Azul! Esperamos verte pronto.", 'source': 'exit'})

    # Si el usuario está en un submenú
    if context.get('submenu'):
        submenu = context['submenu']
        if msg.isdigit():
            idx = int(msg) - 1
            if 0 <= idx < len(submenu):
                item = submenu[idx]
                return jsonify({'reply': item['response'], 'source': 'submenu'})
            else:
                return jsonify({'reply': "Opción no válida. Intenta de nuevo.", 'source': 'submenu'})
        elif msg in ['menu', 'inicio']:
            USER_CONTEXT.pop(session_id, None)
            return jsonify({'reply': show_main_menu(), 'source': 'menu'})
        else:
            return jsonify({'reply': "Por favor, selecciona un número válido o escribe 'menu' para regresar.", 'source': 'submenu'})

    # Si el usuario saluda o pide el menú
    if msg in ['hola', 'buenos días', 'buenas tardes', 'menu', 'inicio']:
        USER_CONTEXT.pop(session_id, None)
        return jsonify({'reply': show_main_menu(), 'source': 'menu'})

    # Si elige una opción del menú principal
    if msg in MAIN_MENU:
        intent = MAIN_MENU[msg]['intent']
        items = [it for it in DATASET if it.get('intent') == intent]
        USER_CONTEXT[session_id] = {"intent": intent, "submenu": items}
        reply = show_submenu(intent)
        return jsonify({'reply': reply, 'source': 'submenu'})

    # Si no coincide con ninguna opción
    return jsonify({'reply': "No entendí tu solicitud. Escribe 'menu' para ver las opciones disponibles.", 'source': 'default'})


#  Endpoints adicionales opcionales (debug/consulta)
@app.route('/menu', methods=['GET'])
def menu():
    intents = {}
    for item in DATASET:
        intent = item.get('intent', 'general')
        intents[intent] = intents.get(intent, 0) + 1
    menu_list = [{'intent': k, 'count': v} for k, v in intents.items()]
    return jsonify({'menu': menu_list})

@app.route('/menu/<intent>', methods=['GET'])
def menu_intent(intent):
    items = [{'id': it['id'], 'question': it['question']} for it in DATASET if it.get('intent') == intent]
    return jsonify({'intent': intent, 'items': items})

@app.route('/faq/<int:item_id>', methods=['GET'])
def faq(item_id):
    for it in DATASET:
        if int(it.get('id')) == int(item_id):
            return jsonify({'id': it.get('id'), 'question': it.get('question'), 'answer': it.get('response')})
    return jsonify({'error': 'not found'}), 404


# Ejecución del servidor Flask
if __name__ == '__main__':
    app.run(debug=True)


