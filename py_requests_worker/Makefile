#   Makefile
#

PYTHON3 := $(shell which python3)
PYTHON3_VERSION := $(shell $(PYTHON3) --version)

clean:
	@echo "======================================================"
	@echo clean: $(IRON_WORKER_PACKAGE_NAME)
	@echo "======================================================"
	@rm -fR __pycache__
	@rm -fR *.pyc
	@rm -fR tmp
	@rm -fR *.zip

install: clean
	@echo "======================================================"
	@echo install $(IRON_WORKER_PACKAGE_NAME)
	@echo "======================================================"
	$(PYTHON3) -m pip install --upgrade pip
	$(PYTHON3) -m pip install --upgrade -r requirements.txt

local-run: install
	@echo $(PYTHON3): $(PYTHON3_VERSION)
	@echo "======================================================"
	@echo local-run
	@echo "======================================================"
	@$(PYTHON3) worker.py || (echo "local-run failed $$?"; exit 1)

list:
	cat Makefile | grep "^[a-z]" | awk '{print $$1}' | sed "s/://g" | sort