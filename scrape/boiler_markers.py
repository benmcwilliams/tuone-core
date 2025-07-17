import re

BOILER_STRINGS = {
    "Your email address will not be published.Required fields are marked*",
    "Name *",
    "E-Mail *",
    "I agree with thePrivacy policy",
    "© 2025 electrive.com",
    "electrive has been following the development of electric mobility with journalistic passion and expertise since 2013. As the industry's leading trade media, we offer comprehensive coverage of the highest quality — as a central platform for the rapid development of this technology. With news, background information, driving reports, interviews, videos and advertising messages.",
    "The gold standard of business intelligence.",
    "Find out more",
    "Give your business an edge with our leading industry insights.",
    "Future Power Technology : Power Technology Focus (monthly)",
    "Thematic Take (monthly)",
    "Visit ourPrivacy Policyfor more information about our services, how we may use, process and share your personal data, including information on your rights in respect of your personal data and how you can unsubscribe from future marketing communications. Our services are intended for corporate subscribers and you warrant that the email address submitted is your corporate email address.",
    "View all newslettersfrom across the GlobalData Media network.",
    "Power industry news, data and in-depth articles on the global trends driving power generation, renewables and innovation",
    "Powered by",
    "© Verdict Media Limited 2025",
    "This article is reproduced at argusmedia.com",
    "As our energy demands grow greater, renewable energy is key to the future of our planet. Harnessing the power of wind is essential. At Aggreko, we have over 60 years’ experience and an in-depth understanding of the power and temperature control needs of wind farms. We have a dedicated Wind Energy Team whose innovative strategies […]",
    "Daily news and in-depth stories in your inbox",
    "Share this article",
    "Follow us"
    # …add any other exact lines you see
}