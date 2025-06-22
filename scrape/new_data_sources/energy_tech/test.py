import requests

url = "https://gemenon.graphql.aspire-ebm.com/"

payload = {
    "query": "query getContentStream(\n  $authorId: Int\n  $excludeContentIds: [Int!]\n  $includeContentIds: [Int!]\n  $includeContentTypes: [ContentType!]\n  $issueId: Int\n  $limit: Int\n  $publishedAfter: Date\n  $publishedBefore: Date\n  $randomizeResults: Boolean\n  $relatedToId: Int\n  $requireMemberships: [ObjectID]\n  $requirePrimaryImage: Boolean\n  $scheduleOption: WebsiteScheduleOption\n  $sectionBubbling: Boolean\n  $sectionId: Int\n  $skip: Int\n  $sortField: ContentSortField\n  $sortOrder: SortOrder\n  $startDateAfter: Date\n  $startDateBefore: Date\n  $teaserFallback: Boolean\n  $teaserMaxLength: Int\n) {\n  getContentStream(\n    input: {\n      authorId: $authorId\n      excludeContentIds: $excludeContentIds\n      includeContentIds: $includeContentIds\n      includeContentTypes: $includeContentTypes\n      issueId: $issueId\n      pagination: { limit: $limit, skip: $skip }\n      publishedAfter: $publishedAfter\n      publishedBefore: $publishedBefore\n      randomizeResults: $randomizeResults\n      relatedTo: { id: $relatedToId }\n      requireMemberships: $requireMemberships\n      requirePrimaryImage: $requirePrimaryImage\n      scheduleOption: $scheduleOption\n      sectionBubbling: $sectionBubbling\n      sectionId: $sectionId\n      sort: { field: $sortField, order: $sortOrder }\n      startDateAfter: $startDateAfter\n      startDateBefore: $startDateBefore\n    }\n  ) {\n    edges {\n      node {\n        id\n        type\n        name\n        shortName\n        teaser(input: { useFallback: $teaserFallback, maxLength: $teaserMaxLength })\n        published\n        publishedDate\n        labels\n        blueConic\n        blueConicClient\n        leaders\n        primaryImage {\n          name\n          src\n          credit\n          alt\n          isLogo\n          displayName\n        }\n        primarySection {\n          alias\n          name\n          id\n        }\n        siteContext {\n          path\n        }\n        company {\n          id\n          name\n          fullName\n          alias\n        }\n        gating {\n          surveyType\n          surveyId\n        }\n        membership {\n          id\n        }\n        userRegistration {\n          isRequired\n          accessLevels\n        }\n        layoutOverride {\n          hideHeader\n          hideFooter\n        }\n        ... on Authorable {\n          authors {\n            edges {\n              node {\n                name\n                path\n                id\n              }\n            }\n          }\n        }\n        ... on ContentEvent {\n          startDate\n          endDate\n        }\n        ... on ContentWebinar {\n          startDate\n        }\n      }\n    }\n  }\n}",
    "variables": {
        "includeContentIds": [55298273, 55298215, 55298158, 55298094, 55297949, 55297828, 55297746, 55297620, 55297415, 55297237, 55297113, 55297077, 55290758, 55296209, 55296662, 55296505, 55296355, 55296363, 55294292, 55296243],
        "limit": 1000
    }
}
headers = {
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

response = requests.post(url, json=payload, headers=headers)

print(response.text)