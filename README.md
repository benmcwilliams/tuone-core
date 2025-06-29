# Tuone

This repository processes newspaper articles to return structured information about clean technology investments. Example investments include the construction of a factory to produce solar panels, the deployment of a wind farm, or the upgrading of a vehicle assembly line to produce electric vehicles.

## 1. Database construction

A database of articles is created and stored in mongoDB with unique article IDs and paragraph numbering {title, date, ID, url, paragraphs}. This is built from the following sources:
- [Electrive](https://www.electrive.com/)
- [World Energy](https://world-energy.org/)
- [RenewsBiz](https://www.renews.biz/)
- [Offshore Wind](https://www.offshorewind.biz/)
- [PV Tech](https://www.pv-tech.org/)
- [PV Magazine](https://www.pv-magazine.com/)
- [Power Technology](https://www.power-technology.com/)

The sub-directories, crawl and scrape run the process to update the article database. 

## 2. Knowledge graph

Knowledge graphs are built using a collection of finetuned language models at the individual article level. 
These are stored in mongoDB under a nodes and relationship header, an example: 

{"_id":{"$oid":"67f52d07981040986eab7b6a"},
    "title":"VinFast starts delivering the VF 9 in the US",
    "paragraphs":[{"p1":"Shortly after completing a billion-euro financing round, Vietnamese car manufacturer VinFast has started delivering its flagship model VF 9 to customers in the US and Canada. The first units were handed over at an event in Los Angeles.","p2":"paragraph-2 text.","pn":"paragraph-n text"],
    "meta":
        {"ID":"2708649",
        "date":{"$date":{"$numberLong":"1732233600000"}},
        "url":"https://www.electrive.com/2024/11/22/vinfast-starts-delivering-the-vf-9-in-the-us/#comment-368047",
        "lastModifiedOn":"2025-04-11T16:29:22+03:00","category":"electrive"},
    "nodes":[
        {"article_id":"67f52d07981040986eab7b6a","id":"company_vinfast","type":"company","name":"VinFast","location":null,"amount":null,"status":null},{"article_id":"67f52d07981040986eab7b6a","id":"factory_north_carolina","type":"factory","name":"North Carolina","location":{"city":"North Carolina","country":"United States"},"amount":"","status":"","phase":""},
        {"article_id":"67f52d07981040986eab7b6a","id":"investment_billion_euro_financing_round","type":"investment","name":"billion-euro financing round","location":null,"amount":"billion-euro","status":"completed","phase":"unclear"},
        {"article_id":"67f52d07981040986eab7b6a","id":"product_vf_9","type":"product","name":"VF 9","location":null,"amount":null,"status":null},
    "relationships":[
        {"article_id":"67f52d07981040986eab7b6a","id":"company_vinfast_owns_factory_north_carolina","source":"company_vinfast","target":"factory_north_carolina","type":"owns","group":"ownership"},
        {"article_id":"67f52d07981040986eab7b6a","id":"company_vinfast_receives_investment_billion_euro_financing_round","source":"company_vinfast","target":"investment_billion_euro_financing_round","type":"receives","group":"financial_origin"}],
    "validation":true}

## 3. Normalisation 

## 4. Reconcilliation

