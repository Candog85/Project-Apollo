# All imports
from flask import Flask, render_template, request, redirect, flash, abort
import pymysql
from dynaconf import Dynaconf
import flask_login

# Declare Flask application
app = Flask(__name__)


# Config settings
conf = Dynaconf(
    settings_file = ["settings.toml"]
)

# Config secret key
app.secret_key = conf.secret_key

# Establish database connection
def connect_db():
    """Connect to the phpMyAdmin database (LOCAL STEAM NETWORK ONLY)"""
    conn = pymysql.connect(
        host = "10.100.34.80",
        database = "fchowdury_proquipment_store",
        user = "fchowdury",
        password = conf.password,
        autocommit = True,
        cursorclass = pymysql.cursors.DictCursor
    )
    return conn


# User Login Manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view=("/login")


# Classes
class User:
    is_authenticated = True
    is_anonymous = False
    is_active = True

    def __init__(self, user_id, username, email, first_name, last_name):
        self.id = user_id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

    def get_id(self):
        return str(self.id)


# Load User Session
@login_manager.user_loader
def load_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `Customer` WHERE `id` = {user_id};")
    result = cursor.fetchone()
    cursor.close()
    conn.close
    if result is not None:
        return User(result["id"], result["username"], result["email"], result["first_name"], result["last_name"])


# Homepage initialization
@app.route("/")
def index():
    return render_template("homepage.html.jinja")


# Browse products
@app.route("/browse")
def product_browse():
    query = request.args.get("query")
    conn = connect_db()
    cursor = conn.cursor()
    if query is None:
        cursor.execute("SELECT * FROM `Product`;")
    else:
        cursor.execute(f"SELECT * FROM `Product` WHERE `name` LIKE '%{query}%' OR `description` LIKE '%{query}%' OR `price` LIKE '%{query}%';")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("browse.html.jinja", products = results)


