bash:
	docker exec -it djangoplicity-visits bash

test:
	docker exec -it djangoplicity-visits coverage run --source='.' manage.py test

coverage-html:
	docker exec -it djangoplicity-visits coverage html
	open ./htmlcov/index.html

test-python27:
	docker exec -it djangoplicity-visits tox -e py27-django111
