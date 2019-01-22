
TEX_NAME = manual
#BIBTEX_NAME = bibtex -min-crossrefs=999
BIBTEX_NAME = biber
ORPHEUS = https://orpheus-prod.lib.cam.ac.uk/policies/

all:
	pdflatex ${TEX_NAME}.tex
	${BIBTEX_NAME} ${TEX_NAME}
	pdflatex ${TEX_NAME}.tex
	#pdflatex ${TEX_NAME}.tex
	# dvips -t letter -Ppdf ${TEX_NAME}.dvi -o ${TEX_NAME}.ps
	# Comment out the next line if you want to create a PDF
	#ps2pdf ${TEX_NAME}.ps ${TEX_NAME}.pdf

html:
	htlatex ${TEX_NAME}.tex

screenshots:
	# see https://www.booleanworld.com/take-screenshots-webpages-command-line/
	# firefox -screenshot ./images/screenshots/home.png ${ORPHEUS} #not working on Dell Precision, but fine on Latitude
	firefox -screenshot ./images/screenshots/journals.png ${ORPHEUS}/journals/

