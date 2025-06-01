from flask import Flask, render_template, request, redirect, url_for, session as flask_session
from sqlalchemy import create_engine, ForeignKey, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

app = Flask(__name__)
app.secret_key = 'your_secret_key' #needed for creating sessions

Base = declarative_base()
engine = create_engine("sqlite:///mydb.db", echo=True)
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    member = Column(Integer)
    persons = relationship("Person", back_populates="user")

    def __init__(self, username, password, member):
        self.username = username
        self.password = password
        self.member = member

    def __repr__(self):
        return f"User(id={self.id}, username='{self.username}' username='{self.member}')"

class Person(Base):
    __tablename__ = "people"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    adult = Column(Integer)
    student = Column(Integer)
    child = Column(Integer)
    infant = Column(Integer)
    user = relationship("User", back_populates="persons")

    def __init__(self, user_id, adult, student, child, infant):
        self.user_id = user_id
        self.adult = adult
        self.student = student
        self.child = child
        self.infant = infant

    def __repr__(self):
        return (f"Person(id={self.id}, user_id={self.user_id}, adult={self.adult}, "
                f"student={self.student}, child={self.child}, infant={self.infant})")

Base.metadata.create_all(bind=engine)

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/visit')
def visit():
    return render_template('visit.html')

@app.route('/conservation')
def conservation():
    return render_template('conservation.html')

@app.route('/login')
def login():
    return render_template('book_login.html')

@app.route('/join_main')
def join_main():
    return render_template('join_main.html')

@app.route('/book_main')
def book_main():
    return render_template('book_main.html')

@app.route('/join_signup', methods=['GET', 'POST'])
def join_signup():
    if request.method == 'POST':
        session = Session()
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            member = 1

            if not email or not password:
                return render_template('join_signup.html', error="Please enter all fields.")

            # Check if user exists
            user = session.query(User).filter_by(username=email).first()
            if not user:
                user = User(username=email, password=password, member=member)
                session.add(user)
                session.commit()

            new_person = Person(user_id=user.id)
            session.add(new_person)
            session.commit()

            # Store user ID in session after successful signup
            flask_session['user_id'] = user.id

            return redirect(url_for('book_ticket'))  # Redirect to booking page

        except Exception as e:
            session.rollback()
            return render_template('join_signup.html', error="An unexpected error occurred.")
        finally:
            session.close()

    return render_template('join_signup.html')

@app.route('/book_signup', methods=['GET', 'POST'])
def book_signup():
    if request.method == 'POST':
        session = Session()
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            member = 0

            if not email or not password:
                return render_template('book_signup.html', error="Please enter all fields.")

            # Check if user exists
            user = session.query(User).filter_by(username=email).first()
            if not user:
                user = User(username=email, password=password, member=member)
                session.add(user)
                session.commit()

            new_person = Person(user_id=user.id)
            session.add(new_person)
            session.commit()

            # Store user ID in session after successful signup
            flask_session['user_id'] = user.id

            return redirect(url_for('book_ticket'))  # Redirect to booking page

        except Exception as e:
            session.rollback()
            return render_template('book_signup.html', error="An unexpected error occurred.")
        finally:
            session.close()
            return render_template('book_main.html')

    return render_template('book_signup.html')

@app.route('/book_login', methods=['GET', 'POST'])
def book_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Use session to check user
        with Session() as session:
            user = session.query(User).filter_by(username=email).first()

            if user and user.password == password:
                # Store user ID in session
                flask_session['user_id'] = user.id
                return redirect(url_for('book_ticket'))

            return render_template('book_login.html', error="Invalid email or password.")

    return render_template('book_login.html')

@app.route('/book_ticket', methods=['GET', 'POST'])
def book_ticket():
    if 'user_id' not in flask_session:
        return redirect(url_for('book_login'))  # Redirect to login if no user is logged in

    session = Session()
    user_id = flask_session['user_id']  # Get user ID from session
    user = session.query(User).get(user_id)

    if request.method == 'POST':
        try:
            adult = int(request.form.get('Adults', 0))
            student = int(request.form.get('student', 0))
            child = int(request.form.get('child', 0))
            infant = int(request.form.get('infant', 0))

            # Ensure at least one ticket is selected
            if adult == 0 and student == 0 and child == 0 and infant == 0:
                return render_template('book_ticket.html', title="Error", text="Please select at least one ticket.")

            new_person = Person(user_id=user.id, adult=adult, student=student, child=child, infant=infant)
            session.add(new_person)
            session.commit()

            # Store ticket data in session
            flask_session['ticket_info'] = {
                'adult': adult,
                'student': student,
                'child': child,
                'infant': infant
            }

            return redirect(url_for('paymentpage'))  # Redirect to payment page

        except Exception as e:
            session.rollback()
            return render_template('book_ticket.html', title="Error", text="An unexpected error occurred.")
        finally:
            session.close()  # Close session

    return render_template('book_ticket.html', user=user)


@app.route('/paymentpage', methods=['GET', 'POST'])
def paymentpage():
    # Retrieve ticket data from session
    ticket_info = flask_session.get('ticket_info', None)
    adult_tickets = ticket_info['adult']
    student_tickets = ticket_info['student']
    child_tickets = ticket_info['child']
    infant_tickets = ticket_info['infant']

    #maths for the total cost in money
    adulttotal=adult_tickets*15
    studenttotal=student_tickets*10
    childtotal=child_tickets*5
    infanttotal=infant_tickets*2
    
    total_tickets = adulttotal + studenttotal + childtotal + infanttotal
  
    if not ticket_info:
        return redirect(url_for('book_ticket'))  # Redirect to book ticket page if no ticket info is available

    return render_template('paymentpage.html', ticket_info=ticket_info, total_tickets=total_tickets)
 
 
if __name__ == '__main__':
    app.run(debug=True)
