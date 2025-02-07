```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Universal-Coatings-&-Services" or company = "Universal Coatings & Services")
sort location, dt_announce desc
```
