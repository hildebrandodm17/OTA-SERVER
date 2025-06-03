import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template, flash, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = "uma_chave_aleatoria_para_flash"
UPLOAD_FOLDER = "uploads"
LAST_CONFIRM_FILE = "last_confirm.txt"
ALLOWED_EXTENSIONS = {"bin"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def grava_ultima_confirmacao():
    """Grava a data/hora UTC atual em LAST_CONFIRM_FILE."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LAST_CONFIRM_FILE, "w") as f:
        f.write(now)

def le_ultima_confirmacao():
    """Lê o conteúdo de LAST_CONFIRM_FILE, caso exista."""
    if os.path.exists(LAST_CONFIRM_FILE):
        with open(LAST_CONFIRM_FILE, "r") as f:
            return f.read().strip()
    return None

# Rota principal: mostra o formulário e, se houver, a última confirmação
@app.route("/", methods=["GET"])
def index():
    status = request.args.get("status", "")
    ultima = le_ultima_confirmacao()
    return render_template("index.html", status=status, ultima_confirmacao=ultima)

# Rota /upload: recebe o POST do formulário, salva firmware.bin em uploads/
@app.route("/upload", methods=["POST"])
def upload_firmware():
    if "file" not in request.files:
        flash("Nenhum arquivo enviado.")
        return redirect(url_for("index", status="erro"))
    file = request.files["file"]
    if file.filename == "":
        flash("Nome de arquivo vazio.")
        return redirect(url_for("index", status="erro"))
    if file and allowed_file(file.filename):
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], "firmware.bin")
        file.save(save_path)
        flash("Upload realizado com sucesso! O ESP32 irá baixar o firmware.")
        return redirect(url_for("index", status="sucesso"))
    else:
        flash("Formato inválido. Só .bin permitido.")
        return redirect(url_for("index", status="erro"))

# Rota /firmware.bin: o ESP32 faz GET aqui para obter o binário
@app.route("/firmware.bin", methods=["GET"])
def serve_firmware():
    firmware_path = os.path.join(app.config["UPLOAD_FOLDER"], "firmware.bin")
    if os.path.exists(firmware_path):
        return send_from_directory(app.config["UPLOAD_FOLDER"], "firmware.bin", as_attachment=True)
    else:
        return "Firmware não encontrado", 404

# Rota /confirm: ESP32 envia POST JSON {"device":"NSU123","status":"ok"} para apagar o firmware
@app.route("/confirm", methods=["POST"])
def confirm_update():
    firmware_path = os.path.join(app.config["UPLOAD_FOLDER"], "firmware.bin")
    if os.path.exists(firmware_path):
        try:
            os.remove(firmware_path)
            # grava data/hora da confirmação
            grava_ultima_confirmacao()
            return jsonify({"message": "Firmware apagado com sucesso."}), 200
        except Exception as e:
            return jsonify({"message": f"Erro ao apagar: {str(e)}"}), 500
    else:
        return jsonify({"message": "Não havia firmware para apagar."}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
