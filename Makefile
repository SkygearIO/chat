VERSION := $(shell git describe --always | sed 's/v\(.*\)/\1/')
PACKAGE_VERSION ?= $(shell echo $(VERSION) | sed 's/-\([0-9]*\)-\(g[0-9a-f]*\)/+\1.\2/')
OS = $(shell uname -s)

ifeq ($(OS),Darwin)
	SED := sed -i ""
else
	SED := sed -i""
endif

.PHONY: update-version
update-version:
	$(SED) "s/version='.*'/version='$(PACKAGE_VERSION)'/" setup.py

.PHONY: release-commit
release-commit:
	./scripts/release-commit.sh
