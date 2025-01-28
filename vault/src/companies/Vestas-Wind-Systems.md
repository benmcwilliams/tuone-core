```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Vestas-Wind-Systems" or company = "Vestas Wind Systems")
sort location, dt_announce desc
```
