# stac-access-performance

Testing the performance of accessing and performing a simple analysis on the same time series of 
[Sentinel-1 RTC](https://explorer.digitalearth.africa/products/s1_rtc) scenes... 
- ...on different HPC systems:
  - [Draco](https://wiki.uni-jena.de/pages/viewpage.action?pageId=22453002)
  - [LRZ](https://www.lrz.de/english/)
- ...and using different access methods:
  - Local STAC catalog using [odc-stac](https://github.com/opendatacube/odc-stac)
  - Local STAC catalog using [stackstac](https://github.com/gjoseph92/stackstac)
  - Local EO3 catalog using [datacube-core](https://github.com/opendatacube/datacube-core) (Open Data Cube)
  - Remote STAC catalog from [Digital Earth Africa](https://explorer.digitalearth.africa/stac) using odc-stac

See [performance.ipynb](https://nbviewer.org/github/maawoo/stac-access-performance/blob/main/performance.ipynb) for details.

The resulting reports can be viewed here:  
https://maawoo.github.io/stac-access-performance/results
