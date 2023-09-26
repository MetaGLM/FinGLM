#!/bin/bash
ROOT_PATH="/tcdata/"
PDF_NAME_PATH="$ROOT_PATH/A-list-pdf-name.txt"
ALL_TXT_PATH="$ROOT_PATH/alltxt/"
ALL_HTML_PATH="$ROOT_PATH/allhtml/"
DATA_PROCESS_PATH="/app/data/"
TXT_EXTRACT_PATH="$DATA_PROCESS_PATH/txt_to_three_table/"
HTML_EXTRACT_PATH="$DATA_PROCESS_PATH/html_to_three_table/"
MAX_PROCESS=10
if test ! -d $DATA_PROCESS_PATH; then
    mkdir -p $DATA_PROCESS_PATH
fi
if test ! -d $TXT_EXTRACT_PATH; then
    mkdir -p $TXT_EXTRACT_PATH
fi
if test ! -d $HTML_EXTRACT_PATH; then
    mkdir -p $HTML_EXTRACT_PATH
fi
echo "1------txt_extract_info start"
for (( i=0; i<$MAX_PROCESS; i++ )); do
    echo $i
    nohup go run $CODE_PATH/txt_extract_info.go $PDF_NAME_PATH $ALL_TXT_PATH $TXT_EXTRACT_PATH $MAX_PROCESS $i 2>&1 &
done
wait
echo "1------txt_extract_info finished"

echo "2------html_extract_info start"
for (( i=0; i<$MAX_PROCESS; i++ )); do
    echo $i
    nohup python $CODE_PATH/html_extract_info.py $PDF_NAME_PATH $ALL_HTML_PATH $HTML_EXTRACT_PATH $MAX_PROCESS $i 2>&1 &
done
wait
echo "2------html_extract_info finished"

echo "3------combine html & txt start"
go run $CODE_PATH/combine_html_txt.go $PDF_NAME_PATH $TXT_EXTRACT_PATH $HTML_EXTRACT_PATH $DATA_PROCESS_PATH
wait
echo "3------combine html & txt finished"

echo "4------extract people info start"
go run $CODE_PATH/extract_people.go $PDF_NAME_PATH $ALL_TXT_PATH $DATA_PROCESS_PATH
wait
echo "4------extract prople info finished"

echo "5------extract baseinfo start"
go run $CODE_PATH/extract_baseinfo.go $PDF_NAME_PATH $ALL_TXT_PATH $DATA_PROCESS_PATH
wait
echo "5------extract baseinfo finished"

echo "6------transfer to excel start"
python $CODE_PATH/transfer_to_excel.py $DATA_PROCESS_PATH
wait
echo "6------transfer to excel finished"