# Separate page per product
@app.route("/product/<product_id>")
def product_details(product_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Retrieve product details (optional, assuming it's part of the page)
    cursor.execute("""
        SELECT * FROM Product WHERE id = %s
    """, (product_id,))
    product = cursor.fetchone()

    # Retrieve reviews along with full name of the customer
    cursor.execute("""
        SELECT 
            Review.review, 
            Review.rating AS rating_stars, 
            Review.timestamp, 
            CONCAT(Customer.first_name, ' ', Customer.last_name) AS user_name
        FROM Review
        JOIN Customer ON Review.customer_id = Customer.id
        WHERE Review.product_id = %s
        ORDER BY Review.timestamp DESC
    """, (product_id,))
    reviews = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("product.html.jinja", product=product, reviews=reviews)

# Review handler
@app.route("/product/<product_id>/review", methods=["POST"])
@flask_login.login_required
def add_review(product_id):
    review = request.form.get("review")
    rating = int(request.form.get("rating"))
    customer_id = flask_login.current_user.id

    conn = connect_db()
    cursor = conn.cursor()

    # Insert review and rating into the database
    cursor.execute("""
        INSERT INTO Review (customer_id, product_id, review, rating, timestamp)
        VALUES (%s, %s, %s, %s, NOW())
    """, (customer_id, product_id, review, rating))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(f"/product/{product_id}")


# Add item to cart
@app.route("/product/<product_id>/cart", methods=["POST"])
@flask_login.login_required
def add_to_cart(product_id):
    quantity = request.form["quantity"]
    customer_id = flask_login.current_user.id
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"""
    INSERT INTO `Cart`
        (`customer_id`, `product_id`, `quantity`)
    VALUES
        ({customer_id}, {product_id}, {quantity})
    ON DUPLICATE KEY UPDATE
        `quantity` = `quantity` + {quantity}
    """)
    cursor.close()
    conn.close()
    return redirect("/cart")


# Sign up page
@app.route("/signup", methods=["POST", "GET"])
def signup_page():
    if flask_login.current_user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        first_name = request.form["fname"]
        last_name = request.form["lname"]
        email = request.form["email"]
        address = request.form["address"]
        username = request.form["username"]
        password = request.form["pass"]
        confirm_password = request.form["confpass"]
        conn = connect_db()
        cursor = conn.cursor()
        if len(username.strip()) > 20:
            flash("Username must be 20 characters or less.")
        else:
            if len(password.strip()) < 8:
                flash("Password must be 8 characters or longer.")
            else:
                if password != confirm_password:
                    flash("Passwords do not match.")
                else:
                    try:
                        cursor.execute(f"""
                            INSERT INTO `Customer`
                                (`username`, `password`, `first_name`, `last_name`, `email`, `address`)
                            VALUES
                                ('{username}', '{password}', '{first_name}', '{last_name}', '{email}', '{address}');
                        """)
                    except pymysql.err.IntegrityError:
                        flash("Username or email is already in use.")
                    else:
                        return redirect("/login")
                    finally:
                        cursor.close()
                        conn.close()
    return render_template("signup.html.jinja")


# Login Page
@app.route("/login", methods=["POST", "GET"])
def login_page():
    if flask_login.current_user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        username = request.form["userVer"].strip()
        password = request.form["passVer"]
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM `Customer` WHERE `username` = '{username}';")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result is None:
            flash("Your username and/or password is incorrect.")
        
        elif password != result["password"]:
            flash("Your username and/or password is incorrect.")
        
        else:
            user = User(result["id"], result["username"], result["email"], result["first_name"], result["last_name"])

            #Loging In
            flask_login.login_user(user)

            return redirect("/")

    return render_template("login.html.jinja")


# Cart Page
@app.route("/cart", methods=["GET"])
@flask_login.login_required
def cart_page():
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id
    cursor.execute(f"""
        SELECT
            `name`,
            `price`,
            `Cart`.`quantity`,
            `image`,
            `product_id`,
            `Cart`.`id`
        FROM `Cart` 
        JOIN `Product` on `product_id` = `Product`.`id` 
        WHERE `customer_id` = {customer_id};
    """)
    results = cursor.fetchall()
    total = 0

    if len(results) > 0:
        for item in results:
            total += (item["price"] * item["quantity"])
        total = round(total, 2)
    cursor.close()
    conn.close()
    return render_template("cart.html.jinja", cartContents = results, sum = total)


# Remove item from Cart
@app.route("/cart/remove_cart", methods=["POST"])
@flask_login.login_required
def remove_cart():
    conn = connect_db()

    cursor = conn.cursor()

    customer_id = flask_login.current_user.id

    cart_id = request.form["id"]

    cursor.execute(f"""
    DELETE FROM `Cart`
    WHERE
        `customer_id` = {customer_id}
    AND
        `Cart`.`id` = {cart_id};
    """)

    
    cursor.close()
    conn.close()

    return redirect("/cart")


# Update Item Quantity in Cart
@app.route("/cart/<cart_id>/update", methods=["POST"])
@flask_login.login_required
def update_cart(cart_id):
    conn = connect_db()

    cursor = conn.cursor()

    new_qty = request.form["quantity"]

    cursor.execute(f"""
    UPDATE `Cart`
    SET `quantity` = {new_qty}
    WHERE `id` = {cart_id}
    ;""")

    
    cursor.close()
    conn.close()

    return redirect("/cart")

# Checkout page
@app.route("/checkout", methods=["GET"])
@flask_login.login_required
def checkout():
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id

    cursor.execute(f"""
        SELECT
            `name`,
            `price`,
            `Cart`.`quantity`,
            `image`,
            `product_id`,
            `Cart`.`id`
        FROM `Cart` 
        JOIN `Product` on `product_id` = `Product`.`id` 
        WHERE `customer_id` = {customer_id};
    """)

    # Fetch cart items
    results = cursor.fetchall()

    if len(results) == 0:
        return redirect("/browse")
    
    else:
        subtotal = 0
        for item in results:
            subtotal += (item["price"] * item["quantity"])
        
        # Calculate taxes (10%) and shipping fees ($5)
        # Insert any tax rate and shipping charge
        tax_rate = 0.10
        shipping_fee = 5.00
        tax = round(subtotal * tax_rate, 2)
        total = round(subtotal + tax + shipping_fee, 2)
    
    # Fetch user info
    cursor.execute(f"""
        SELECT * FROM `Customer`
        WHERE `id` = {customer_id}
    ;""")
    consumer = cursor.fetchone()

    # Close connections
    cursor.close()
    conn.close()

    return render_template(
        "checkout.html.jinja", 
        cartContents=results, 
        subtotal=subtotal, 
        tax=tax, 
        shipping=shipping_fee, 
        total=total, 
        customer=consumer
    )

@app.route("/checkout/sale")
@flask_login.login_required
def create_sale():
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Get the current customer's ID
        customer_id = flask_login.current_user.id

        # Verify if the customer exists and fetch their address
        cursor.execute("SELECT `address` FROM `Customer` WHERE `id` = %s;", (customer_id,))
        result = cursor.fetchone()
        if not result:
            return "Customer not found", 404

        address = result["address"]

        # Insert a new sale record
        cursor.execute("""
            INSERT INTO `Sale` (`customer_id`, `address`, `status`)
            VALUES (%s, %s, %s);
        """, (customer_id, address, "Placed"))

        # Get the last inserted sale ID
        sale_id = cursor.lastrowid

        # Fetch products from the cart
        cursor.execute("SELECT * FROM `Cart` WHERE `customer_id` = %s;", (customer_id,))
        products = cursor.fetchall()

        # Insert products into the Sale_Product table
        for product in products:
            cursor.execute("""
                INSERT INTO `Sale_Product` (`sale_id`, `product_id`, `quantity`)
                VALUES (%s, %s, %s);
            """, (sale_id, product["product_id"], product["quantity"]))

        # Commit transaction
        conn.commit()

    except pymysql.err.IntegrityError as e:
        conn.rollback()
        return f"Database error: {e}", 500
    except Exception as e:
        conn.rollback()
        return f"Error: {e}", 500
    finally:
        cursor.close()
        conn.close()

    return redirect("/thankyou")


@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html.jinja")

@app.route("/orders")
@flask_login.login_required
def order_history():
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id

    # Use parameterized queries
    cursor.execute("""
        SELECT
            `Sale`.`id` AS `sale_id`,
            `Sale`.`status`,
            `Sale_Product`.`product_id`,
            `Product`.`name`,
            `Product`.`price`,
            `Sale_Product`.`quantity`
        FROM `Sale` 
        JOIN `Sale_Product` ON `Sale`.`id` = `Sale_Product`.`sale_id`
        JOIN `Product` ON `Sale_Product`.`product_id` = `Product`.`id`
        WHERE `Sale`.`customer_id` = %s;
    """, (customer_id,))

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("orders.html.jinja", orders=results)