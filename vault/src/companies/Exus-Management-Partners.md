```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Exus-Management-Partners" or company = "Exus Management Partners")
sort location, dt_announce desc
```
