import random
from sqlalchemy.orm import Session
from backend import Part, CarParameter

car_messages = [
    "Speed is the ultimate thrill!",
    "Shift into high gear and feel the rush!",
    "Life is too short for slow cars.",
    "Drive fast, but drive safe!",
    "Four wheels move the body, but two wheels move the soul.",
    "Nothing beats the sound of a roaring engine!",
    "Fast cars, fast dreams!",
]

def generate_html_content(db: Session):
    car_message = random.choice(car_messages)

    parts_list = db.query(Part).all()
    parts_html = "".join(
        f"<li>{part.part_name}: {part.description} - {part.price:.2f} {part.currency} | Stock: {part.stock_quantity} | Car: {part.part_parameters.car_name if part.part_parameters else 'N/A'}" +
        f"<form action='/remove_part/' method='post' style='display:inline; margin-left: 10px;'><input type='hidden' name='id' value='{part.id}' /><input type='password' name='admin_code' placeholder='Admin Code' required style='padding: 3px; width: 120px; margin-right: 5px;' /><button type='submit' style='padding: 3px 6px; background-color: #e74c3c; color: white; border: none; cursor: pointer; border-radius: 5px;'>Remove</button></form>" +
        (f"<br><img src='/static/uploaded_photos/disk_breakes_Meyle.jpg' alt='No Image' style='max-width: 200px; max-height: 200px; margin-top: 10px;'>" if part.photo_path else '') +
        "</li>" 
        for part in parts_list
    )

    part_parameters_list = db.query(CarParameter).all()
    part_parameters_html = "".join(
        f"<option value='{parameter.id}'>{parameter.car_name} ({parameter.year}) - {parameter.engine_type}</option>" for parameter in part_parameters_list
    )
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Auto Parts Inventory</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f0f0f0;
                margin: 40px;
                color: #333;
            }}
            h1 {{
                font-weight: bold;
                color: #e74c3c;
                border-bottom: 2px solid #333;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #f39c12;
            }}
            form {{
                margin-bottom: 20px;
                padding: 15px;
                background-color: #f7f7f7;
                border: 1px solid #ddd;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            label {{
                display: block;
                margin-bottom: 6px;
                color: #555;
                font-weight: bold;
            }}
            input[type="text"],
            input[type="number"],
            input[type="password"],
            select {{
                width: 90%;
                padding: 4px;
                margin-bottom: 8px;
                border: 1px solid #ccc;
                border-radius: 8px;
                font-size: 12px;
                height: auto;
            }}
            input[type="text"]:focus,
            input[type="number"]:focus,
            input[type="password"]:focus,
            select:focus {{
                border-color: #8e44ad;
                box-shadow: 0 0 5px rgba(142, 68, 173, 0.5);
                outline: none;
            }}
            button {{
                padding: 6px 10px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                transition: background-color 0.3s, transform 0.2s;
            }}
            button:hover {{
                background-color: #2980b9;
                transform: scale(1.05);
            }}
            ul {{
                list-style-type: none;
                padding-left: 0;
            }}
            li {{
                padding: 8px 0;
                border-bottom: 1px solid #ddd;
                color: #2c3e50;
            }}
            li:last-child {{
                border-bottom: none;
            }}
            .car-message {{
                font-size: 18px;
                font-weight: bold;
                color: #f39c12;
                margin-top: 20px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>Auto Parts Inventory</h1>
        <div class="car-message">{car_message}</div>
        <form action="/add_part/" method="post" enctype="multipart/form-data">
            <label for="name">Part Name</label>
            <input type="text" id="name" name="name" required>
            <label for="description">Description</label>
            <input type="text" id="description" name="description" required>
            <label for="price">Price</label>
            <input type="number" step="0.01" id="price" name="price" required>
            <label for="currency">Currency</label>
            <select id="currency" name="currency" required>
                <option value="" disabled selected>Select currency</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
            </select>
            <label for="stock_quantity">Stock Quantity</label>
            <input type="number" id="stock_quantity" name="stock_quantity" required>
            <label for="part_parameters">Part Parameters (Car)</label>
            <select id="part_parameters" name="part_parameters">
                <option value="" disabled selected>Select car</option>
                {part_parameters_html}
            </select>
            <label for="file">Upload Photo:</label>
            <input type="file" name="file" id="file"><br><br>
            <button type="submit">Add Part</button>
        </form>
        <h2>Available Parts</h2>
        <ul>
            {parts_html}
        </ul>
        <h2>Add Car Parameters</h2>
        <form action="/add_part_parameters/" method="post">
            <label for="car_name">Car Name</label>
            <input type="text" id="car_name" name="car_name" required>
            <label for="manufacturer">Manufacturer</label>
            <input type="text" id="manufacturer" name="manufacturer" required>
            <label for="year">Year</label>
            <input type="number" id="year" name="year" required>
            <label for="engine_type">Engine Type</label>
            <input type="text" id="engine_type" name="engine_type" required>
            <button type="submit">Add Parameters</button>
        </form>
    </body>
    </html>
    """