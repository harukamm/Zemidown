#!/bin/sh

src_dir="src"
test_dir="test"
out_dir=$test_dir

for fname in `ls ${test_dir}/*.txt | xargs -n 1 basename`
do
  input="${test_dir}/${fname}"
  output="${out_dir}/${fname}.html"
  exe="python ${src_dir}/conv_main.py ${input} ${output}"
  echo $exe
  ${exe}
  ret=$?
  if [ $ret -ne 0 ]; then
    exit 1
  fi
done
