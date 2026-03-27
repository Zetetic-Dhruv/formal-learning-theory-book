TEX_DIR  := textbook
MAIN     := main
PDF      := $(TEX_DIR)/$(MAIN).pdf

.PHONY: all clean distclean

all: $(PDF)

$(PDF): $(TEX_DIR)/$(MAIN).tex $(wildcard $(TEX_DIR)/chapters/*.tex) $(wildcard $(TEX_DIR)/appendices/*.tex)
	cd $(TEX_DIR) && latexmk -pdf $(MAIN).tex

clean:
	cd $(TEX_DIR) && latexmk -c $(MAIN).tex

distclean:
	cd $(TEX_DIR) && latexmk -C $(MAIN).tex
