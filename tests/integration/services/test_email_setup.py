
SUBJECT = "Welcome to bookllist!"
BODY = """
Hello user!  Welcome to booklist.  
You must be smart."""
FROM = "admin@localhost"
MAILBOX = "user"
MAILBOX_PASSWORD = ""
TO = MAILBOX + "@localhost"

def test_send_email_and_receive(smtp_connection, pop_connection):
    """Test sending and receiving an email."""
    from email.mime.text import MIMEText

    # Send an email
    msg = MIMEText(BODY)
    msg["Subject"] = SUBJECT
    msg["From"] = FROM
    msg["To"] = TO

    smtp_connection.send_message(msg)

    # Check it in the POP mailbox
    pop_connection.user(MAILBOX)
    pop_connection.pass_(MAILBOX_PASSWORD)

    email_count = len(pop_connection.list()[1])
    assert email_count > 0

    # Retrieve emails and verify content
    for i in range(1, email_count + 1):
        _, email_lines, _ = pop_connection.retr(i)
        email_content = b"\n".join(email_lines).decode("utf-8")
        assert BODY in email_content
        assert SUBJECT in email_content
