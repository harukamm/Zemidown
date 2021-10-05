#!/bin/sh

src_dir="src"
test_dir="test"
out_dir="docs"

rm -rf $out_dir
mkdir -p $out_dir

for fname in `ls ${test_dir}/*.txt | xargs -n 1 basename`
do
  input="${test_dir}/${fname}"
  exe="python3 ${src_dir}/conv_main.py ${out_dir} ${input}"
  echo $exe
  ${exe}
  ret=$?
  if [ $ret -ne 0 ]; then
    exit 1
  fi
done

files="$(ls $out_dir | sort -n)"
index_file="$out_dir/index.html"

echo """<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta NAME="viewport" content='width=device-width, initial-scale=1' />
    <title>Zemidown docs</title>
    <style>
    </style>
  </head>
  <body>
    <h1>Files</h1>
    <ul>""" >> "$index_file"

for file in $files; do
  echo "<li><a href='$file'>$file</a></li>" >> "$index_file"
done

echo """
  </ul></body>
</html>""" >> "$index_file"
