configure:
	@mkdir logs || true 
	python3 configure.py
run:
	python3 main.py
