QEMS2 - a question submission and editing system
=====

This is a fork of QEMS2 redesigned with the Foundation framework instead of Bootstrap. See the original project for setup information.

Note that this can be used with an existing instance of QEMS2 by changing the database name from qems2 to qems2_stable and running `python manage.py bower install; python manage.py collectstatic; python manage.py runserver` in the qems2-foundation directory. 