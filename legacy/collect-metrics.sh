DS_PATH=$1


for f in $(find $DS_PATH)
do
  md5 $f
done
