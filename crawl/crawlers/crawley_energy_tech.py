import os
import time

import certifi
import requests
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# === Environment & Config ===
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
COLLECTION_NAME = os.getenv("MONGO_URLS_NAME")

GRAPHQL_URL = "https://gemenon.graphql.aspire-ebm.com/"
BASE_URL = "https://www.energytech.com"
current_timestamp_ms = int(time.time() * 1000)

HEADERS = {
    "host": "gemenon.graphql.aspire-ebm.com",
    "connection": "keep-alive",
    "sec-ch-ua-platform": "\"Linux\"",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
    "content-type": "application/json",
    "sec-ch-ua-mobile": "?0",
    "x-tenant-key": "ebm_energytech",
    "accept": "*/*",
    "origin": "https://www.energytech.com",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://www.energytech.com/",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9"
}


# === MongoDB ===
def get_mongo_collection():
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
    db = client[DB_NAME]
    return db[COLLECTION_NAME]


# === Step 1: Fetch Article IDs ===
def fetch_article_ids(skip=0, limit=10):
    payload = {
        "query": "query searchContentPublicWebsites(\n  $status: facetSearchItem\n  $created: searchDateRange\n  $limit: Int\n  $published: searchDateRange\n  $searchPhrase: String\n  $textSearchFields: [textSearchFieldsList]\n  $skip: Int\n  $sortDirection: sortDirection\n  $sortField: sortField\n  $tenant: facetSearchItem\n  $type: facetSearchItem\n  $updated: searchDateRange\n  $websiteSchedules: facetSearchItem\n  $websiteSchedulesImplied: facetSearchItem\n) {\n  searchContent(\n    input: {\n      searchPhrase: $searchPhrase\n      textSearchFields: $textSearchFields\n      limit: $limit\n      skip: $skip\n      sort: { field: $sortField, direction: $sortDirection }\n      search: {\n        created: $created,\n        published: $published,\n        updated: $updated,\n      }\n      facetSearch: {\n        tenant: $tenant\n        status: $status\n        type: $type\n        websiteSchedules: $websiteSchedules\n        websiteSchedulesImplied: $websiteSchedulesImplied\n      }\n      facetFields: [\n        tenant\n        type\n        websiteSchedules\n      ]\n      returnFields: [\n        created\n        createdBy\n        labels\n        name\n        paginationToken\n        primaryImage\n        primarySection\n        published\n        score\n        status\n        teaser\n        type\n        updated\n        updatedBy\n      ]\n    }\n  ) {\n    docs\n    meta\n  }\n}",
        "variables": {
            "sortField": "published",
            "sortDirection": "desc",
            "limit": skip,
            "skip": limit,
            "published": {
                "to": current_timestamp_ms,
            },
            "status": {
                "operator": "or",
                "values": ["1"]
            },
            "tenant": {
                "operator": "or",
                "values": ["ebm_energytech"]
            },
            "type": {
                "operator": "or",
                "values": [
                    "Apparatus",
                    "Article",
                    "Blog",
                    "Company",
                    "Document",
                    "Event",
                    "InQuarters",
                    "MediaGallery",
                    "News",
                    "Page",
                    "Podcast",
                    "PressRelease",
                    "Product",
                    "Video",
                    "Webinar",
                    "Whitepaper"
                ]
            }
        }
    }

    response = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS)
    print(response)
    response.raise_for_status()
    data = response.json()
    print(data)
    docs = data.get("data", {}).get("searchContent", {}).get("docs", [])
    return [doc["id"] for doc in docs if "id" in doc]


