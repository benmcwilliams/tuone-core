# Tuone

This repository processes newspaper articles to return structured information about clean technology investments. Example investments include the construction of a factory to produce solar panels, the deployment of a wind farm, or the upgrading of a vehicle assembly line to produce electric vehicles.

## 1. Database

A database of articles is created with unique article IDs and paragraph numbering {title, date, ID, url, paragraphs}. This is built from the following sources:
- [Electrive](https://www.electrive.com/)
- [World Energy](https://world-energy.org/)
- [RenewsBiz](https://www.renews.biz/)
- [Offshore Wind](https://www.offshorewind.biz/)
- [PV Tech](https://www.pv-tech.org/)
- [PV Magazine](https://www.pv-magazine.com/)
- [Power Technology](https://www.power-technology.com/)

Three steps build the article database:
1. Crawl source websites and retrieve all article URLs.
2. Process article URLs to extract the article title, date and text (stored as paragraphs) and store this in a database.
3. Screen articles for keywords to identify relevant articles. This results in about 90% of full articles being rejected.

**i-crawl.py**
This script crawls the sources and stores article URLs in a database.

**ii-scrape.py**
This script processes article URLs to extract the information and store it in a database.

**iii-filter.py**
Every article is screened for keywords. A dictionary of article IDs and boolean values is created indicating whether the article is relevant (contains a keyword). This dictionary filters the database for article_collection which is the primary data source for analysis. 
- keywords = {"factory", "facility", "plant", "production line", "production site", "refinery", "pilot project"}

## 2. Project Node Identification (Project Collections)

In a second phase, we identify projects mentioned in the articles. Projects are assigned a unique projectID. A project is defined by two vectors: a company and location. These project nodes form the basis of further analysis.

Duplicate projects are merged using three dictionaries. 
1. Company duplicates: merging similar company names (eg Volkswagen and VW)
2. Location duplicates: merging similar locations (eg Komárom and Komarom)
3. Canonical nodes: a merging of (companny, location) pairs or tuples. For cases, where duplication is caused not by alternatite company namings but by multiple attribution at the same project node.  

**iv-recognise-projects.py**
This script runs the project recognition prompt on each article. It returns a list of projects mentioned in each article, in jsonl format. These are stored in the folder src/article_project_lists, where each jsonl file has the name of the article ID.

**v-project-collections.py**
The *input* is the appended article_project_lists. That is, all project nodes that are initially recognised by our first prompt. 
The purpose of this script is to reduce the number of project nodes by merging duplicates and creating canonical nodes. This is done by applying the three dictionaries (company; location; canonical nodes) to the project nodes.
- outputs a clean projects_recognised.json 
- outputs a chronological.json with projects sorted by date
- updates company_to_companyID.pkl and location_to_locationID.pkl with new IDs

## 3. Summaries

The *chronological.json* is now the primary data source for further analysis. It is a dictionary of each canonical node mapped to a list of articles that discuss that node. This is the same as *projects_recognised.json* only with articles ordered by descending date. This is relevant for prompting GPT, as attention is understood to focus more on first articles. 

**vi-summaries.py**
This script generates summaries of projects. Multiple summary types are possible. 
Any new summary request should be added to prompts/summaries/ and the 'summary_prompt_path_dict' in vi-summaries.py.
Currently, we generate an "evolutionary" summary and a "contrastive" summary. 

**vii-merge-summaries.py**
This script merges the "evolutionary" and "contrastive" summaries to form a consistent text output, which is then used for prompting GPT.

## 4. Model Outputs 

**x-node-extraction.py**
This script sequentially processes each project node. It asks a series of questions returning answers from the model. 
Prompts are all listed in *prompts/prompt_tree*. Outputs are stored in *src/outputs/model*. 
The logic is that questions are asked in an iterative manner. First the model identified which technology the project corresponds to. Then it identifies which component of which value chain (deployment or manufacturing) the project corresponds to within that technology. Then for each technology/component value, the model is asked how many investments (initial; first expansion; second expansion etc) are present. 
Finally for each of these specific *investment phases* the model is asked to return a series of specific information (capacity, investment value, dates, jobs).

## Updating Obsidian 
**obsidian-sync.ipynb**
This script updates the Obsidian database with the latest information. Any projects marked by the user as 'checked' in the vault are left untouched. All other projects are updated with the latest model outputs. 

**create-page-views**
This script creates the markdown views by project, company and location. Each view is a markdown file with dataview logic to show the investment phases associated with that company/location/project. 