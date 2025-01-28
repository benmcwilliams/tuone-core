```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Neart-na-Gaoithe-Offshore-Wind-Limited" or company = "Neart na Gaoithe Offshore Wind Limited")
sort location, dt_announce desc
```
