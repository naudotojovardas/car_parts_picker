from fastapi import FastAPI, Form, Depends, HTTPException, File, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from frontend import generate_html_content
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from pydantic import BaseModel, EmailStr, field_validator
from backend import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user, verify_password, fake_users_db, add_part_to_db, add_part_parameters_to_db,
    remove_part_from_db, ADMIN_PASSWORD

)

app = FastAPI()

ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
async def read_root():
    try:
        html_content = generate_html_content(fake_users_db)
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {e}</h1>")


# Pydantic Models
class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str

class UserInDB(User):
    hashed_password: str



# Login page route
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Register page route
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})



# Handle login form submission
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    # Check if user exists in the fake database
    user = fake_users_db.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify the password using the hashed password
    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Redirect to the main page upon successful login
    return RedirectResponse(url="/main", status_code=303)


# Register a User
@field_validator('email')
@app.post("/register")
async def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(password)    
    fake_users_db[username] = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password}
    
    return RedirectResponse(url="/main", status_code=303)


@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})
    

# Login User and Issue Token
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}




# Protected Route
@app.get("/users/me/")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user['username'], "email": current_user['email']}



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
async def remove_part(id: int = Form(...), admin_code: str = Form(...)):
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

