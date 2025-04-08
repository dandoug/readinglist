### Development metrics 
![Pylint Score](https://img.shields.io/endpoint?url=https://docs.booklist.media/reports/pylint.json)&nbsp;&nbsp;&nbsp;![Test Line Coverage](https://img.shields.io/endpoint?url=https://docs.booklist.media/reports/coverage.json)

# Reading List 

This is a project I use to manage a reading list of books I'm interested in.  I started with the books from the [Jack Carr reading list](https://www.amazon.com/shop/jackcarrusa/list/37WQJIYIWUHJF?ref_=cm_sw_r_cp_ud_aipsflist_PQE3BJ1TEY9FAW4707A8) on Amazon, but then I found others I wanted to add for my own interests.  It quickly grew beyond what I wanted to keep in a simple text file or even a spreadsheet.

I had this vision of being able to pull it while in a book store or library, filter it down to ones I'd like read next, maybe even easily link or search to the library or audiobook sources I use... there seemed no end of features.  It screamed to be made into an app. Since I wanted more practice with Python, I went with Flask. Similarly, I wanted more AWS experience, so I used AWS Elastic Beanstalk for provisioning, AWS RDS for the datastore, and various other AWS services -- favoring those simple enough to not require too much learning curve, but detailed enough to give me flexibility. 

Logging in as a user of the app allows you to save `read/up_next` status and `like/dislike` feedback about books.  This information is kept on a per-user basis.

# Set up

The app was built and tested locally on macOS Sequoia 15.3.2 using Python 3.11.11 (installed from pyenv 2.5.3, which in turn was installed with homebrew), but I try my best to avoid version and operating system dependencies wherever possible.

## Python Environment

From the project root, execute this (adjust for your platform)

```bash
$ python -m venv .venv
$ source .venv/bin/activate
$ python -m pip install --upgrade pip
$ pip install -r requirements.txt
```

## Execution Environment

There a file called [.env.sample](.env.sample) in the project root.  You should copy this and rename it to [.env]()   Edit the renamed file and set the environment variables in it to match your environment (read the comments in the file for more hints).  This file should never be checked into source control.  In a production environment, the environment variables set this way would typically be set externally and so this file probably wouldn't even exist.  It's intended for local development and testing.  In the production environment I use, this is done via AWS Secret Manager and loaded during deployment via [fetch_secrets.py](.ebextensions/fetch_secrets.py).

### Database schema

The DDL to create the database tables is in [books.sql](database/books.sql), [security.sql](database/security.sql), and [favorites.sql](database/favorites.sql).  The should be run to create the necessary tables in that order.

There's also a script [initial_book_load](database/initial_book_load.sql) that can load up about 200 books that I used to start.  You can use it or not to boot strap your collection.

### Users and Roles

The security model has two roles

* **admin** - can register and manage users and can delete books from the db
* **editor** - can add and edit books

A user need not have a role.  

All users, when logged in, can record `read/up_next` status and `like/dislike` feedback about books in the db and use those attributes to filter searches.

Registering a user requires an email address and a password (min 8 characters).  Before the user can login, the email address must be verfied by clicking a link that is sent to that address via email during registration.  The password can be changed via a `Forgot Password` function (which also relies on an email being sent.)  The email configuration is part of the environment.  

When the app starts, if there are no users defined with the `admin` role, a default one is created with email address `admin@example.com` and password `example1`.  If your installation is live on the internet somewhere, you should quickly create a non-default user with the `admin` role and delete `admin@example.com`.

### Running locally

Once the environment is installed, configured, and activated, the application can be run locally with

```bash
$ python run.py
```

The application will be available on [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Deployment to AWS Elastic Beanstalk

The files in [.ebextensions](.ebextensions) are for deploying to AWS Elastic Beanstalk and include certificate generation and installation by [certbot](https://eff-certbot.readthedocs.io/en/stable/using.html#certbot-command-line-options).  The deployed application is running at [https://booklist.media/](https://booklist.media/).




