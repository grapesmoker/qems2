QEMS2 - a question submission and editing system
=====

## What is it?

QEMS2 is a successor to a system called, intuitively enough, QEMS, which was used by [High School Academic Pyramidal Questions](www.hsapq.com) to produce quizbowl questions for various high school quizbowl competitions. The original QEMS was written in PHP and broke down after the maintainer stopped working on it; it was also completely hand-coded and made no use of modern web development frameworks or standards. QEMS2 is an attempt to remedy all that, by rebuilding the system from the ground up using modern tools.

## Stack

QEMS2 is based on a technology stack that uses MySQL for storage, Python (in the form of Django) for the backend, and jQuery/Bootstrap for frontend manipulations. 

## Installation

Grab the code:

        git clone https://github.com/grapesmoker/qems2


To run QEMS2 on a generic *nix (including OS X), you'll need the following prerequisites.

        python2 >= 2.7, MySQL, nodejs, npm

Once you have those installed, you should use `pip` to get the necessary Python packages

        sudo pip install django
        sudo pip install beautifulsoup4
        sudo pip install django-bower
        sudo pip install django-contrib-comments

It's generally recommended that you user `virtualenv` to set up a virtual environment for your project. 

Next, grab `bower` using `npm` for front-end package management:

        sudo npm install -g bower

Set up your MySQL connection as, for example, `mysql -u root -p`:

        create user django@localhost identified by 'django';
        create database qems2;
        grant all privileges on qems2.* to django@localhost;

Finally, use `manage.py` to populate the database, install the front-end packages, collect static files, and start the development server:

        python manage.py syncdb
        python manage.py bower install
        python manage.py collectstatic
        python manage.py runserver

As with any Django project, you should now be able to access the website at http://localhost:8000.
