# SSURGO-QA
Official version of the Quality Assurance tools used to certify SSURGO data 
# 1. Setup
<ul> 
<li>Download SSURGO by Areasymbol - Use Soil Data Access and Web Soil Survey download page to get SSURGO datasets. User can a wildcard to query the database by Areasymbol or by age. </li>
<li>Download SSURGO by Region - Downloads SSURGO Soil Survey Areas that are owned by a specific region including an approximiate 2 soil survey area buffer. </li>
<li>Generate Regional Transactional Geodatabase - Used to create the Regional Transactional Spatial Database (RTSD) for SSURGO. </li>
<li>Generate SSO SSURGO Datasets - Create a SSURGO file geodatabase for a selected MLRA Soil Survey Office. </li>
<li>Import SSURGO Datasets in FGDB - This tooll will import SSURGO spatial and tabular datasets within a given location into a File Geodatabase and establish the necessary table and feature class relationships to interact with the dataset. </li>
<li>Insert NATSYM and MUNAME Value - This tool adds the National Mapunit Symbol (NATMUSYM) and the Mapunit Name (MUNAME) values to the corresponding MUKEY. An MUKEY field is required to execute. A network connection is required in order to submit a query to SDacess. </li>
<li>RTSD - Check SDJR Project Out - Designed to work with the RTSD to manage SDJR projects and export data for those projects to be sent to the MLRA SSO. </li>
</ul>

# 2. Quality Assurance

<ul>
<li> Check Attributes - Checks formatting of the selected soil attributes (normally AREASYMBOL and MUSYM). Also checks to make sure that the AREASYMBOL is present in Web Soil Survey.</li>
<li>Compare Spatial-NASIS Mapunits - Check MUSYM values in the input layer using a NASIS online report. Internet connection required for this tool. </li>
<li>Find Common Lines - Compares attributes between adjacent polygons and flags those that are the same. </li>
<li>Find Common Points - Find points where polygon with the same attribute value intersect. These are usually soil polygons that get 'pinched off'. This will also flag self-intersecting polygons.</li>
<li>Find Edge Matching Errors - Looks for locations along survey boundaries where a node-to-node match does not exist. It does NOT look at soil attribute matches. </li>
<li>Find Multipart Features - Simply reports the existence of multipart polygons. These must be exploded in an edit session if they are detected.</li>
<li>Find Slivers - Looks for slivers or gaps in a polygon layer based upon a minimum-allowed internal polygon angle. Often smaller angles are the result of snapping vertices that create slivers, zig zags or bowties. </li>
<li>Find Vertex Problems - Calculate area statistics by state or survey area from a GCS polygon featureclass and find problem vertices </li>
<li>Report Vertex Count - Simply reports the number of vertices found in the input featureclass. This tool is useful when the user wants to find out how many vertices were present 'before-and-after'. </li>
<li>Report Vertex Densisty - Calculate area statistics by state or survey area from a  polygon featureclass. Can be used to determine what surveys are potential candidates for thinning or may have vertices that are liable to contribute to snapping or other geometry problems. </li>
</ul>

# 3. Certification

<ul>
<li>Export to SSURGO Shapefile - Export geodatabase featureclasses to SSURGO shapefile format. These shapefiles are suitable for posting to the Staging Server. </li>
<li>Generate Special Feature File - Creates the feature description text file-table for SSURGO. </li>
<li>Zip SSURGO Export Folders - Zips all of the required SSURGO shapefiles and feature file for posting to the Staging Server. </li>
