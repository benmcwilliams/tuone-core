# date_selectors.py

DATE_SELECTORS = {
    'electrive_battery': ('class', '.date'),
    'electrive_automobile': ('class', '.date'),
    'energy_voice_hydrogen': ('class', '.post-timestamp__published'),
    'offshoreWindBiz': ('class', '.article-meta__info'),
    'power_technology': ('class', '.article-meta .date-published'),
    'pv_magazine_hydrogen': ('class', '.entry-published.updated'),
    'pv_magazine_manufacturing': ('class', '.entry-published.updated'),
    'pv_magazine_utility': ('class', '.entry-published.updated'),
    'pv_magazine_energy-storage': ('class', '.entry-published.updated'),
    'pv_magazine_balance-of-system': ('class', '.entry-published.updated'),
    'pv_tech': ('tag', 'time'),
    'renewsBiz_offshore_wind': ('class', '.first-upper[itemprop="dateCreated"]'),
    'renewsBiz_onshore_wind': ('class', '.first-upper[itemprop="dateCreated"]'),
    'renewsBiz_solar': ('class', '.first-upper[itemprop="dateCreated"]'),
    'world_energy_battery': ('class', '.color-front.fwb'),
    'world_energy_hydrogen': ('class', '.color-front.fwb'),
    'world_energy_solar': ('class', '.color-front.fwb'),
    'world_energy_wind': ('class', '.color-front.fwb'),
    'world_energy_geothermal': ('class', '.color-front.fwb'),
    'world_energy_hydropower': ('class', '.color-front.fwb'),
    'world_energy_nuclear': ('class', '.color-front.fwb'),
    'world_energy_vehicles': ('class', '.color-front.fwb')
}