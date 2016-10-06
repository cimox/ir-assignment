#!/bin/bash

IFS='
'

LIMIT=10000
files=( `find ../ -type f -name 'articles.json'` )

for file in "${files[@]}"; do
	ln=`wc -l $file | awk '{ print $1 }'`
	echo "Importing file: $file"
	while [[ $ln -gt 0 ]]; do
		tail -$ln $file | head -$LIMIT > tmp.json
		res=`head -2 tmp.json`
		echo "> Remaining lines $ln, sample: $res"

		curl -XPOST localhost:9200/_bulk --data-binary "@tmp.json"

		if [[ $ln -ge $LIMIT ]]; then
			ln=$(($ln-$LIMIT))
		else
			ln=$LIMIT
		fi
	done
done
