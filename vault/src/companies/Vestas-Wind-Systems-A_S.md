```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Vestas-Wind-Systems-A_S" or company = "Vestas Wind Systems A_S")
sort location, dt_announce desc
```
