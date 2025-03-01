#!/bin/bash
#
#
rootdir="/bigdata/webcams/"
while read tag url; do
    destdir=${rootdir}/${tag}
    tagname=${destdir}/${tag}.txt
    mkdir -p $destdir
    destfile=$(date +"${destdir}/%Y%m%dT%H%M.jpg")
    echo $tag @ $url >&2
    echo curl --etag-compare ${tagname} --etag-save ${tagname} ${url} -o ${destfile}
    curl --etag-compare ${tagname} --etag-save ${tagname} ${url} -o ${destfile}
done < listewebcam
