MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
.SUFFIXES:
.SECONDARY:

# environment variables
.EXPORT_ALL_VARIABLES:
ifdef LINKML_ENVIRONMENT_FILENAME
include ${LINKML_ENVIRONMENT_FILENAME}
else
include config.public.mk
endif

RUN = poetry run
SCHEMA_NAME = $(LINKML_SCHEMA_NAME)
SOURCE_SCHEMA_PATH = $(LINKML_SCHEMA_SOURCE_PATH)
SOURCE_SCHEMA_DIR = $(dir $(SOURCE_SCHEMA_PATH))
SRC = src
DEST = project
PYMODEL = $(SRC)/$(SCHEMA_NAME)/datamodel
PROJ = proj
PYPROJ = python/$(subst -,_,$(SCHEMA_NAME))
PYTHON_DATACLASS = $(PYPROJ)/dataclass.py
DOCDIR = docs
DOCTEMPLATES = templates
EXAMPLEDIR = data/examples/

CONFIG_YAML = --config-file config.yaml


GEN_DOC_ARGS =
ifdef LINKML_GENERATORS_DOC_ARGS
GEN_DOC_ARGS += ${LINKML_GENERATORS_DOC_ARGS}
endif

GEN_OWL_ARGS =
ifdef LINKML_GENERATORS_OWL_ARGS
GEN_OWL_ARGS += ${LINKML_GENERATORS_OWL_ARGS}
endif

GEN_JAVA_ARGS =
ifdef LINKML_GENERATORS_JAVA_ARGS
GEN_JAVA_ARGS += ${LINKML_GENERATORS_JAVA_ARGS}
endif

GEN_TS_ARGS =
ifdef LINKML_GENERATORS_TYPESCRIPT_ARGS
GEN_TS_ARGS += ${LINKML_GENERATORS_TYPESCRIPT_ARGS}
endif


# basename of a YAML file in model/
.PHONY: all clean setup gen-project gen-examples gendoc

# note: "help" MUST be the first target in the file,
# when the user types "make" they should get help info
help: status
	@echo ""
	@echo "make setup -- initial setup (run this first)"
	@echo "make site -- makes site locally"
	@echo "make install -- install dependencies"
	@echo "make test -- runs tests"
	@echo "make lint -- perform linting"
	@echo "make testdoc -- builds docs and runs local test server"
	@echo "make deploy -- deploys site"
	@echo "make update -- updates linkml version"
	@echo "make help -- show this help"
	@echo ""

status: check-config
	@echo "Project: $(SCHEMA_NAME)"
	@echo "Source: $(SOURCE_SCHEMA_PATH)"
	@echo "Python DC  : $(PYTHON_DATACLASS)"


# install any dependencies required for building
install:
	poetry install
.PHONY: install


# EXPERIMENTAL
# create-data-harmonizer:
# 	npm init data-harmonizer $(SOURCE_SCHEMA_PATH)

all: site
site: gen-dist gendoc
%.yaml: gen-dist
deploy: all mkd-gh-deploy

$(PYTHON_DATACLASS): $(SCHEMAS)
	mkdir -p $(PROJ)
	$(RUN) gen-project ${CONFIG_YAML} -d $(PROJ) $(SOURCE_SCHEMA_PATH) && \
	echo mv $(PROJ)/$(SCHEMA_NAME).py $(PYTHON_DATACLASS)
	mv $(PROJ)/$(SCHEMA_NAME).py $(PYTHON_DATACLASS)
	mv $(PROJ)/jsonschema/$(SCHEMA_NAME).schema.json misc/
	mv $(PROJ)/jsonld/$(SCHEMA_NAME).context.jsonld misc/
	mv $(PROJ)/jsonld/$(SCHEMA_NAME).jsonld misc/
	mv $(PROJ)/shacl/$(SCHEMA_NAME).shacl.ttl rdf/
	mv $(PROJ)/owl/$(SCHEMA_NAME).owl.ttl rdf/
	mv $(PROJ)/prefixmap/$(SCHEMA_NAME).yaml rdf/$(SCHEMA_NAME).prefixmap.yaml

