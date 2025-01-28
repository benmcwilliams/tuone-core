```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Eolia-Renovables-SA" or company = "Eolia Renovables SA")
sort location, dt_announce desc
```
