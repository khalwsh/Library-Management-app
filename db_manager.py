from validate_fields import *
from book import *
from User import *

def check_user_exist(username, password, cursor):
    cursor.execute(f"select user_name from user where user_name = \"{username}\" and password = \"{password}\"")
    return len(cursor.fetchall()) == 1


def insert_user(user_name_input_text, password_input_text, fname_input_text, lname_input_text, email_input_text,
                Address_input_text, Phone_input_text, cursor, connection):
    try:
        cursor.execute(
            f"INSERT INTO user (fname, lname, email, user_name, password , Address) "
            f"VALUES ('{fname_input_text}', '{lname_input_text}', '{email_input_text}', '{user_name_input_text}', '{password_input_text}' , '{Address_input_text}');"
        )
        connection.commit()

        cursor.execute(f"SELECT id FROM user where user_name = '{user_name_input_text}';")
        user_id = cursor.fetchone()[0]
        cursor.execute(f"INSERT INTO phones (user_id , phone_number) VALUES ('{user_id}', '{Phone_input_text}');")
        connection.commit()

        print(f"{cursor.rowcount} record(s) inserted successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        connection.rollback()


def check_create_user(user_name_text, password_text, fname_text, lname_text, email_text, Address_text, Phone_text,
                      cursor):
    '''
      first we want to check that no field in null or empty
      we want to check that the user name is unique and didn't exist in the database.
      we want to check that the password is strong with certain criteria
      we want to ensure email belong to certain domain @ exist
      Address must contain numbers then locations
      phone number must be 11 or 13 if you have the country code but if it was 13 then first letter is +
      return error message
    '''
    # all fields are not empty
    if len(user_name_text) == 0 or len(password_text) == 0 or len(fname_text) == 0 or len(lname_text) == 0 or len(
            email_text) == 0 or len(Address_text) == 0 or len(Phone_text) == 0:
        return "Not complete"

    # user_name check
    cursor.execute(f"select user_name from user where user_name = \"{user_name_text}\";")
    if len(cursor.fetchall()) != 0:
        return "User already exists"

    # password strength
    [valid, error] = check_password(password_text)
    if not valid:
        return error

    # check email
    if email_text.find("@") == -1:
        return "Email not belong to a certain domain"

    # Address check
    [valid, error] = check_address(Address_text)
    if not valid:
        return error

    [valid, error] = check_phone(Phone_text)
    if not valid:
        return error

    return None

def load_user(current_user_name, cursor):
    # Use parameterized query to prevent SQL injection
    cursor.execute("SELECT * FROM user WHERE user_name = %s", (current_user_name,))
    user_data = cursor.fetchone()

    if not user_data:
        return None

    id, fname, lname, email, user_name, password, Address = user_data
    # Get phone numbers
    cursor.execute("SELECT phone_number FROM phones WHERE user_id = %s", (id,))
    phones = [phone[0] for phone in cursor.fetchall()]

    # Get borrowed books
    cursor.execute("SELECT book_id FROM borrowed WHERE user_id = %s", (id,))
    books_ids = [book_id[0] for book_id in cursor.fetchall()]

    borrowed_books = []
    for book_id in books_ids:
        cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        book_data = cursor.fetchone()
        if book_data:
            ibook_id, title, author, status, pages = book_data
            borrowed_books.append(Book(ibook_id, title, author, status, pages))  # Note: Changed 'book' to 'Book'
    return User(user_name, password, id, email, fname, lname, Address, phones, borrowed_books)

def insert_phone(id, text, cursor, connection):
    try:
        cursor.execute(f"select * from phones where phone_number = '{text}' and user_id = '{id}';")
        if len(cursor.fetchall()) != 0:
            return
        cursor.execute(
            f"INSERT INTO phones (user_id, phone_number) VALUES ('{id}', '{text}');"
        )
        connection.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        connection.rollback()

def delete_phone(id , text , cursor , connection):
    try:
        cursor.execute(
            f"delete from phones WHERE phone_number = '{text}' AND user_id = '{id}';"
        )
        connection.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        connection.rollback()

def return_book(user_id , book_id , cursor , connection):
    try:
        cursor.execute(
            f"delete from borrowed WHERE user_id = '{user_id}' AND book_id = '{book_id}';"
        )
        connection.commit()
        cursor.execute("update books set status = 1 where id = %s", (book_id,))
        connection.commit()
    except Exception as e:
            print(f"An error occurred: {e}")
            connection.rollback()

def get_available_books(cursor):
    cursor.execute("select * from books where status = 1;")
    all = cursor.fetchall()
    books = []
    for book in all:
        id , title, author, status, pages = book
        books.append(Book(id, title, author, status, pages))
    return books

def borrow_book(user_id, book_id, cursor, connection):
    try:
        # Check if the book exists and its status is available (status = 1)
        cursor.execute("SELECT COUNT(*) FROM books WHERE id = %s AND status = 1", (book_id,))
        book_available = cursor.fetchone()[0]

        if not book_available:
            print("The book is either unavailable or does not exist.")
            return

        # Insert a new record into the borrowed table with the calculated end_date
        cursor.execute(
            """
            INSERT INTO borrowed (user_id, book_id, end_date)
            VALUES (%s, %s, CURRENT_TIMESTAMP + INTERVAL 10 DAY)
            """,
            (user_id, book_id)
        )
        connection.commit()

        # Update the book's status to unavailable (status = 0)
        cursor.execute("UPDATE books SET status = 0 WHERE id = %s", (book_id,))
        connection.commit()

        print("Book borrowed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        connection.rollback()

def insert_book(title , author , pages, cursor, connection):
    try:
        cursor.execute(
            f"insert into books(title , author, pages) values ('{title}', '{author}', '{pages}');"
        )
        connection.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        connection.rollback()

def delete_book(id , cursor , connection):
    try:
        cursor.execute(
            f"delete from books where id = %s", (id,)
        )
        connection.commit()
    except Exception as e:
        print("this book is not currently in the library")
        print(f"An error occurred: {e}")
        connection.rollback()

def get_all_users(cursor):
    cursor.execute("select * from user")
    all = cursor.fetchall()
    user_list = []
    for user in all:
        id, fname, lname, email, user_name, password, Address = user
        password = len(password) * '*'
        cursor.execute(f"select phone_number from phones WHERE user_id = '{id}';")
        phones = [phone[0] for phone in cursor.fetchall()]
        cursor.execute(f"select book_id from borrowed WHERE user_id = '{id}';")
        books_ids = cursor.fetchall()
        borrowed_books = []
        for book_id in books_ids:
            cursor.execute("SELECT * FROM books WHERE id = %s", (book_id[0],))
            book_data = cursor.fetchone()
            if book_data:
                book__id, title, author, status, pages = book_data
                borrowed_books.append(Book(book__id, title, author, status, pages))

        user_list.append(User(user_name, password, id, email, fname, lname, Address, phones, borrowed_books))
    return user_list

def get_borrowed_books(cursor):
    # Get all borrowed books (status = 0 means borrowed)
    cursor.execute("""
        SELECT books.id, books.title, books.author, books.status, books.pages,
               borrowed.start_date, borrowed.end_date
        FROM books 
        JOIN borrowed ON books.id = borrowed.book_id
        WHERE books.status = 0;
    """)

    books = []
    for row in cursor.fetchall():
        book_id, title, author, status, pages, start_date, end_date = row
        book = Book(book_id, title, author, status, pages)
        books.append([book, start_date, end_date])

    return books

def delete_user(id , cursor , connection):
    try:
        cursor.execute(f"update books set status = 1 where id in (select book_id from borrowed where user_id = '{id}');" )

        cursor.execute(
            f"delete from borrowed WHERE user_id = '{id}';"
        )

        cursor.execute(
            f"delete from phones where user_id = '{id}';"
        )
        cursor.execute(
            f"delete from user where id = %s", (id,)
        )
        connection.commit()
    except Exception as e:
        print("this book is not currently in the library")
        print(f"An error occurred: {e}")
        connection.rollback()