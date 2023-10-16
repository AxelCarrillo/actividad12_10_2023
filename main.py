from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import csv
from PIL import Image, ImageOps
from io import BytesIO
from typing import List, Optional
import qrcode  # Importar la biblioteca qrcode

app = FastAPI()

# Ruta al archivo CSV de contactos
archivo_csv = 'contactos.csv'

# Ruta donde se guardarán las imágenes
ruta_imagenes = 'imagenes/'

# Modelo de datos para contactos
class Contacto(BaseModel):
    id_contacto: int
    nombre: str
    primer_apellido: str
    segundo_apellido: str
    email: str
    telefono: str

# Endpoint para buscar contactos por nombre en formato JSON
@app.get("/buscar_contacto", response_model=List[Contacto], description="Buscar contactos por nombre en formato JSON")
def buscar_contacto(nombre: str):
    lista_contactos = []
    with open(archivo_csv, 'r', newline='') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            if nombre.lower() in row['nombre'].lower():
                lista_contactos.append(row)
    return lista_contactos


# Endpoint para obtener todos los contactos
@app.get("/contactos", response_model=List[Contacto], description="Listar contactos en formato JSON")
def obtener_contactos():
    lista_contactos = []
    with open(archivo_csv, 'r', newline='') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            lista_contactos.append(row)
    return lista_contactos

# Endpoint para agregar un nuevo contacto
@app.post("/contactos", response_model=Contacto)
def agregar_contacto(contacto: Contacto):
    with open(archivo_csv, 'a', newline='') as csvfile:
        fieldnames = contacto.dict().keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow(jsonable_encoder(contacto))
    return contacto

# Endpoint para actualizar un contacto por id_contacto
@app.put("/contactos/{id_contacto}", response_model=Contacto)
def actualizar_contacto(id_contacto: int, contacto: Contacto):
    lista_contactos = []
    actualizado = False
    with open(archivo_csv, 'r', newline='') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            if int(row['id_contacto']) == id_contacto:
                row = jsonable_encoder(contacto)
                actualizado = True
            lista_contactos.append(row)
    if actualizado:
        with open(archivo_csv, 'w', newline='') as csvfile:
            fieldnames = lista_contactos[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in lista_contactos:
                writer.writerow(row)
        return contacto
    raise HTTPException(status_code=404, detail="Contacto no encontrado")

# Endpoint para borrar un contacto por id_contacto
@app.delete("/contactos/{id_contacto}")
def borrar_contacto(id_contacto: int):
    lista_contactos = []
    eliminado = False
    with open(archivo_csv, 'r', newline='') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            if int(row['id_contacto']) == id_contacto:
                eliminado = True
            else:
                lista_contactos.append(row)
    if eliminado:
        with open(archivo_csv, 'w', newline='') as csvfile:
            fieldnames = lista_contactos[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in lista_contactos:
                writer.writerow(row)
        return "Contacto eliminado"
    raise HTTPException(status_code=404, detail="Contacto no encontrado")

# Ruta para generar un código QR a partir de una URL de imagen
@app.get("/generar_qr")
def generar_qr(url_imagen: str):
    # Crea un objeto QRCode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Agrega la URL de la imagen al código QR
    qr.add_data(url_imagen)
    qr.make(fit=True)

    # Crea una imagen PIL
    imagen_qr = qr.make_image(fill_color="black", back_color="white")

    # Define la ruta de guardado del código QR en la carpeta "imagenes"
    ruta_guardado = f"{ruta_imagenes}codigo_qr.png"

    # Guarda la imagen QR en la carpeta "imagenes"
    imagen_qr.save(ruta_guardado)

    # Devuelve la imagen QR como una respuesta de transmisión
    with open(ruta_guardado, "rb") as f:
        imagen_data = f.read()

    return {"mensaje": "Código QR generado", "imagen_qr": imagen_data}

# Endpoint para cargar y procesar una imagen con efectos opcionales
@app.post("/imagenes")
async def cargar_imagen(
    imagen: UploadFile, 
    crop: Optional[str] = None, 
    fliph: Optional[bool] = False, 
    colorize: Optional[bool] = False
):
    imagen_path = ruta_imagenes + imagen.filename
    
    with open(imagen_path, "wb") as image_file:
        image_file.write(imagen.file.read())
    
    img = Image.open(imagen_path)
    
    if crop:
        coordenadas = [int(x) for x in crop.split(',')]
        img = img.crop(coordenadas)
    
    if fliph:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    
    if colorize:
        img = ImageOps.colorize(img, '#00f', '#f00')
    
    img.save(imagen_path)
    
    return JSONResponse(content={"message": "Imagen procesada y guardada"}, status_code=200)
