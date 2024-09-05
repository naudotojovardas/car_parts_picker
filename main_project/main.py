from fastapi import FastAPI, Form, Depends, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from backend import get_db, Part, CarParameter, ADMIN_PASSWORD, add_part_to_db, add_part_parameters_to_db, remove_part_from_db
from frontend import generate_html_content
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os

app = FastAPI()

# Directory where uploaded photos will be stored
UPLOAD_DIR = "uploaded_photos"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load templates
templates = Jinja2Templates(directory="templates")

# Title page route
@app.get("/", response_class=HTMLResponse)
async def title_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Main webpage route
@app.get("/main", response_class=HTMLResponse)
async def read_root(db: Session = Depends(get_db)):
    try:
        html_content = generate_html_content(db)
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {e}</h1>")

# Add part route with photo upload
@app.post("/add_part/", response_class=HTMLResponse)
async def add_part(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    currency: str = Form(...),
    stock_quantity: int = Form(...),
    part_parameters: int = Form(None),  # Optional
    file: UploadFile = File(None),  # Optional file upload
    db: Session = Depends(get_db)
):
    try:
        # Save the file to the server if it was uploaded
        file_location = None
        if file:
            file_location = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_location, "wb") as file_object:
                file_object.write(file.file.read())

        # Call the add_part_to_db function with the path to the saved file
        add_part_to_db(
            db=db,
            name=name,
            description=description,
            price=price,
            currency=currency,
            stock_quantity=stock_quantity,
            part_parameters=part_parameters,
            photo_path=file_location  # Pass the file path to the database
        )

        return HTMLResponse(content="""
        <html>
        <head>
            <meta http-equiv="refresh" content="0;url=/main" />
        </head>
        <body>
            <p>Part added successfully! Redirecting...</p>
        </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {e}</h1>")

# Add part parameters route
@app.post("/add_part_parameters/", response_class=HTMLResponse)
async def add_part_parameters(
    car_name: str = Form(...),
    manufacturer: str = Form(...),
    year: int = Form(...),
    engine_type: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        add_part_parameters_to_db(db, car_name, manufacturer, year, engine_type)
        return HTMLResponse(content="""
        <html>
        <head>
            <meta http-equiv="refresh" content="0;url=/main" />
        </head>
        <body>
            <p>Part parameters added successfully! Redirecting...</p>
        </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {e}</h1>")

# Remove part route
@app.post("/remove_part/", response_class=HTMLResponse)
async def remove_part(id: int = Form(...), admin_code: str = Form(...), db: Session = Depends(get_db)):
    try:
        if admin_code != ADMIN_PASSWORD:
            raise HTTPException(status_code=403, detail="Unauthorized: Incorrect Admin Code")
        
        remove_part_from_db(db, id)
        return HTMLResponse(content="""
        <html>
        <head>
            <meta http-equiv="refresh" content="0;url=/main" />
        </head>
        <body>
            <p>Part removed successfully! Redirecting...</p>
        </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {e}</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

