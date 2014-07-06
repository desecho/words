apt-get install libhunspell-dev hunspell-en-us hunspell-fr

pip install -r requirements.txt
bower install

./manage.py syncdb
./manage.py collectstatic
