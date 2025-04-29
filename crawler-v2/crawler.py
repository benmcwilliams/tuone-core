from crawlers.crawley_world_energy import world_energy_crawler
from crawlers.crawley_pv_magazine import pv_magazine_crawler
from crawlers.crawley_pv_tech import pv_tech_crawler
from crawlers.crawley_renewsBiz import renews_biz_crawler
from crawlers.crawley_offshorewindbiz import offshorewindBiz_crawler
from crawlers.crawley_electrive import electrive_crawler
from crawlers.crawley_power_technology import power_technology_crawler
from config.config_crawl import WORLD_ENERGY_CHANNELS, PV_MAGAZINE_EXTENSIONS, RENEWS_BIZ_TECH_DICT, ELECTRIVE_PAGE_TYPES

# set max pages to crawl for each source
world_energy_max_pages = 5
pv_magazine_max_pages = 5
pv_tech_max_pages = 5
renews_biz_max_pages = 5
offshore_wind_max_pages = 5
electrive_max_pages = 2
power_technology_max_pages = 5

if __name__ == "__main__":

    # # crawl world energy
    # for tech in WORLD_ENERGY_CHANNELS.keys():
    #     world_energy_crawler(tech, max_pages=world_energy_max_pages)
    #
    # # crawl PV Magazine
    # for tech in PV_MAGAZINE_EXTENSIONS.keys():
    #     pv_magazine_crawler(PV_MAGAZINE_EXTENSIONS, tech=tech, max_pages=pv_magazine_max_pages)
    #
    # # crawl PV Tech
    # pv_tech_crawler(max_pages=pv_tech_max_pages)
    #
    # # crawl renewsBiz
    # for tech in RENEWS_BIZ_TECH_DICT.keys():
    #     renews_biz_crawler(tech, max_pages=renews_biz_max_pages)
    #
    # # crawl offshoreWindBiz
    # offshorewindBiz_crawler(max_pages=offshore_wind_max_pages)

    # crawl electrive
    for page_type in ELECTRIVE_PAGE_TYPES:
        electrive_crawler(page_type=page_type, max_pages=electrive_max_pages)

    # # crawl Power Technology
    # power_technology_crawler(max_pages=power_technology_max_pages)