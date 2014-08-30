QuEST
=====

quizbowl submission system

To run this on a generic *nix (including OS X):

Make sure python, django, and MySQL are installed.

```
git clone https://github.com/grapesmoker/qems2
cd qems2/
sudo pip install django-debug-toolbar
sudo pip install django-bower
sudo npm install -g bower
python manage.py syncdb
python manage.py bower install
python manage.py runserver
```

MySQL
```
create user django@localhost identified by 'django';
create database qems2;
grant all privileges on qems2.* to django@localhost;
```
