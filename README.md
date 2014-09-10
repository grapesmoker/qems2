QEMS2
=====

quizbowl submission system

To run this on generic *nix (including OS X):

1. Required: `python2 >= 2.7, django >= 1.6, pip, MySQL, nodejs, beautifulsoup4`

2. Execute the following in the directory of your choice:

        git clone https://github.com/grapesmoker/qems2
        cd qems2/
        sudo pip install django-debug-toolbar
        sudo pip install django-bower
        sudo pip install django.contrib.comments
        sudo npm install -g bower

3. Using MySQL as, for example, `mysql -u root -p`:

        create user django@localhost identified by 'django';
        create database qems2;
        grant all privileges on qems2.* to django@localhost;

4. Lastly, set everything up:

        python manage.py syncdb
        python manage.py bower install
        python manage.py runserver
