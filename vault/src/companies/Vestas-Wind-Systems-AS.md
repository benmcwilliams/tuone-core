```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Vestas-Wind-Systems-AS" or company = "Vestas Wind Systems AS")
sort location, dt_announce desc
```
