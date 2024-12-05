from fastapi import FastAPI, Form, Depends, HTTPException, File, UploadFile, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user, pwd_context,
     ADMIN_PASSWORD
)
from crud import add_part_parameters_to_db, add_part_to_db, remove_part_from_db, get_or_create_cart
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
async def title_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/main", response_class=HTMLResponse)
async def shop(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> HTMLResponse:
    products = db.query(Part).all()
    random_fact = random.choice(car_facts)
    
    # Get or create the user's cart and calculate item count
    cart = get_or_create_cart(db, user.id)
    cart_count = sum(item.quantity for item in cart.items)

    return templates.TemplateResponse("shop.html", {"request": request, "products": products, "cart_count": cart_count, "random_fact": random_fact})


def generate_html_content(db: Session) -> dict:
    car_message = random.choice(car_facts)

    # Query parts and parameters
    parts_list = db.query(Part).all()
    part_parameters_list = db.query(CarParameter).all()

    # Generate the HTML for parts
    parts_html = "".join(
        f"<li>{part.part_name}: {part.description} - {part.price:.2f} {part.currency} | Stock: {part.stock_quantity} | Car: {part.part_parameters if part.part_parameters else 'N/A'}" +
        f"<form action='/remove_part/' method='post' style='display:inline; margin-left: 10px;'><input type='hidden' name='id' value='{part.id}' /><input type='password' name='admin_code' placeholder='Admin Code' required style='padding: 3px; width: 120px; margin-right: 5px;' /><button type='submit' style='padding: 3px 6px; background-color: #e74c3c; color: white; border: none; cursor: pointer; border-radius: 5px;'>Remove</button></form>" +
        (f"<br><img src='/static/{part.photo_path}' alt='No Image' style='max-width: 200px; max-height: 200px; margin-top: 10px;'>" if part.photo_path else '') +
        "</li>" 
        for part in parts_list
    )

    # Generate the HTML for part parameters
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
async def read_root(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> HTMLResponse:
    try:
        content = generate_html_content(db)
        return templates.TemplateResponse("admin.html", {"request": request, **content})
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {e}</h1>")




# Login page route
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def show_registration_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)) -> RedirectResponse:
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
async def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...),role: str = Form("user"), db: Session = Depends(get_db)) -> HTMLResponse:
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
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict:
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
async def read_users_me(current_user: User = Depends(get_current_user)) -> dict:
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
) -> HTMLResponse:
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
    request: Request,
    car_name: str = Form(...),
    manufacturer: str = Form(...),
    year: int = Form(...),
    engine_type: str = Form(...),
    db: Session = Depends(get_db)    
) -> HTMLResponse:
    print(f"engine type is {engine_type} 1")
    try:
        add_part_parameters_to_db(db, car_name, manufacturer, year, engine_type)
        return HTMLResponse(content="""
        <html>
        <head>
            <meta http-equiv="refresh" content="0;url=/shop" />
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
async def remove_part(db: Session = Depends(get_db), id: int = Form(...), admin_code: str = Form(...)) -> HTMLResponse:
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
async def set_role(user_id: int, role: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
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
async def add_to_cart(
    product_id: int,
    quantity: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Dependency injection for current user
) -> dict:
    # Use the current user's ID
    user_id = current_user.id

    # Fetch the part
    part = db.query(Part).filter(Part.id == product_id).first()
    if not part:
        return {"error": "Product not found"}
    
    if part.stock_quantity < quantity:
        return {"error": "Not enough stock"}
    
    # Fetch or create the cart
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    # Check if the item is already in the cart
    cart_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.part_id == product_id
    ).first()
    
    if cart_item:
        if part.stock_quantity >= cart_item.quantity + quantity:
            cart_item.quantity += quantity
        else:
            return {"error": "Not enough stock to add this quantity"}
    else:
        new_cart_item = CartItem(
            cart_id=cart.id,
            part_id=part.id,
            quantity=quantity
        )
        db.add(new_cart_item)
    
    # Reduce the stock
    part.stock_quantity -= quantity
    db.commit()
    
    return RedirectResponse(url="/cart", status_code=302)

@app.post("/update_cart/{item_id}")
async def update_cart_item(
    item_id: int,
    quantity: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RedirectResponse:
    # Fetch the cart item
    cart_item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not cart_item:
        return {"error": "Cart item not found"}

    # Fetch the associated part
    part = db.query(Part).filter(Part.id == cart_item.part_id).first()
    if not part:
        return {"error": "Associated part not found"}

    # Check stock availability
    if part.stock_quantity + cart_item.quantity < quantity:
        return {"error": "Not enough stock"}

    # Update the quantity
    part.stock_quantity += cart_item.quantity - quantity  # Restore stock for removed quantity
    cart_item.quantity = quantity

    db.commit()
    return RedirectResponse(url="/cart", status_code=302)


@app.post("/remove_from_cart/{item_id}")
async def remove_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RedirectResponse:
    # Fetch the cart item
    cart_item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not cart_item:
        return {"error": "Cart item not found"}

    # Fetch the associated part
    part = db.query(Part).filter(Part.id == cart_item.part_id).first()
    if part:
        part.stock_quantity += cart_item.quantity  # Restore stock

    # Remove the item from the cart
    db.delete(cart_item)
    db.commit()

    return RedirectResponse(url="/cart", status_code=302)



@app.get("/cart")
async def view_cart(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Dependency to get the authenticated user
) -> HTMLResponse:
    user_id = current_user.id
    
    # Fetch the user's cart
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart or not cart.items:
        return templates.TemplateResponse(
            "cart.html",
            {"request": request, "cart_items": [], "cart_total": 0}
        )

    # Calculate the total cost and prepare cart items
    cart_items = []
    total_cost = 0
    for item in cart.items:
        part = db.query(Part).filter(Part.id == item.part_id).first()
        if part:
            total_price = part.price * item.quantity
            total_cost += total_price
            cart_items.append({
                "id": item.id,
                "name": part.part_name,
                "image_url": part.photo_path or "/static/default_image.png",  # Replace with default image path
                "price": part.price,
                "quantity": item.quantity,
                "stock_quantity": part.stock_quantity,
                "part_name": part.part_name,
                "total_price": total_price,
            })
    
    return templates.TemplateResponse(
        "cart.html",
        {"request": request, "cart_items": cart_items, "cart_total": total_cost}
    )


car_facts = [
    "The first car was invented in 1886 by Karl Benz.",
    "There are over 1 billion cars in use worldwide.",
    "The world's fastest car is the Bugatti Chiron Super Sport 300+.",
    "75% of cars produced by Rolls-Royce are still on the road.",
    "Electric cars were invented before gasoline cars.",
    "The average car has about 30,000 parts.",
    "Speed is the ultimate thrill!",
    "Shift into high gear and feel the rush!",
    "Life is too short for slow cars.",
    "Drive fast, but drive safe!",
    "Four wheels move the body, but two wheels move the soul.",
    "Nothing beats the sound of a roaring engine!",
    "Fast cars, fast dreams!"
    "Mercedes is comfort, BMW is looks, but Audi is power! or something like that...",
    "The best car safety device is a rear-view mirror with a cop in it.",
    "Red and blue go whoo whoo whoo, but red and blue flashing lights mean you're screwed."
]


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)


# fastapi dev main_project/main.py