# === Step 2: Fetch URLs for Given IDs ===
def fetch_urls_from_ids(ids):
    # Prepare a new query that takes the IDs and gets URLs
    payload = {
        "query": "query getContentStream(\n  $authorId: Int\n  $excludeContentIds: [Int!]\n  $includeContentIds: [Int!]\n  $includeContentTypes: [ContentType!]\n  $issueId: Int\n  $limit: Int\n  $publishedAfter: Date\n  $publishedBefore: Date\n  $randomizeResults: Boolean\n  $relatedToId: Int\n  $requireMemberships: [ObjectID]\n  $requirePrimaryImage: Boolean\n  $scheduleOption: WebsiteScheduleOption\n  $sectionBubbling: Boolean\n  $sectionId: Int\n  $skip: Int\n  $sortField: ContentSortField\n  $sortOrder: SortOrder\n  $startDateAfter: Date\n  $startDateBefore: Date\n  $teaserFallback: Boolean\n  $teaserMaxLength: Int\n) {\n  getContentStream(\n    input: {\n      authorId: $authorId\n      excludeContentIds: $excludeContentIds\n      includeContentIds: $includeContentIds\n      includeContentTypes: $includeContentTypes\n      issueId: $issueId\n      pagination: { limit: $limit, skip: $skip }\n      publishedAfter: $publishedAfter\n      publishedBefore: $publishedBefore\n      randomizeResults: $randomizeResults\n      relatedTo: { id: $relatedToId }\n      requireMemberships: $requireMemberships\n      requirePrimaryImage: $requirePrimaryImage\n      scheduleOption: $scheduleOption\n      sectionBubbling: $sectionBubbling\n      sectionId: $sectionId\n      sort: { field: $sortField, order: $sortOrder }\n      startDateAfter: $startDateAfter\n      startDateBefore: $startDateBefore\n    }\n  ) {\n    edges {\n      node {\n        id\n        type\n        name\n        shortName\n        teaser(input: { useFallback: $teaserFallback, maxLength: $teaserMaxLength })\n        published\n        publishedDate\n        labels\n        blueConic\n        blueConicClient\n        leaders\n        primaryImage {\n          name\n          src\n          credit\n          alt\n          isLogo\n          displayName\n        }\n        primarySection {\n          alias\n          name\n          id\n        }\n        siteContext {\n          path\n        }\n        company {\n          id\n          name\n          fullName\n          alias\n        }\n        gating {\n          surveyType\n          surveyId\n        }\n        membership {\n          id\n        }\n        userRegistration {\n          isRequired\n          accessLevels\n        }\n        layoutOverride {\n          hideHeader\n          hideFooter\n        }\n        ... on Authorable {\n          authors {\n            edges {\n              node {\n                name\n                path\n                id\n              }\n            }\n          }\n        }\n        ... on ContentEvent {\n          startDate\n          endDate\n        }\n        ... on ContentWebinar {\n          startDate\n        }\n      }\n    }\n  }\n}",
        "variables": {
            "includeContentIds": ids,
            "limit": 10000
        }
    }

    response = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS)
    response.raise_for_status()
    data = response.json()

    edges = data.get("data", {}).get("getContentStream", {}).get("edges", [])
    full_urls = [
        BASE_URL + edge["node"]["siteContext"]["path"]
        for edge in edges
        if edge.get("node") and edge["node"].get("siteContext") and "path" in edge["node"]["siteContext"]
    ]

    return full_urls


# === Step 3: Store New URLs in Mongo ===
def store_urls_to_mongo(urls, category="energytech"):
    collection = get_mongo_collection()

    # Check for duplicates
    existing_urls = set(
        doc['url'] for doc in collection.find({"category": category}, {"url": 1})
    )
    new_urls = [url for url in urls if url not in existing_urls]

    documents = [{"url": url, "category": category, "status": "new"} for url in new_urls]

    if documents:
        collection.insert_many(documents, ordered=False)
        print(f"Inserted {len(documents)} new URLs.")
    else:
        print("No new URLs to insert.")


def aspire_energytech_crawler(skip=0, limit=10, category="energytech"):
    try:
        print(f"\nCrawling Aspire (EnergyTech) for category: {category} [skip={skip}, limit={limit}]")
        article_ids = fetch_article_ids(skip=skip, limit=limit)
        print(f"Fetched {len(article_ids)} articles.")
        if not article_ids:
            print("No article IDs returned.")
            return

        article_urls = fetch_urls_from_ids(article_ids)
        print(f"Fetched {len(article_urls)} articles.")
        if not article_urls:
            print("No article URLs extracted.")
            return

        store_urls_to_mongo(article_urls, category=category)

    except Exception as e:
        print("Aspire EnergyTech crawler error:", str(e))
