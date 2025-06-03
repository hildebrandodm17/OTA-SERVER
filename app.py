import os
from flask import Flask, request, render_template, send_from_directory, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"bin"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Garante que a pasta exista
if not os.path.isdir(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Página principal com formulário de upload e status.
    """
    message = ""
    if request.method == "POST":
        # Verifica se veio um arquivo no campo "firmware"
        if "firmware" not in request.files:
            message = "Nenhum arquivo enviado."
            return render_template("index.html", message=message)

        file = request.files["firmware"]
        if file.filename == "":
            message = "Nome de arquivo inválido."
            return render_template("index.html", message=message)

        if file and allowed_file(file.filename):
            # Sempre salvamos como firmware.bin (sobrescreve versões antigas)
            destino = os.path.join(app.config["UPLOAD_FOLDER"], "firmware.bin")
            file.save(destino)
            message = "Upload realizado com sucesso! O ESP32 irá baixar o firmware."
        else:
            message = "Formato inválido. Envie um arquivo .bin."
    return render_template("index.html", message=message)

@app.route("/firmware.bin", methods=["GET"])
def serve_firmware():
    """
    Rota para o ESP32 baixar o firmware.
    Se firmware.bin existe em uploads/, retorna-o. Caso contrário, 404.
    """
    caminho = os.path.join(app.config["UPLOAD_FOLDER"], "firmware.bin")
    if os.path.isfile(caminho):
        # force_download=False faz com que seja servido “inline,” mas o ESP32 tratará.
        return send_from_directory(app.config["UPLOAD_FOLDER"], "firmware.bin", as_attachment=True)
    else:
        # Arquivo não encontrado → ESP interpreta como "nenhuma atualização disponível"
        return ("", 404)

@app.route("/confirm", methods=["POST"])
def confirm():
    """
    Rota que recebe a confirmação do ESP32.
    Espera um JSON com {"device": "identificador", "status": "ok"}.
    Se status == "ok", apaga firmware.bin e retorna 200.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido"}), 400

    # Você pode validar aqui se data.get("device") bate com algo que espera.
    status = data.get("status", "")
    if status == "ok":
        caminho = os.path.join(app.config["UPLOAD_FOLDER"], "firmware.bin")
        if os.path.isfile(caminho):
            try:
                os.remove(caminho)
                return jsonify({"message": "Firmware apagado com sucesso."}), 200
            except Exception as e:
                return jsonify({"error": f"Falha ao apagar: {str(e)}"}), 500
        else:
            return jsonify({"message": "Não havia firmware para apagar."}), 200
    else:
        return jsonify({"error": "Status inválido"}), 400

if __name__ == "__main__":
    # Para desenvolvimento local. No Render, o gunicorn do Procfile será usado.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
