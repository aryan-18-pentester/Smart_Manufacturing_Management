from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from ai_assistant import ask_ai
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError


# ── Setup ──────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ── User model ─────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    def __repr__(self):
        return f"<User {self.username}>"


#-----Data Model-----------------------
class Data(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)   
    price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


#-----Orders_Model------------
class Order(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    inventory_item_id = db.Column(db.Integer, nullable=False)
    quantity_item = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime, nullable=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text)


# --- 0Auth model-------------------
'''class OAuth(OAuthConsumerMixin, db.Model):
    __bind_key__ = 'orders'
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User)
'''


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Register ───────────────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password_hash=generate_password_hash(password))
        if user.query.filter_by(username=username).first():
            flash("Username already exists.")
            return redirect(url_for("register"))

# Create and save the new user
        new_user = User(username=username,
password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

# ── Login ──────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.')
    return render_template('login.html')


# ── Logout ─────────────────────────────────────────────────────────────────────
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', active='dashboard')



#----------Switch_User------------
@app.route('/switch_user',methods=['GET', 'POST'])
@login_required
def switch_user():
   # username = request.form['username']
   # print(request.form)
   # target_user = User.query.filter_by(username=username).first()
    if request.method == 'POST':
        print(request.form)
        user_id = request.form.get("user_id")
        
        if user_id is None:
            flash("No User Selected")
            return redirect(url_for("switch_user"))
        target_user = db.session.get(User, int(user_id))
        if target_user:
            login_user(target_user) 
            return redirect(url_for('dashboard'))
    accounts = User.query.all()
    return render_template('switch_user.html',accounts=accounts)



#-------------Ai-Assistant--------------
@app.route("/Ai_assistant", methods=["GET", "POST"])
@login_required
def Ai_assistant():

    answer = ""

    if request.method == "POST":

        question = request.form["question"]
        print('recieved question:', question)
        print('sending request to ollama ... ')

        answer = ask_ai(question)
        print("recieved response")

    return render_template(
        "Ai_assistant.html",
        answer=answer,
    )


#----------Machines-------------
@app.route('/Machines', methods=["GET", "POST"])
@login_required
def Machines():
    user = User.query.filter_by(username=current_user.username).first()
    if not user:  # Still handle the case where a user isn't found
        user = User(username=current_user.username, password_hash=generate_password_hash('password')) # Re-establish if no initial user
        db.session.add(user)
        db.session.commit()
    
    per_page = 4  # Number of items per page
    total_items = Data.query.count()
    total_pages = (total_items + per_page - 1) // per_page

    low_stock = Data.query.filter(Data.quantity < 10).count()
    result = db.session.query(func.sum(Data.quantity * Data.price)).scalar()
    total_value = result if result is not None else 0.0

    if request.method == "POST":
        item_id = request.form.get("item_id")
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price')

        if item_id:
            record = Data.query.filter_by(id=item_id).first_or_404()
            record.name = name
            record.quantity = quantity
            record.price = price
        else:
            record = Data(name=name, quantity=quantity,
                          price=price, user_id=current_user.id)
            db.session.add(record)

        print(request.form)
    page = request.args.get('page', 1, type=int)  # Corrected this line
    data = Data.query.filter_by(user_id=user.id).paginate(page=request.args.get(
 'page', 1, type=int), per_page=per_page)
    db.session.commit()

    return render_template('Machines.html', inventory=data, total_items=total_items, low_stock=low_stock, total_value=total_value, page=page, total_pages=total_pages)



#-------------delete-----------
@app.route('/delete/<int:id>', methods=['POST'])
def delete_record(id):
    # 1. Fetch the record by ID
    record = Data.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    # 2. Delete from session
    db.session.delete(record)
    
    # 3. Commit to database
    db.session.commit()
    
    # 4. Redirect to prevent re-submission on refresh
    return redirect(url_for('Machines'))   


#--------Orders--------------------
@app.route('/orders', methods=['GET', 'POST'])
@login_required
def orders():

    if request.method == 'POST':

        customer_name = request.form.get('customer_name')

        inventory_item_id = request.form.get('inventory_item_id', type=int)

        print("inventory_item_id =", inventory_item_id)

        quantity_item = request.form.get('quantity', type=int)

        unit_price = request.form.get('unit_price', type=float)

        due_date_str = request.form.get('date')

        notes = request.form.get('notes')
        


        due_date = (
            datetime.strptime(due_date_str, '%Y-%m-%d')
            if due_date_str else None
        )

        order = Order(
            customer_name=customer_name,
            inventory_item_id=inventory_item_id,
            quantity_item=quantity_item,
            unit_price=unit_price,
            due_date=due_date,
            notes=notes,
            user_id=current_user.id
        )

        db.session.add(order)
        db.session.commit()

        flash('Order created successfully', 'success')

        return redirect(url_for('orders'))

    orders_data = Order.query.filter_by(user_id=current_user.id).all()
    inventory_items = Data.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'Orders.html',
        orders=orders_data,
        machines=inventory_items
    )


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
