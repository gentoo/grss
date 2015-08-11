#!/bin/bash

if [[ ${#@} != "1" ]]; then
	echo "usage: $0 <tag>"
fi

tag=$1
ver=${tag/v}
git archive --format=tar --prefix=grss-${ver}/ $tag | gzip - > ../grss-${ver}.tar.gz
