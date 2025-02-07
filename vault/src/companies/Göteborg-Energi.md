```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Göteborg-Energi" or company = "Göteborg Energi")
sort location, dt_announce desc
```
