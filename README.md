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

## Usage

QEMS2 is currently in heavy development. Although the core parts of the application are stable, features are being added all the time, so it's hard to give an exhaustive description of them all here. The foregoing will summarize the basic concepts involved in the question submission and editing workflow.

### Roles

QEMS2 is structured around the concept of roles. There are three types of roles in the system: owners, editors, and writers (there are also administrators who can access the admin site, but that is not strictly speaking a part of the application itself). The hierarchy of powers is strictly inclusive from the top down, i.e. anything that an editor can do, an owner can do, and anything that a writer can do, an editor can do.

1. Owners: Anyone who creates a tournament is automatically the owner of that tournament and has complete freedom to do anything they would like to it. This includes assigning other users to be editors or writers of their tournament, modifying the tournament distribution, and editing any question in the system.
2. Editors: these users have the power to edit or delete any question in the system. They do not have the power to change the distribution or the core information about the set. Editors can also lock questions to prevent writers from editing those questions.
3. Writers: these users are empowered only to submit questions, edit (unlocked) questions that they have submitted, and see (but not edit) questions submitted by others.

In addition, any user can leave comments on packets, individual questions, or the set as a whole.