# generates all project files
gen-dist: $(PYTHON_DATACLASS)
	$(RUN) gen-project ${CONFIG_YAML} -d $(DEST) $(SOURCE_SCHEMA_PATH) && mv $(DEST)/*.py $(PYMODEL)
	mkdir -p ${PROJ}/plantuml
	$(RUN) gen-plantuml $(SOURCE_SCHEMA_PATH) -d ${PROJ}/plantuml/${SCHEMA_NAME}

	mkdir -p ${PROJ}/rdf
	$(RUN) gen-rdf $(SOURCE_SCHEMA_PATH) > ${PROJ}/rdf/${SCHEMA_NAME}.rdf
	mv ${PROJ}/rdf/${SCHEMA_NAME}.rdf rdf/${SCHEMA_NAME}.rdf


	mkdir -p ${PROJ}/sparql
	$(RUN) gen-sparql $(SOURCE_SCHEMA_PATH) -d ${PROJ}/sparql/${SCHEMA_NAME}
	mv ${PROJ}/sparql/${SCHEMA_NAME}/*.rq sparql/

	mkdir -p ${PROJ}/pydantic
	$(RUN) gen-pydantic $(SOURCE_SCHEMA_PATH) \
					--extra-fields forbid \
					> ${PROJ}/model.py
	mv ${PROJ}/model.py ${PYPROJ}/model.py

	#mkdir -p ${PROJ}/markdown
	#$(RUN) gen-markdown $(SOURCE_SCHEMA_PATH) -i  -d ${PROJ}/markdown/${SCHEMA_NAME}

# non-empty arg triggers owl (workaround https://github.com/linkml/linkml/issues/1453)
ifneq ($(strip ${GEN_OWL_ARGS}),)
	mkdir -p ${DEST}/owl || true
	$(RUN) gen-owl ${GEN_OWL_ARGS} $(SOURCE_SCHEMA_PATH) >${DEST}/owl/${SCHEMA_NAME}.owl.ttl
endif
# non-empty arg triggers java
ifneq ($(strip ${GEN_JAVA_ARGS}),)
	$(RUN) gen-java ${GEN_JAVA_ARGS} --output-directory ${DEST}/java/ $(SOURCE_SCHEMA_PATH)
endif
# non-empty arg triggers typescript
ifneq ($(strip ${GEN_TS_ARGS}),)
	mkdir -p ${DEST}/typescript || true
	$(RUN) gen-typescript ${GEN_TS_ARGS} $(SOURCE_SCHEMA_PATH) >${DEST}/typescript/${SCHEMA_NAME}.ts
endif

test: test-python

test-python: gen-examples
	$(RUN) pytest


lint:
	$(RUN) linkml-lint $(SOURCE_SCHEMA_PATH)

check-config:
ifndef LINKML_SCHEMA_NAME
	$(error **Project not configured**:\n\n - See '.env.public'\n\n)
else
	$(info Ok)
endif

VALID_YML_FILES := $(wildcard $(EXAMPLEDIR)/valid/*.yml)
VALID_TTL_FILES := $(patsubst $(EXAMPLEDIR)/valid/%.yml,$(EXAMPLEDIR)/valid/%.ttl,$(VALID_YML_FILES))
VALID_NT_FILES := $(patsubst $(EXAMPLEDIR)/valid/%.ttl,$(EXAMPLEDIR)/valid/%.nt,$(VALID_TTL_FILES))
VALID_JSON_FILES := $(patsubst $(EXAMPLEDIR)/valid/%.yml,$(EXAMPLEDIR)/valid/%.json,$(VALID_YML_FILES))
VALID_JSON_LD_FILES := $(patsubst $(EXAMPLEDIR)/valid/%.yml,$(EXAMPLEDIR)/valid/%.ld.json,$(VALID_YML_FILES))

$(EXAMPLEDIR)/valid/%.ttl: $(EXAMPLEDIR)/valid/%.yml $(PYTHON_DATACLASS) $(SCHEMAS)
	$(RUN) linkml-convert -t ttl \
		   -m $(PYTHON_DATACLASS) \
		   --target-class-from-path \
		   -s $(SOURCE_SCHEMA_PATH) \
		   -o $@ $<

$(EXAMPLEDIR)/valid/%.json: $(EXAMPLEDIR)/valid/%.yml
	$(RUN) linkml-convert -t json \
		   -m $(PYTHON_DATACLASS) \
		   --target-class-from-path \
		   -s $(SOURCE_SCHEMA_PATH) \
		   -o $@ $<

$(EXAMPLEDIR)/valid/%.ld.json: $(EXAMPLEDIR)/valid/%.yml
	$(RUN) linkml-convert -t json-ld \
		   -m $(PYTHON_DATACLASS) \
		   --target-class-from-path \
		   -s $(SOURCE_SCHEMA_PATH) \
		   -o $@ $<


convert-valid-yml-to-ttl: $(VALID_TTL_FILES) $(SCHEMAS) $(PYTHON_DATACLASS)
convert-valid-yml-to-nt: $(VALID_NT_FILES) $(SCHEMAS) $(PYTHON_DATACLASS)
convert-valid-yml-to-json: $(VALID_JSON_FILES) $(SCHEMAS) $(PYTHON_DATACLASS)
convert-valid-yml-to-json-ld: $(VALID_JSON_LD_FILES) $(SCHEMAS) $(PYTHON_DATACLASS)

docs/%.svg: schema/%.yaml
	$(RUN) gen-plantuml \
		--kroki-server https://kroki.r4.v-lad.org \
		-d docs $<

docs/erd.mermaid: schema/$(SCHEMA_NAME).yaml
	$(RUN) gen-erdiagram \
			$<  > $@
		# --exclude-attributes \

.PHONY: convert-valid-yml-to-ttl convert-valid-yml-to-json convert-valid-yml-to-json-ld

gen-examples: $(VALID_TTL_FILES) $(VALID_JSON_FILES) $(VALID_JSON_LD_FILES)

examples/output:
	mkdir -p $@
	$(RUN) linkml-run-examples \
		--output-formats json \
		--output-formats yaml \
		--counter-example-input-directory data/examples/invalid \
		--input-directory data/examples/valid \
		--output-directory $@ \
		--schema $< > $@/README.md

# Test documentation locally
serve: testdoc

# Python datamodel
$(PYMODEL):
	mkdir -p $@


$(DOCDIR):
	mkdir -p $@

gendoc:
	mkdir -p $(DOCDIR)
	cp -rf templates/docs/* $(DOCDIR) ; \
	$(RUN) gen-doc \
		-d $(DOCDIR) \
		--template-directory templates/docgen-templates \
		$(SOURCE_SCHEMA_PATH)

testdoc: gendoc
	$(RUN) mkdocs serve

distdoc: gendoc
	$(RUN) mkdocs build


# only necessary if setting up via cookiecutter
.cruft.json:
	echo "creating a stub for .cruft.json. IMPORTANT: setup via cruft not cookiecutter recommended!" ; \
	touch $@

clean:
	rm -rf $(DEST)
	rm -rf tmp
	rm -fr docs/*
	rm -fr site/*
	rm -fr sparql/*
	rm -fr misc/*
	rm -fr rdf/*
	rm -fr sql/*
	rm -fr $(PYMODEL)/*

include project.Makefile
