import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template, flash, jsonify

app = Flask(__name__)
app.secret_key = "uma_chave_aleatoria_para_flash"  # qualquer string serve
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"bin"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# Garante que a pasta 'uploads' exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Rota principal: mostra o formulário de upload
@app.route("/", methods=["GET"])
def index():
    # 'status' pode mostrar mensagens de erro/sucesso
    status = request.args.get("status", "")
    return render_template("index.html", status=status)

# Rota /upload: recebe o POST do formulário, salva firmware.bin em uploads/
@app.route("/upload", methods=["POST"])
def upload_firmware():
    # 'file' é o name do <input> no formulário
    if "file" not in request.files:
        flash("Nenhum arquivo enviado.")
        return redirect(url_for("index", status="erro"))
    file = request.files["file"]
    if file.filename == "":
        flash("Nome de arquivo vazio.")
        return redirect(url_for("index", status="erro"))
    if file and allowed_file(file.filename):
        # Salva sempre como 'firmware.bin', sobrescrevendo se já existir
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
        # Envia o 'firmware.bin' diretamente
        return send_from_directory(app.config["UPLOAD_FOLDER"], "firmware.bin", as_attachment=True)
    else:
        # Se não existir, retorna 404
        return "Firmware não encontrado", 404

# Rota /confirm: ESP32 envia POST JSON {"device":"NSU123","status":"ok"} para apagar o firmware
@app.route("/confirm", methods=["POST"])
def confirm_update():
    # Opcional: pode checar request.json["device"], ["status"], etc.
    firmware_path = os.path.join(app.config["UPLOAD_FOLDER"], "firmware.bin")
    if os.path.exists(firmware_path):
        try:
            os.remove(firmware_path)
            return jsonify({"message": "Firmware apagado com sucesso."}), 200
        except Exception as e:
            return jsonify({"message": f"Erro ao apagar: {str(e)}"}), 500
    else:
        return jsonify({"message": "Não havia firmware para apagar."}), 200

if __name__ == "__main__":
    # Só roda em debug/local. No Render, o entrypoint será via gunicorn.
    app.run(host="0.0.0.0", port=5000, debug=True)
