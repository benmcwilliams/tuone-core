```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Adris-Grupa" or company = "Adris Grupa")
sort location, dt_announce desc
```
