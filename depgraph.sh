#!/bin/bash

#input directory
xml_dir=../ACL-ARC-math-20/*_gd_output.xml

#output directory
tsv_dir=../results
root_dir=../results/root
sink_dir=../results/sink

ext=.tsv

for fl in $xml_dir
do
    source_flname=$(basename $fl)

    tsv_flname="${source_flname/_gd_output.xml/$ext}"
    echo $fl
    python depgraph.py $source_flname 1 > $tsv_dir/$tsv_flname &
done
