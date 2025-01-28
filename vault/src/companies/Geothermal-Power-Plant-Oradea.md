```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Geothermal-Power-Plant-Oradea" or company = "Geothermal Power Plant Oradea")
sort location, dt_announce desc
```
