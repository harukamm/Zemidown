#!/bin/sh

src_dir="src"
test_dir="test"
out_dir="out"

if [ ! -d $out_dir ]
then
    mkdir $out_dir
fi

for fname in `ls ${test_dir}/*.txt | xargs -n 1 basename`
do
  input="${test_dir}/${fname}"
  exe="python ${src_dir}/conv_main.py ${input}"
  echo $exe
  ${exe}
  ret=$?
  if [ $ret -ne 0 ]; then
    exit 1
  fi
done
