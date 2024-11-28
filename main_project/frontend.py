import random
from sqlalchemy.orm import Session
from db_models import Part, CarParameter


car_messages = [
    "Speed is the ultimate thrill!",
    "Shift into high gear and feel the rush!",
    "Life is too short for slow cars.",
    "Drive fast, but drive safe!",
    "Four wheels move the body, but two wheels move the soul.",
    "Nothing beats the sound of a roaring engine!",
    "Fast cars, fast dreams!"
    "Mercedes is comfort, BMW is looks, but Audi is power! or something like that...",
    "The best car safety device is a rear-view mirror with a cop in it.",
    "Red and blue go whoo whoo whoo, but red and blue flashing lights mean you're screwed.",
]

def generate_html_content(db: Session):
    car_message = random.choice(car_messages)

    parts_list = db.query(Part).all()
    parts_html = "".join(
        f"<li>{part.part_name}: {part.description} - {part.price:.2f} {part.currency} | Stock: {part.stock_quantity} | Car: {part.part_parameters.car_name if part.part_parameters else 'N/A'}" +
        f"<form action='/remove_part/' method='post' style='display:inline; margin-left: 10px;'><input type='hidden' name='id' value='{part.id}' /><input type='password' name='admin_code' placeholder='Admin Code' required style='padding: 3px; width: 120px; margin-right: 5px;' /><button type='submit' style='padding: 3px 6px; background-color: #e74c3c; color: white; border: none; cursor: pointer; border-radius: 5px;'>Remove</button></form>" +
        (f"<br><img src='/static/{part.photo_path}' alt='No Image' style='max-width: 200px; max-height: 200px; margin-top: 10px;'>" if part.photo_path else '') +
        "</li>" 
        for part in parts_list
    )

    part_parameters_list = db.query(CarParameter).all()
    part_parameters_html = "".join(
        f"<option value='{parameter.id}'>{parameter.car_name} ({parameter.year}) - {parameter.engine_type}</option>" for parameter in part_parameters_list
    )
    return f"""
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto Parts Inventory</title>
    <style>
        /* Background Styling */
        body {{
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #eaf2f8, #d6eaf8, #f4ecf7);
            color: #333;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }}

        /* Main Container */
        .container {{
            width: 90%;
            max-width: 800px;
        }}

        /* Header Styling */
        h1 {{
            color: #e74c3c;
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 3px solid rgba(51, 51, 51, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        /* Adding Icon to Header */
        h1::before {{
            content: '🚗';
            font-size: 2.5rem;
            margin-right: 10px;
        }}

        h2 {{
            color: #3498db;
            font-size: 1.6rem;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
        }}

        /* Adding Icons to Sub-Headers */
        h2::before {{
            content: '🔧';
            margin-right: 8px;
        }}

        /* Form Styling */
        form {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            transition: transform 0.3s, box-shadow 0.3s;
            border-left: 8px solid #3498db;
            border-right: 8px solid #e74c3c;
        }}

        form:hover {{
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            transform: translateY(-5px);
        }}

        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }}

        input[type="text"],
        input[type="number"],
        input[type="file"],
        select {{
            width: 100%;
            padding: 10px;
            margin-bottom: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.2s, box-shadow 0.2s;
            background-color: rgba(245, 245, 245, 0.9);
        }}

        input:focus,
        select:focus {{
            border-color: #8e44ad;
            box-shadow: 0 0 6px rgba(142, 68, 173, 0.3);
            outline: none;
        }}

        /* Button Styling */
        button {{
            display: inline-block;
            padding: 12px 15px;
            font-size: 14px;
            color: #fff;
            background: linear-gradient(135deg, #3498db, #2980b9);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.3s, transform 0.2s;
            width: 100%;
            font-weight: bold;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            letter-spacing: 1px;
            text-transform: uppercase;
        }}

        button:hover {{
            background: linear-gradient(135deg, #2980b9, #3498db);
            transform: scale(1.05);
        }}

        /* List Styling */
        ul {{
            list-style-type: none;
            padding-left: 0;
            margin-top: 0;
            color: #333;
            background-color: rgba(255, 255, 255, 0.85);
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        }}

        li {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
            color: #2c3e50;
            display: flex;
            align-items: center;
        }}

        li:last-child {{
            border-bottom: none;
        }}

        li::before {{
            content: '🛠️';
            margin-right: 10px;
        }}

        /* Car Message Styling */
        .car-message {{
            font-size: 1.2rem;
            font-weight: bold;
            color: #e67e22;
            text-align: center;
            padding: 12px;
            margin-bottom: 20px;
            background-color: rgba(253, 242, 233, 0.9);
            border-radius: 8px;
            border: 1px solid #f5cba7;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            animation: fadeIn 1s ease-in-out;
        }}

        /* Fade-in Animation */
        @keyframes fadeIn {{
            from {{
                opacity: 0;
            }}
            to {{
                opacity: 1;
            }}
        }}

        /* Additional Section Styling */
        .form-section {{
            margin-top: 30px;
            margin-bottom: 20px;
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .form-section:hover {{
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
            transform: translateY(-3px);
        }}
    </style>
</head>

<body>
    <div class="container">
        <header>
            <h1>Auto Parts Inventory</h1>
        </header>

        <section class="form-section">
            <div class="car-message">{car_message}</div>

            <!-- Add Part Form -->
            <h2>Add Part</h2>
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
                <input type="file" name="file" id="file">

                <button type="submit">Add Part</button>
            </form>
        </section>

        <section class="form-section">
            <h2>Available Parts</h2>
            <ul>
                {parts_html}
            </ul>
        </section>

        <section class="form-section">
            <h2>Add Car Parameters</h2>

            <!-- Add Car Parameters Form -->
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
        </section>
    </div>
</body>

</html>
    """