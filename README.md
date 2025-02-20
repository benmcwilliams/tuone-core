# Tuone

This repository processes newspaper articles to return structured information about clean technology investments. Example investments include the construction of a factory to produce solar panels, the deployment of a wind farm, or the upgrading of a vehicle assembly line to produce electric vehicles.

## 1. Database (DONE)

A database of articles is created and stored in mongoDB with unique article IDs and paragraph numbering {title, date, ID, url, paragraphs}. This is built from the following sources:
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

An example entry of the article_collection is shown below:

{
    "title": "Mitsubishi Chemical expands production capacities",
    "paragraphs": [
        {
            "p1": "Tokyo-based Mitsubishi Chemical wants to boost up its battery electrolyte business. It plans several strategic steps due to growing demand on the electric vehicle market.",
            "p2": "The company plans to restarting production in a factory based in Britain and doubling its output in the States. Part of the reconstruction plan is also to close a factory in China. The company is said to be even willing to temporarily limit its mobile device battery production.",
            "p3": "Initially, the UK plant has built batteries since 2012. However, the anticipated demand did not arise, so the production lines were stopped in March 2016.asia.nikkei.com",
            "p4": "Your email address will not be published.Required fields are marked*",
            "p5": "Name *",
            "p6": "E-Mail *",
            "p7": "I agree with thePrivacy policy",
            "p8": "We have been covering the development of electric mobility with journalistic passion and expertise since 2011. As the industry's leading specialist media, we offer comprehensive reporting of the highest quality - as a central platform for the rapid ramp-up of this technology. With news, background information, driving reports, interviews, videos as well as advertising messages.",
            "p9": "\u00a9 2024 electrive.com"
        }
    ],
    "meta": {
        "ID": "1100001",
        "date": "04-12-2017",
        "url": "https://www.electrive.com/2017/12/04/mitsubishi-chemical-expands-capacities-due-high-demand/"
    }
}

## 2. Entity Identification (TO DO)

In a second phase, we identify projects mentioned in the articles. A project is identified with a physical location and the name of the company or joint venture who is investing. The products of the factory are defined as a sub-node.

**identify-projects.py** (TO DO)
This script prompts an LLM with each article to extract company, joint venture and factory entities. Products are returned as a sub-node of the factory and refer to whatever is produced at the factory. The entities are stored in the mongoDB collection, 'primary_entities'. 
- load articles from mongoDB (collapse paragraphs)
- pass article through OpenAI API (run prompt)
- return structured output (entities)
- store in mongoDB

**resolve-projects.py** (TO DO)
This script prompts an LLM with each article and the primary entities identified. 

Process 
- loads articles from mongoDB
- loads primary entities from mongoDB (which are stored with an articleID)
- prompt will pass the entities and the article text, and it will ask to define relationships between the entities.

For example:
- company FUNDS joint_venture
- company FUNDS factory (this is a project)
- joint_venture FUNDS factory (this is a project)
- company CONTRACTS factory

f{Here are the companies {company_list}, here is the {joint venture}. Can you resolve relationships between them in the following article: {article_text}}

**normalise-projects.py** (TO DO)
The result of the previous two steps is a list of projects, defined by a factory location, an investing company and a list of products.
- company names are normalised (eg Volkswagen and VW, VW Group) and also any parent/subsidiary relationships are defined, merge duplicates. This is the dictionary: 
*src/mappings/company_name_variations.json*
- products are normalised to a master list (eg Tesla Model X and VW ID.3 both map to 'electric vehicles'), merge duplicates
*dictionary to be defined*
- query the OpenStreeMap API to return latitude and longitude of factory locations
- merge duplicates in cases where factory locations are within 15 squared km and company | product list pairings are identical
- output *chronological.json* - this is a JSON dictionary which maps each projectID to a list of articleIDs that discuss the project, in chronological order of the date the article was published
*this script also updates the ID dictionary. 

Here is an example of how *chronological.json*
{
    "GBR-07876-08197": [
        1705678
    ],
    "GBR-07877-08197": [
        1705678
    ],
}

!(in the current pipeline this is done in the *v-unique-projects.py* script, see end)

## 3. Summaries

- each collection of articles discussing a project is passed to an LLM. 

**vi-summaries.py** (TO DO, CHIARA)
This script generates summaries of projects. Multiple summary types are possible. 
Any new summary request should be added to prompts/summaries/ and the 'summary_prompt_path_dict' in vi-summaries.py.
Currently, we generate an "evolutionary" summary and a "contrastive" summary. 

**vii-merge-summaries.py** (TO BE DELETED)
This script merges the "evolutionary" and "contrastive" summaries to form a consistent text output, which is then used for prompting GPT.

## 4. Model Outputs 

The input for this stage is summaries of projects. 

**p-knowledge-graph.py** (TO DO)
This script creates a knowledge graph from the project summaries. 
- Extract all relevant descriptive ENTITIES about a project (investments eg (€500 million), capacities (eg 100 MWh), dates (eg announced on 12-2022, completed on 12-2023), jobs (eg 1,000 employees), subsidies, etc) and then identifies RELATIONSHIPS between these entities.
1. Will read in the summaries for each project as identified in section 3. 
2. Pass a first prompt to an LLM asking to extract entities, and store these in mongoDB. 
3. Pass a second prompt to an LLM with the identifited entities, and the article again, asking to extract relationships. 
4. Store these in mongoDB (this is the final output)

## 5. Validation (TO DO, ROSS)  

**z-frontend.py** 
A frontend for the knowledge graphs. Two versions 
- articles with the identified company and factory relationships identified (according to the LLM). User can correct these if they disagree. 
- summaries with the identified project descriptive entities and relationships. Again users can correct. 
The script connects directly and updates the mongoDB on user entry.


# possible LLM finetuning



#### OLD code
**v-unique-projects.py**
The *input* is the appended article_project_lists. That is, all project nodes that are initially recognised by our first prompt. 
The purpose of this script is to reduce the number of project nodes by merging duplicates and creating canonical nodes. This is done by applying the three dictionaries (company; location; canonical nodes) to the project nodes.
- outputs a clean projects_recognised.json 
- outputs a chronological.json with projects sorted by date
- updates company_to_companyID.pkl and location_to_locationID.pkl with new IDs


**x-node-extraction.py**
This script sequentially processes each project node. It asks a series of questions returning answers from the model. 
Prompts are all listed in *prompts/prompt_tree*. Outputs are stored in *src/outputs/model*. 
The logic is that questions are asked in an iterative manner. First the model identified which technology the project corresponds to. Then it identifies which component of which value chain (deployment or manufacturing) the project corresponds to within that technology. Then for each technology/component value, the model is asked how many investments (initial; first expansion; second expansion etc) are present. 
Finally for each of these specific *investment phases* the model is asked to return a series of specific information (capacity, investment value, dates, jobs).
