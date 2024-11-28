from fastapi import FastAPI, Form, Depends, HTTPException, File, UploadFile, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from crud_authorization import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user, pwd_context,
     ADMIN_PASSWORD, get_or_create_cart, car_facts
)
from db_models import User, Part, CartItem, Cart, CarParameter
from pydantic_models import Token
from database import get_db, create_database
import random

create_database()

app = FastAPI()

ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Directory where uploaded photos will be stored
UPLOAD_DIR = "static/uploaded_photos"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


# Mount static directory an Load templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Title page route
@app.get("/", response_class=HTMLResponse)
async def title_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/main", response_class=HTMLResponse)
async def shop(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    products = db.query(Part).all()
    random_fact = random.choice(car_facts)
    
    # Get or create the user's cart and calculate item count
    cart = get_or_create_cart(db, user.id)
    cart_count = sum(item.quantity for item in cart.items)

    return templates.TemplateResponse("shop.html", {"request": request, "products": products, "cart_count": cart_count, "random_fact": random_fact})


def generate_html_content(db: Session):
    car_message = random.choice(car_facts)

    # Query parts and parameters
    parts_list = db.query(Part).all()
    part_parameters_list = db.query(CarParameter).all()

    # Generate the HTML for parts
    parts_html = "".join(
        f"<li>{part.part_name}: {part.description} - {part.price:.2f} {part.currency} | Stock: {part.stock_quantity} | Car: {part.part_parameters.car_name if part.part_parameters else 'N/A'}" +
        f"<form action='/remove_part/' method='post' style='display:inline; margin-left: 10px;'><input type='hidden' name='id' value='{part.id}' /><input type='password' name='admin_code' placeholder='Admin Code' required style='padding: 3px; width: 120px; margin-right: 5px;' /><button type='submit' style='padding: 3px 6px; background-color: #e74c3c; color: white; border: none; cursor: pointer; border-radius: 5px;'>Remove</button></form>" +
        (f"<br><img src='/static/{part.photo_path}' alt='No Image' style='max-width: 200px; max-height: 200px; margin-top: 10px;'>" if part.photo_path else '') +
        "</li>" 
        for part in parts_list
    )

    # Generate the HTML for car parameters
    part_parameters_html = "".join(
        f"<option value='{parameter.id}'>{parameter.car_name} ({parameter.year}) - {parameter.engine_type}</option>" for parameter in part_parameters_list
    )

    # Return a dictionary to pass to the HTML template
    return {
        "car_message": car_message,
        "parts_html": parts_html,
        "part_parameters_html": part_parameters_html
    }


# Main webpage route
@app.get("/shop", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        content = generate_html_content(db)
        return templates.TemplateResponse("admin.html", {"request": request, **content})
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {e}</h1>")




# Login page route
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def show_registration_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    print(f"Login attempt for user: {username}")
    
    # Use the session `db` to query the database
    user = authenticate_user(username, password, db)

    if not user:
        print(f"Authentication failed for user: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    access_token = create_access_token(data={"sub": user.username})

    print(f"Login successful for user: {username}")
    # return JSONResponse({"access_token": access_token, "token_type": "bearer"})
    response=RedirectResponse(url="/main", status_code=303)
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True, 
        secure=True,   # Enable this in production (HTTPS only)
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return response
    # return RedirectResponse(request.url_for("read_root"), status_code=303)


# Register a User
@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...),role: str = Form("user"), db: Session = Depends(get_db)):
    user_in_db = db.query(User).filter(User.email == email).first()
    if user_in_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(password)    
    new_user = User(email=email, username=username, hashed_password=hashed_password, role=role)

    # Add new user to the database and commit
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return templates.TemplateResponse("register_success.html", {"request": request})
    

# Login User and Issue Token
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},  # Use 'user.username' from the User model, not dictionary
        expires_delta=access_token_expires
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
    file: UploadFile = None,  # Optional file upload
    db: Session = Depends(get_db)
):
    try:
        # Save the file to the server if it was uploaded
        file_location = None
        print(f"File: {file}")
        file_content = await file.read()
        if file_content:
            print(f"Saving file: {file.filename}")
            file_location = os.path.join(UPLOAD_DIR, file.filename)
            print(f"File location: {file_location}")
            with open(file_location, "wb") as file_object:
                file_object.write(file_content)


        # Call the add_part_to_db function with the path to the saved file
        add_part_to_db(
            
            name=name,
            description=description,
            price=price,
            currency=currency,
            stock_quantity=stock_quantity,
            part_parameters=part_parameters,
            photo_path=file_location,  # Pass the file path to the database
            db = db
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
    print(f"engine type is {engine_type} 1")
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
async def remove_part(db: Session = Depends(get_db), id: int = Form(...), admin_code: str = Form(...)):
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
    

@app.put("/admin/set_role/{user_id}")
async def set_role(user_id: int, role: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if the current user is an admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can set roles")
    
    # Fetch user by ID and update role
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role
    db.commit()
    return {"message": f"User {user.username}'s role updated to {role}"}


@app.post("/add_to_cart/{product_id}")
async def add_to_cart(product_id: int, quantity: int = Form(...), db: Session = Depends(get_db)):
    # Fetch the product from the database
    product = db.query(CartItem).filter(CartItem.cart_id == product_id).first()
    
    if not product:
        return {"error": "Product not found"}
    
    # Check if enough stock is available
    if product.quantity < quantity:
        return {"error": "Not enough stock"}
    
    # Check if the item is already in the cart
    cart_item = db.query(CartItem).filter(CartItem.id == product_id).first()
    if cart_item:
        # Update the quantity if the item is already in the cart
        if product.stock_quantity >= cart_item.quantity + quantity:
            cart_item.quantity += quantity
        else:
            return {"error": "Not enough stock"}
    else:
        # Add the item to the cart
        new_cart_item = CartItem(
            id=product.id,
            cart_id=product_id,
            part_id=product_id,
            quantity=quantity
        )
        db.add(new_cart_item)
    
    # Reduce the product stock
    product.quantity -= quantity
    db.commit()
    
    return {"message": "Item added to cart"}


@app.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    cart = get_or_create_cart(db, user_id)
    cart_items = cart.items if cart else []
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return templates.TemplateResponse("cart.html", {"request": request, "cart_items": cart_items, "total_price": total_price})


@app.get("/cart")
def view_cart(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Fetch all cart items for the current user
    cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()
    print(f"Cart items for user {current_user.id}: {[(item.product_id, item.quantity) for item in cart_items]}")  # Debugging
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    # Render cart template with items and total cost
    return templates.TemplateResponse("cart.html", {"request": request, "cart_items": cart_items, "total": total})


def add_part_to_db(db: Session, name: str, description: str, price: float, currency: str, stock_quantity: int, part_parameters: int = None, photo_path: str = None):
    new_part = Part(
        part_name=name,
        description=description,
        price=price,
        currency=currency,
        stock_quantity=stock_quantity,
        part_parameters_id=part_parameters,
        photo_path=photo_path
    )
    db.add(new_part)  # Add the new part to the session.
    db.commit()  # Commit the transaction to save changes in the DB.


# Add car part parameters to the `part_parameters` table in the database.
def add_part_parameters_to_db(db: Session, car_name: str, manufacturer: str, year: int, engine_type: str):
    print(f"engine type is {engine_type} 2")
    new_part_parameter = CarParameter(
        car_name=car_name,
        manufacturer=manufacturer,
        year=year,
        engine_type=engine_type
    )
    db.add(new_part_parameter)  # Add the new parameters to the session.
    db.commit()  # Commit the transaction to save the new parameters.


# Remove a part from the `parts` table in the database by its ID.
def remove_part_from_db(db: Session, part_id: int):
    part_to_remove = db.query(Part).filter(Part.id == part_id).first()  # Find the part by ID.
    if part_to_remove:
        db.delete(part_to_remove)  # Mark the part for deletion.
        db.commit()  # Commit the transaction to apply the deletion.




# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)


# fastapi dev main_project/main.py



