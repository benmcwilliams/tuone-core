```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Laurentis-Energy-Partners" or company = "Laurentis Energy Partners")
sort location, dt_announce desc
```
